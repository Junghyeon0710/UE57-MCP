"""UE 5.7 전용 로컬 빌드 패키지를 만들고 같은 엔진 빌드에 설치한다."""
from pathlib import Path
import hashlib
import json
import os
import platform
import tempfile
import zipfile

FORMAT = "ue57-mcp-prebuilt-v1"
MANIFEST = "prebuilt.json"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def safe_relative(path):
    """압축 파일의 절대 경로, 상위 경로, Windows 경로 우회를 거부한다."""
    rel=Path(path)
    if (not path or rel.is_absolute() or rel.as_posix()!=path
        or any(part in {".","..",""} or part.endswith(("."," ")) for part in path.split("/"))
        or any(c in path for c in '<>:"\\|?*') or any(ord(c)<32 for c in path)):
        raise ValueError(f"Unsafe archive path: {path}")
    return rel

def compatible_engine(engine, metadata):
    """5.8 경로를 읽지 않고 5.7 버전과 바이너리 BuildId를 검사한다."""
    engine=Path(engine)
    v=read_json(engine/"Engine/Build/Build.version")
    version=".".join(str(v[k]) for k in ["MajorVersion","MinorVersion","PatchVersion"])
    build_id=read_json(engine/"Engine/Binaries/Win64/UnrealEditor.modules")["BuildId"]
    if version!=metadata["engine_version"] or build_id!=metadata["engine_build_id"]:
        raise ValueError(f"Prebuilt package requires UE {metadata['engine_version']} BuildId {metadata['engine_build_id']}; installed {version} BuildId {build_id}")
    if metadata.get("platform")!="Win64" or platform.system()!="Windows":
        raise ValueError("This prebuilt package runs on Windows x64 only")

def validate_runtime(bundle, metadata, api):
    """모든 플러그인의 모듈 BuildId와 참조 DLL을 검사한다."""
    manifests=list(bundle.rglob("Binaries/Win64/UnrealEditor.modules"))
    if not manifests:raise ValueError("Compiled module manifests are missing")
    for path in manifests:
        modules=read_json(path)
        if modules["BuildId"]!=metadata["engine_build_id"]:
            raise ValueError(f"Module BuildId differs: {path.relative_to(bundle)}")
        for name in modules["Modules"].values():
            safe_relative(name)
            if not api.inside(path.parent,name).is_file():
                raise ValueError(f"Compiled module is missing: {name}")
    if not (bundle/"ModelContextProtocol/Binaries/Win64/UnrealEditor-ModelContextProtocol.dll").is_file():
        raise ValueError("Compiled MCP DLL is missing")

def pack(bundle, engine57, output, api):
    """검증된 소스·에셋과 실행에 필요한 DLL을 로컬 ZIP으로 묶는다."""
    bundle=Path(bundle).resolve();output=Path(output).resolve()
    if output.is_relative_to(bundle):raise ValueError("Archive output must be outside the bundle")
    marker=api.validate_bundle(bundle)
    if output.exists():raise FileExistsError(f"Archive already exists: {output}")
    module=read_json(bundle/"ModelContextProtocol/Binaries/Win64/UnrealEditor.modules")
    metadata={"format":FORMAT,"platform":"Win64","engine_version":"5.7.4",
              "engine_build_id":module["BuildId"],"toolset_count":55,"tool_count":858,
              "distribution":"Engine-derived tools: use an authorized Unreal Engine distribution channel.","files":{}}
    compatible_engine(engine57,metadata)
    validate_runtime(bundle,metadata,api)
    files=[]
    for path in sorted(bundle.rglob("*")):
        rel=path.relative_to(bundle)
        if not path.is_file() or {"Intermediate","Saved","__pycache__",".git"}.intersection(rel.parts):continue
        safe_relative(rel.as_posix())
        if path.is_symlink():raise ValueError(f"Bundle contains a symbolic link: {rel}")
        if path.suffix in {".pdb",".lib",".exp"} and rel.as_posix() not in marker["files"]:continue
        data=path.read_bytes()
        metadata["files"][rel.as_posix()]=digest(data)
        files.append((rel.as_posix(),data))
    if not any(name.endswith("UnrealEditor-ModelContextProtocol.dll") for name,_ in files):
        raise ValueError("Compiled MCP DLL is missing")
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.name+".partial")
    if temporary.exists():raise FileExistsError(f"Partial archive exists: {temporary}")
    try:
        with zipfile.ZipFile(temporary,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for name,data in files:archive.writestr("plugins/"+name,data)
            archive.writestr(MANIFEST,json.dumps(metadata,ensure_ascii=False,indent=2)+"\n")
        os.replace(temporary,output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {"path":str(output),"sha256":digest(output.read_bytes()),"bytes":output.stat().st_size,"files":len(files)}

def install_archive(archive_path, engine57, project, port, api):
    """패키지의 모든 해시를 검사한 뒤 기존 로컬 설치기로 설치한다."""
    project=Path(project).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        metadata=json.loads(archive.read(MANIFEST).decode("utf-8-sig"))
        if metadata.get("format")!=FORMAT:raise ValueError("Unknown prebuilt package format")
        compatible_engine(engine57,metadata)
        expected={"plugins/"+p for p in metadata["files"]}|{MANIFEST}
        names=archive.namelist()
        if len(names)!=len({p.casefold() for p in names}) or set(names)!=expected:
            raise ValueError("Archive contains duplicate, missing or unlisted files")
        for rel in metadata["files"]:
            safe_relative(rel)
            api.inside(project.parent,"Plugins/UE57MCP/"+rel)
        with tempfile.TemporaryDirectory(prefix="ue57-unpack-") as temporary:
            root=Path(temporary).resolve()
            for rel,expected_hash in metadata["files"].items():
                data=archive.read("plugins/"+rel)
                if digest(data)!=expected_hash:raise ValueError(f"Archive integrity failure: {rel}")
                target=api.inside(root,rel)
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
            validate_runtime(root,metadata,api)
            return api.install(root,project,port)
