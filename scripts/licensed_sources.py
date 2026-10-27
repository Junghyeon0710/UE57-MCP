"""인증된 공식 저장소에서 조립에 필요한 원본과 의존 파일만 가져온다."""
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
from pathlib import Path
import subprocess
import urllib.request
import xml.etree.ElementTree as ET


def git(root, *args, **kwargs):
    return subprocess.check_output(["git", "-C", str(root), *args], **kwargs)


def fetch(recipe, assets, work):
    """공식 접근 권한을 확인하고 고정 리비전 및 파일 해시를 검증한다."""
    source = recipe["official_source"]
    root = Path(work).resolve() / "dependencies/epic58"
    root.parent.mkdir(parents=True, exist_ok=True)
    if not root.exists():
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none",
                        "--no-checkout", "--branch", source["tag"], source["url"], str(root)], check=True)
    if git(root, "remote", "get-url", "origin", text=True).strip() != source["url"]:
        raise ValueError("Source cache is not the official Epic repository")
    if git(root, "rev-parse", "HEAD", text=True).strip() != source["revision"]:
        raise ValueError("Source revision differs from the verified UE 5.8.4 baseline")
    names = set(git(root, "ls-tree", "-r", "--name-only", "HEAD", text=True).splitlines())
    wanted = {s["path"] for s in recipe["sources"].values() if s["root"] == "ue58"}
    wanted.update(s["source"] for s in assets["files"])
    wanted.update({"Engine/Build/Build.version", "Engine/Build/Commit.gitdeps.xml"})
    patterns = "\n".join("/" + n for n in sorted(wanted & names))
    git(root, "sparse-checkout", "set", "--no-cone", "--stdin", input=patterns, text=True)
    git(root, "checkout", "--detach", source["revision"])
    manifest = (root / "Engine/Build/Commit.gitdeps.xml").read_bytes()
    if hashlib.sha256(manifest.replace(b"\r\n", b"\n")).hexdigest() != source["manifest_sha256"]:
        raise ValueError("Official dependency manifest hash mismatch")
    download_dependencies(root, manifest, wanted - names)
    return root


def download_dependencies(root, manifest, wanted):
    """공식 매니페스트가 지정한 압축 팩에서 필요한 파일만 추출한다."""
    tree = ET.fromstring(manifest)
    base = tree.attrib["BaseUrl"]
    if base != "https://cdn.unrealengine.com/dependencies":
        raise ValueError("Unexpected dependency download host")
    files = {e.attrib["Name"]: e.attrib for e in tree.find("Files")}
    blobs = {e.attrib["Hash"]: e.attrib for e in tree.find("Blobs")}
    packs = {e.attrib["Hash"]: e.attrib for e in tree.find("Packs")}
    groups = {}
    for name in sorted(wanted):
        if name not in files:
            raise ValueError(f"Official source is missing: {name}")
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError("Dependency path escapes cache")
        expected = files[name]["Hash"]
        if path.is_file() and hashlib.sha1(path.read_bytes()).hexdigest() == expected:
            continue
        blob = blobs[expected]
        groups.setdefault(blob["PackHash"], []).append((path, blob))

    def download(pair):
        key, entries = pair
        pack = packs[key]
        remote = pack["RemotePath"]
        if "/" in remote or ".." in remote:
            raise ValueError("Unexpected dependency pack path")
        request = urllib.request.Request(f"{base}/{remote}/{key}")
        with urllib.request.urlopen(request, timeout=120) as response:
            compressed = response.read(int(pack["CompressedSize"]) + 1)
        if len(compressed) != int(pack["CompressedSize"]):
            raise ValueError("Dependency download size mismatch")
        data = gzip.decompress(compressed)
        if len(data) != int(pack["Size"]) or hashlib.sha1(data).hexdigest() != key:
            raise ValueError("Dependency pack integrity check failed")
        for path, blob in entries:
            start, size = int(blob["PackOffset"]), int(blob["Size"])
            value = data[start:start + size]
            if len(value) != size or hashlib.sha1(value).hexdigest() != blob["Hash"]:
                raise ValueError(f"Dependency file integrity check failed: {path.name}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
        return len(entries)

    with ThreadPoolExecutor(max_workers=6) as executor:
        count = sum(executor.map(download, groups.items()))
    print(f"Official dependencies verified; downloaded {count} files", flush=True)
