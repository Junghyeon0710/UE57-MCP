#!/usr/bin/env python3
"""라이선스 보유자의 로컬 엔진에서 UE 5.7 MCP를 조립하고 설치한다."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECIPE = ROOT / "recipes/ue5.7.4-from-5.8.4.json"
MARKER = ".ue57-mcp-bundle.json"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")

def inside(root, relative):
    """상대 경로가 지정한 디렉터리를 벗어나거나 링크로 우회하지 않는지 검사한다."""
    root = Path(root).resolve()
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts or ":" in str(relative) or "\\" in str(relative):
        raise ValueError(f"Unsafe relative path: {relative}")
    path = (root / rel).resolve()
    if path == root or not path.is_relative_to(root):
        raise ValueError(f"Path escapes root: {relative}")
    return path

def run(args, **kwargs):
    subprocess.run([str(a) for a in args], check=True, **kwargs)

def engine_version(root):
    v = read_json(Path(root)/"Engine/Build/Build.version")
    return ".".join(str(v[x]) for x in ["MajorVersion", "MinorVersion", "PatchVersion"])

def load_sources(recipe, roots):
    """출력 전에 모든 로컬 원본의 SHA256을 검증한다."""
    result = {}
    for key, spec in recipe["sources"].items():
        if spec["root"] not in roots:
            raise ValueError(f"Missing source root: {spec['root']}")
        path = inside(roots[spec["root"]], spec["path"])
        raw = path.read_bytes()
        if digest(raw) != spec["sha256"]:
            raise ValueError(f"Source differs from verified version: {spec['root']}:{spec['path']}")
        try:
            lines = raw.decode("utf-8-sig").replace("\r\n", "\n").splitlines(keepends=True)
            if spec.get("view") == "patch-additions":
                lines = [x[1:] for x in lines if x.startswith("+") and not x.startswith("+++")]
            elif spec.get("view"):
                raise ValueError(f"Unknown source view: {spec['view']}")
        except UnicodeError:
            lines = None
        result[key] = (raw, lines)
    return result

def assemble(recipe, roots, output, check_versions=True):
    """검증한 소스 조각과 독자 호환 변경을 임시 폴더에서 조립한 뒤 이동한다."""
    if recipe.get("format") != 1:
        raise ValueError("Unsupported recipe format")
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {output}")
    if os.name=="nt" and max((len(str(output/spec["path"])) for spec in recipe["files"]), default=0)>240:
        raise ValueError("Windows source path is too long. Use a short --work-dir, for example C:/UE57MCPBuild")
    if check_versions:
        for key, expected in recipe["source_versions"].items():
            if engine_version(roots[key]) != expected:
                raise ValueError(f"{key} must be {expected}")
    sources = load_sources(recipe, roots)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="ue57-mcp-", dir=output.parent) as tmp:
        stage = Path(tmp)/"bundle"
        stage.mkdir()
        manifest = {}
        for spec in recipe["files"]:
            path = inside(stage, spec["path"])
            if spec["path"] in manifest:
                raise ValueError(f"Duplicate output path: {spec['path']}")
            if "source" in spec:
                raw, lines = sources[spec["source"]]
                data = raw if spec["mode"] == "binary" else "".join(lines).encode("utf-8")
            else:
                pieces = []
                for piece in spec["pieces"]:
                    if piece[0] == "text":
                        pieces.append(piece[1])
                    elif piece[0] == "copy":
                        lines = sources[piece[1]][1]
                        if lines is None or not (0 <= piece[2] <= piece[3] <= len(lines)):
                            raise ValueError(f"Invalid source range: {spec['path']}")
                        pieces.append("".join(lines[piece[2]:piece[3]]))
                    else:
                        raise ValueError(f"Unknown recipe operation: {piece[0]}")
                data = "".join(pieces).encode("utf-8")
            if digest(data) != spec["sha256"]:
                raise ValueError(f"Assembly hash mismatch: {spec['path']}")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            manifest[spec["path"]] = digest(data)
        write_json(stage/MARKER, {"format":1, "assets_ready":False, "files":manifest,
                   "source_versions":recipe.get("source_versions", {}), "recipe_sha256":digest(json.dumps(recipe, sort_keys=True).encode())})
        if not stage.resolve().is_relative_to(output.parent):
            raise ValueError("Temporary output escaped destination")
        os.replace(stage, output)
    return len(manifest)

def fetch_portkit(work, recipe):
    path = Path(work).resolve()/"dependencies/portkit"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        run(["git", "clone", "--no-checkout", recipe["portkit"]["url"], path])
        run(["git", "-C", path, "checkout", "--detach", recipe["portkit"]["revision"]])
    revision = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    if revision != recipe["portkit"]["revision"]:
        raise ValueError("PortKit checkout differs from pinned revision")
    return path

def create_host(work):
    """검증 전용 C++ 프로젝트를 만들며 기존 파일은 같은 내용일 때만 재사용한다."""
    host = Path(work).resolve()/"host57"
    files = {
        "UE57MCPHost.uproject":json.dumps({"FileVersion":3,"EngineAssociation":"5.7","Modules":[{"Name":"UE57MCPHost","Type":"Runtime","LoadingPhase":"Default"}]},indent=2)+"\n",
        "Source/UE57MCPHost/UE57MCPHost.Build.cs":'using UnrealBuildTool;\npublic class UE57MCPHost : ModuleRules { public UE57MCPHost(ReadOnlyTargetRules Target) : base(Target) { PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs; PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" }); } }\n',
        "Source/UE57MCPHost/UE57MCPHost.cpp":'#include "Modules/ModuleManager.h"\nIMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, UE57MCPHost, "UE57MCPHost");\n',
        "Source/UE57MCPHostEditor.Target.cs":'using UnrealBuildTool;\npublic class UE57MCPHostEditorTarget : TargetRules { public UE57MCPHostEditorTarget(TargetInfo Target) : base(Target) { Type = TargetType.Editor; bUseAdaptiveUnityBuild = false; DefaultBuildSettings = BuildSettingsVersion.V6; IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_7; ExtraModuleNames.Add("UE57MCPHost"); } }\n',
        "Config/DefaultEditorPerProjectUserSettings.ini":"[/Script/ModelContextProtocolEngine.ModelContextProtocolSettings]\nbAutoStartServer=False\nbEnableToolSearch=True\n",
        "Config/DefaultGame.ini":'[/Script/Engine.AssetManagerSettings]\n+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",AssetBaseClass="/Script/GameFeatures.GameFeatureData",bHasBlueprintClasses=False,bIsEditorOnly=True,Directories=(),SpecificAssets=(),Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=True,CookRule=NeverCook))\n'
    }
    for rel, text in files.items():
        p = inside(host, rel)
        if p.exists() and p.read_text(encoding="utf-8") != text:
            raise FileExistsError(f"Existing host file differs: {p}")
        if p.exists():continue
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return host/"UE57MCPHost.uproject"

def build(engine, project, target=None):
    root = Path(engine).resolve()
    project = Path(project).resolve()
    if engine_version(root)!="5.7.4":
        raise ValueError("Build engine must be the verified UE 5.7.4 version")
    if not read_json(project).get("Modules") and target is None:
        bundle=project.parent/"Plugins/UE57MCP"
        validate_bundle(bundle)
        if not (bundle/"ModelContextProtocol/Binaries/Win64/UnrealEditor-ModelContextProtocol.dll").exists():
            raise ValueError("Blueprint-only project requires the host-built plugin binaries")
        print("Blueprint-only project: using host-built plugins; open the editor and run verify.")
        return
    ubt = root/"Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe"
    run([ubt, target or project.stem+"Editor", "Win64", "Development", f"-Project={project}", "-NoHotReloadFromIDE"])

def generate_assets(engine57, engine58, work):
    """소유한 엔진에서 에셋 데이터를 추출하고 5.7에서 새 에셋으로 저장한다."""
    work = Path(work).resolve()
    host = work/"host57/UE57MCPHost.uproject"
    source = work/"source58/Source58.uproject"
    if not source.exists():
        write_json(source,{"FileVersion":3,"EngineAssociation":"5.8","Plugins":[{"Name":n,"Enabled":True} for n in ["PythonScriptPlugin","EditorScriptingUtilities","PCGToolset","DataflowAgent","ChaosClothAsset","ChaosClothAssetEditorCore"]]})
    env = dict(os.environ, UE57_MCP_ASSET_WORK=str(work))
    for engine, project, script, report in [
        (engine58,source,"export58.py","source58-export.json"),
        (engine57,host,"create57.py","assets57-report.json")]:
        editor = Path(engine)/"Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
        report_path = work/report
        # 유효한 5.8 추출물은 재사용하고, 5.7 결과는 매번 에디터에서 재검증한다.
        if report_path.exists() and script=="export58.py":
            existing=read_json(report_path)
            if existing.get("error") or len(existing.get("skills",[]))!=8 or len(existing.get("cloth_graph",{}).get("nodes",[]))!=32:
                raise ValueError("Existing source export is incomplete; use a new work directory")
            continue
        if report_path.exists():
            index=1
            while report_path.with_name(report_path.name+f".previous-{index}").exists():index+=1
            report_path.rename(report_path.with_name(report_path.name+f".previous-{index}"))
        run([editor, project, "-Unattended", "-NoSplash", "-NoSound", "-NoLiveCoding", "-RenderOffscreen", "-culture=en",
             "-run=pythonscript", f"-script={ROOT/'scripts/ue_assets'/script}",f"-abslog={work/(script+'.log')}"], env=env)
        report_data = read_json(report_path)
        if report_data.get("error"):
            raise RuntimeError(f"Asset generation failed: {report_data['error']}")
    report = read_json(work/"assets57-report.json")
    if report["skill_count"] != 8 or report["cloth_node_count"] != 31 or report["cloth_connections"] != 36:
        raise ValueError("Generated asset counts differ from verified baseline")
    bundle = work/"host57/Plugins/UE57MCP"
    marker = read_json(bundle/MARKER)
    for p in bundle.rglob("*.uasset"):
        if {"Intermediate","Saved"}.intersection(p.relative_to(bundle).parts):continue
        marker["files"][p.relative_to(bundle).as_posix()] = digest(p.read_bytes())
    marker["assets_ready"] = True
    write_json(bundle/MARKER, marker)

def ini_section(text, section, values):
    """다른 설정과 Unreal 배열 항목을 보존하며 필요한 키만 갱신한다."""
    text = text.replace("\r\n", "\n")
    header = f"[{section}]"
    lines = text.splitlines()
    starts = [i for i,line in enumerate(lines) if line.strip()==header]
    if len(starts)>1:raise ValueError(f"Duplicate INI section: {section}")
    if starts:
        start=starts[0]
        end=next((i for i in range(start+1,len(lines)) if lines[i].lstrip().startswith("[")),len(lines))
        replace_keys={k.lower() for k in values if not k.startswith("+")}
        keep=[x for x in lines[start+1:end] if x.split("=",1)[0].strip().lower() not in replace_keys]
        lines[start+1:end]=[f"{k}={v}" for k,v in values.items()]+keep
    else:
        lines += ["",header]+[f"{k}={v}" for k,v in values.items()]
    return "\n".join(lines)+"\n"

def validate_bundle(bundle, require_assets=True):
    marker = read_json(bundle/MARKER)
    if require_assets and not marker.get("assets_ready"):
        raise ValueError("Bundle is source-only; run bootstrap including asset generation first")
    for rel, expected in marker["files"].items():
        if digest(inside(bundle,rel).read_bytes()) != expected:
            raise ValueError(f"Bundle was modified: {rel}")
    return marker

def install(bundle, project, port=8000):
    """프로젝트 추적 파일을 바꾸지 않고 새 로컬 플러그인과 설정을 설치한다."""
    if not 1 <= port <= 65535:raise ValueError("Port must be 1..65535")
    bundle=Path(bundle).resolve();project=Path(project).resolve()
    marker=validate_bundle(bundle)
    if not project.is_file() or project.suffix!=".uproject":raise ValueError("Expected a .uproject file")
    config=read_json(project)
    association=str(config.get("EngineAssociation",""))
    if re.fullmatch(r"\d+\.\d+(?:\.\d+)?",association) and not association.startswith("5.7"):
        raise ValueError("Project EngineAssociation is not 5.7")
    target=inside(project.parent,"Plugins/UE57MCP")
    if target.exists() or list((project.parent/"Plugins").rglob("ModelContextProtocol.uplugin")):
        raise FileExistsError("An MCP plugin installation already exists; back it up and remove it before installing")
    before=digest(project.read_bytes())
    settings=inside(project.parent,"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini")
    game=inside(target,"AllToolsets/Config/Game.ini")
    changes={}
    old=settings.read_text(encoding="utf-8-sig") if settings.exists() else ""
    changes[settings]=ini_section(old,"/Script/ModelContextProtocolEngine.ModelContextProtocolSettings",{
        "bAutoStartServer":"True","ServerPortNumber":str(port),"ServerUrlPath":"/mcp","bEnableToolSearch":"True"}).encode()
    default_game=project.parent/"Config/DefaultGame.ini"
    configured=default_game.read_text(encoding="utf-8-sig") if default_game.exists() else ""
    if 'PrimaryAssetType="GameFeatureData"' not in configured:
        changes[game]=ini_section("","/Script/Engine.AssetManagerSettings",{
            "+PrimaryAssetTypesToScan":'(PrimaryAssetType="GameFeatureData",AssetBaseClass="/Script/GameFeatures.GameFeatureData",bHasBlueprintClasses=False,bIsEditorOnly=True,Directories=(),SpecificAssets=(),Rules=(Priority=-1,ChunkId=-1,bApplyRecursively=True,CookRule=NeverCook))'}).encode()
    gitroot=subprocess.run(["git","-C",str(project.parent),"rev-parse","--show-toplevel"],capture_output=True,text=True)
    if gitroot.returncode==0:
        repo=Path(gitroot.stdout.strip()).resolve()
        for p in changes:
            tracked=subprocess.run(["git","-C",str(repo),"ls-files","--error-unmatch",p.relative_to(repo).as_posix()],capture_output=True)
            if tracked.returncode==0:raise ValueError(f"Local configuration is Git-tracked; refusing to modify it: {p}")
        exclude_output=subprocess.check_output(["git","-C",str(repo),"rev-parse","--git-path","info/exclude"],text=True).strip()
        exclude=Path(exclude_output)
        if not exclude.is_absolute():exclude=repo/exclude
        exclude=exclude.resolve()
        old=exclude.read_text(encoding="utf-8-sig") if exclude.exists() else ""
        patterns=["/"+target.relative_to(repo).as_posix()+"/","/"+(project.parent/"Saved").relative_to(repo).as_posix()+"/"]
        missing=[p for p in patterns if p not in old.splitlines()]
        if missing:changes[exclude]=(old+"\n# Local UE57-MCP installation and generated editor state\n"+"\n".join(missing)+"\n").encode()
    backups={p:p.read_bytes() if p.exists() else None for p in changes}
    recovery=inside(project.parent,"Saved/UE57MCP/installation-backup.json")
    if recovery.exists():raise FileExistsError(f"Existing installation record: {recovery}")
    target.parent.mkdir(parents=True,exist_ok=True)
    def ignore_generated(directory,names):
        ignored=[]
        for name in names:
            relative=(Path(directory)/name).relative_to(bundle).as_posix()
            if name in {"Intermediate","Saved","__pycache__"}:
                ignored.append(name)
            elif Path(name).suffix in {".pdb",".lib",".exp"} and relative not in marker["files"]:
                ignored.append(name)
        return ignored
    try:
        shutil.copytree(bundle,target,ignore=ignore_generated)
        validate_bundle(target)
        for p,data in changes.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        if digest(project.read_bytes())!=before:raise RuntimeError("Project descriptor changed during installation")
        write_json(recovery,{"plugin_directory":str(target),"project_sha256":before,
            "previous_files":{str(p):data.decode("utf-8-sig") if data is not None else None for p,data in backups.items()},"port":port})
    except Exception:
        for p,data in backups.items():
            if data is None:p.unlink(missing_ok=True)
            else:p.write_bytes(data)
        if target.exists() and target.resolve()==inside(project.parent,"Plugins/UE57MCP"):
            shutil.rmtree(target)
        raise
    return target

class MCPClient:
    def __init__(self,url):
        self.url=url;self.session=None;self.sequence=0
        self.request("initialize",{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"ue57-mcp-verifier","version":"1.0.0"}})
        self.request("notifications/initialized",notification=True)
    def request(self,method,params=None,notification=False):
        self.sequence+=1
        payload={"jsonrpc":"2.0","method":method}
        if not notification:payload["id"]=self.sequence
        if params is not None:payload["params"]=params
        headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream","MCP-Protocol-Version":"2025-06-18"}
        if self.session:headers["Mcp-Session-Id"]=self.session
        req=urllib.request.Request(self.url,json.dumps(payload).encode(),headers)
        with urllib.request.urlopen(req,timeout=60) as response:
            self.session=response.headers.get("Mcp-Session-Id") or self.session
            data=response.read().decode()
        if not data.strip():return None
        result=json.loads(data)
        if "error" in result:raise RuntimeError(str(result["error"]))
        return result.get("result")

def verify(url):
    c=MCPClient(url);c.request("ping")
    tools=c.request("tools/list")["tools"]
    names={x["name"] for x in tools}
    if not {"list_toolsets","describe_toolset","call_tool"}<=names:raise ValueError("Tool-search meta-tools are missing")
    response=c.request("tools/call",{"name":"list_toolsets","arguments":{}})
    if response.get("isError"):raise RuntimeError(str(response))
    return {"status":"connected","meta_tools":sorted(names),"toolsets":response}

def main():
    parser=argparse.ArgumentParser(description="Install UE 5.7 MCP plugins or build them from licensed local engine sources.")
    sub=parser.add_subparsers(dest="command",required=True)
    boot=sub.add_parser("bootstrap")
    boot.add_argument("--engine57",type=Path,required=True);boot.add_argument("--engine58",type=Path,required=True)
    boot.add_argument("--work-dir",type=Path,default=ROOT/"_work");boot.add_argument("--portkit",type=Path)
    resume=sub.add_parser("resume")
    resume.add_argument("--engine57",type=Path,required=True);resume.add_argument("--engine58",type=Path,required=True)
    resume.add_argument("--work-dir",type=Path,required=True)
    ass=sub.add_parser("assemble")
    ass.add_argument("--engine57",type=Path,required=True);ass.add_argument("--engine58",type=Path,required=True)
    ass.add_argument("--portkit",type=Path,required=True);ass.add_argument("--output",type=Path,required=True)
    inst=sub.add_parser("install");inst.add_argument("--bundle",type=Path,required=True);inst.add_argument("--project",type=Path,required=True);inst.add_argument("--port",type=int,default=8000)
    pack=sub.add_parser("pack-prebuilt");pack.add_argument("--bundle",type=Path,required=True);pack.add_argument("--engine57",type=Path,required=True);pack.add_argument("--output",type=Path,required=True)
    prebuilt=sub.add_parser("install-prebuilt");prebuilt.add_argument("--archive",type=Path,required=True);prebuilt.add_argument("--engine57",type=Path,required=True);prebuilt.add_argument("--project",type=Path,required=True);prebuilt.add_argument("--port",type=int,default=8000)
    release=sub.add_parser("install-release",help="Download and install the pinned plugins from Epic's GitHub network")
    release.add_argument("--engine57",type=Path,required=True);release.add_argument("--project",type=Path,required=True);release.add_argument("--port",type=int,default=8000)
    release.add_argument("--cache-dir",type=Path,default=ROOT/"_work/downloads")
    b=sub.add_parser("build");b.add_argument("--engine57",type=Path,required=True);b.add_argument("--project",type=Path,required=True);b.add_argument("--target")
    v=sub.add_parser("verify");v.add_argument("--url",default="http://127.0.0.1:8000/mcp");v.add_argument("--output",type=Path)
    args=parser.parse_args();recipe=read_json(DEFAULT_RECIPE)
    if args.command in {"bootstrap","assemble"}:
        portkit=args.portkit or fetch_portkit(args.work_dir,recipe)
        output=args.output if args.command=="assemble" else args.work_dir.resolve()/"host57/Plugins/UE57MCP"
        count=assemble(recipe,{"ue57":args.engine57,"ue58":args.engine58,"portkit":portkit},output)
        print(f"Assembled {count} files: {output}",flush=True)
        if args.command=="bootstrap":
            project=create_host(args.work_dir);build(args.engine57,project);generate_assets(args.engine57,args.engine58,args.work_dir)
            print(f"Ready to install: {output}")
    elif args.command=="install":print(install(args.bundle,args.project,args.port))
    elif args.command in {"pack-prebuilt","install-prebuilt"}:
        import prebuilt_bundle
        api=sys.modules[__name__]
        if args.command=="pack-prebuilt":print(json.dumps(prebuilt_bundle.pack(args.bundle,args.engine57,args.output,api),indent=2))
        else:print(prebuilt_bundle.install_archive(args.archive,args.engine57,args.project,args.port,api))
    elif args.command=="install-release":
        import prebuilt_bundle
        import release_download
        descriptor=read_json(ROOT/"releases/ue5.7.4-win64.json")
        print(release_download.install(descriptor,args.engine57,args.project,args.port,args.cache_dir,sys.modules[__name__],prebuilt_bundle))
    elif args.command=="resume":
        for key,path in [("ue57",args.engine57),("ue58",args.engine58)]:
            if engine_version(path)!=recipe["source_versions"][key]:raise ValueError(f"Unexpected engine version: {key}")
        bundle=args.work_dir.resolve()/"host57/Plugins/UE57MCP"
        validate_bundle(bundle,require_assets=False)
        project=create_host(args.work_dir);build(args.engine57,project)
        if not read_json(bundle/MARKER).get("assets_ready"):generate_assets(args.engine57,args.engine58,args.work_dir)
        print(f"Ready to install: {bundle}")
    elif args.command=="build":build(args.engine57,args.project,args.target)
    elif args.command=="verify":
        result=verify(args.url)
        if args.output:write_json(args.output,result)
        print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=="__main__":
    try:main()
    except (ValueError,OSError,RuntimeError,subprocess.CalledProcessError) as e:
        print(f"UE57-MCP: {e}",file=sys.stderr);sys.exit(1)
