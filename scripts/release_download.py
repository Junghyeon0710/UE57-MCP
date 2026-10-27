"""Epic GitHub 네트워크 접근 권한과 공개 해시를 검증하여 플러그인만 내려받는다."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
import zipfile

UPSTREAM="EpicGames/UnrealEngine"
API="https://api.github.com"

def github_token(repository):
    """환경 변수, GitHub CLI, Git 자격 증명 순서로 기존 인증을 메모리에만 읽는다."""
    for name in ("GH_TOKEN","GITHUB_TOKEN"):
        if os.environ.get(name):return os.environ[name]
    env=dict(os.environ,GIT_TERMINAL_PROMPT="0",GCM_INTERACTIVE="Never")
    if shutil.which("gh"):
        result=subprocess.run(["gh","auth","token","--hostname","github.com"],capture_output=True,text=True,env=env)
        if result.returncode==0 and result.stdout.strip():return result.stdout.strip()
    if shutil.which("git"):
        result=subprocess.run(["git","credential","fill"],input=f"protocol=https\nhost=github.com\npath={repository}.git\n\n",
                              capture_output=True,text=True,env=env)
        values=dict(line.split("=",1) for line in result.stdout.splitlines() if "=" in line)
        if result.returncode==0 and values.get("password"):return values["password"]
    raise ValueError("GitHub authentication is required. Link your Epic and GitHub accounts, then run 'gh auth login' or sign in using Git Credential Manager. Never paste tokens into chat.")

class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    """인증 헤더 없이 GitHub의 HTTPS 릴리스 파일 호스트로만 이동한다."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed=urllib.parse.urlsplit(newurl)
        if parsed.scheme!="https" or parsed.netloc not in {"api.github.com","release-assets.githubusercontent.com","objects.githubusercontent.com"}:
            raise ValueError("Unexpected GitHub download redirect")
        redirected=super().redirect_request(req,fp,code,msg,headers,newurl)
        if redirected:redirected.remove_header("Authorization")
        return redirected

class GitHub:
    """고정 GitHub API에만 인증을 보내며 오류에 인증 값이나 서명 URL을 노출하지 않는다."""
    def __init__(self,token):
        self.token=token
        self.opener=urllib.request.build_opener(GitHubRedirect())
    def open(self,path,binary=False):
        if not path.startswith("/repos/") or "?" in path or "#" in path:
            raise ValueError("Unexpected GitHub API path")
        headers={"Accept":"application/octet-stream" if binary else "application/vnd.github+json",
                 "User-Agent":"UE57-MCP-installer","X-GitHub-Api-Version":"2022-11-28"}
        req=urllib.request.Request(API+path,headers=headers)
        req.add_unredirected_header("Authorization","Bearer "+self.token)
        try:return self.opener.open(req,timeout=60)
        except urllib.error.HTTPError as error:
            if error.code in {401,403,404}:
                raise ValueError("GitHub access denied. Your account must have access to EpicGames/UnrealEngine and the distribution fork. See docs/prebuilt.md.") from None
            raise ValueError(f"GitHub request failed (HTTP {error.code})") from None
        except urllib.error.URLError:
            raise ValueError("GitHub connection failed. Check your network and retry.") from None
    def json(self,path):
        with self.open(path) as response:return json.load(response)

def validate_descriptor(data):
    """공개 메타데이터에서 임의 URL이나 잘못된 해시·파일 경로를 거부한다."""
    if data.get("format")!=1:raise ValueError("Unknown release descriptor format")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*",data.get("repository","")):
        raise ValueError("Invalid distribution repository")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*",data.get("tag","")):
        raise ValueError("Invalid release tag")
    if not re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*\.zip",data.get("asset","")):
        raise ValueError("Invalid release asset name")
    if not re.fullmatch(r"[0-9a-f]{64}",data.get("sha256","")):
        raise ValueError("Invalid release SHA256")
    if not isinstance(data.get("bytes"),int) or not 0<data["bytes"]<=1024**3:
        raise ValueError("Invalid release size")

def fetch(descriptor,cache,client=None):
    """Epic fork와 고정 릴리스의 접근 권한을 확인한 뒤 ZIP을 원자적으로 저장한다."""
    validate_descriptor(descriptor)
    if descriptor.get("status")!="published":
        raise ValueError("The plugin release is prepared but not published yet. See docs/prebuilt.md for publication status; no project files were changed.")
    repo=descriptor["repository"]
    client=client or GitHub(github_token(repo))
    details=client.json("/repos/"+repo)
    if not details.get("private") or not details.get("fork") or details.get("source",{}).get("full_name","").lower()!=UPSTREAM.lower():
        raise ValueError("Distribution repository is not a private fork in Epic's UnrealEngine network")
    release=client.json("/repos/"+repo+"/releases/tags/"+descriptor["tag"])
    if release.get("draft") or release.get("tag_name")!=descriptor["tag"]:
        raise ValueError("Unexpected distribution release")
    assets=[a for a in release.get("assets",[]) if a.get("name")==descriptor["asset"]]
    if len(assets)!=1 or assets[0].get("state")!="uploaded" or assets[0].get("size")!=descriptor["bytes"]:
        raise ValueError("Pinned plugin asset is missing or has a different size")
    asset=assets[0]
    if asset.get("digest") and asset["digest"]!="sha256:"+descriptor["sha256"]:
        raise ValueError("GitHub asset digest differs from the pinned SHA256")
    target=Path(cache).resolve()/descriptor["asset"]
    if target.exists():
        if target.stat().st_size!=descriptor["bytes"] or hashlib.sha256(target.read_bytes()).hexdigest()!=descriptor["sha256"]:
            raise ValueError("Cached archive differs from the release. Move it aside before retrying.")
        return target
    target.parent.mkdir(parents=True,exist_ok=True)
    temporary=target.with_name(target.name+".partial")
    written=0;hasher=hashlib.sha256()
    try:
        with temporary.open("xb") as output:
            with client.open("/repos/"+repo+"/releases/assets/"+str(int(asset["id"])),binary=True) as response:
                while chunk:=response.read(1024*1024):
                    written+=len(chunk)
                    if written>descriptor["bytes"]:raise ValueError("Download exceeds the pinned release size")
                    hasher.update(chunk);output.write(chunk)
        if written!=descriptor["bytes"] or hasher.hexdigest()!=descriptor["sha256"]:
            raise ValueError("Downloaded plugin ZIP failed its SHA256 or size check")
        os.replace(temporary,target)
    except FileExistsError:
        raise ValueError("A partial download already exists. Move it aside before retrying.") from None
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return target

def install(descriptor,engine57,project,port,cache,api,prebuilt):
    """5.7 엔진 호환성을 먼저 확인하고 검증한 다운로드를 기존 설치기로 전달한다."""
    validate_descriptor(descriptor)
    prebuilt.compatible_engine(engine57,descriptor)
    archive=fetch(descriptor,cache)
    with zipfile.ZipFile(archive) as package:
        metadata=json.loads(package.read(prebuilt.MANIFEST).decode("utf-8-sig"))
    for key in ("engine_version","engine_build_id","platform"):
        if metadata.get(key)!=descriptor[key]:raise ValueError("Package engine metadata differs from the release descriptor")
    return prebuilt.install_archive(archive,engine57,project,port,api)
