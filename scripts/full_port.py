"""5.8 엔진 설치 없이 기존 전체 이식본을 생성하고 5.7 프로젝트에 설치한다."""
import argparse
import base64
import json
from pathlib import Path
import sys

import licensed_sources
import ue57_mcp as api


def convert_assets(spec, source, bundle):
    """라이선스 원본에 5.7 직렬화 변경을 적용하고 검증된 결과만 저장한다."""
    prepared = {}
    for item in spec["files"]:
        raw = api.inside(source, item["source"]).read_bytes()
        if api.digest(raw) != item["source_sha256"]:
            raise ValueError(f"Asset source hash mismatch: {item['source']}")
        pieces = []
        for op in item["operations"]:
            if op[0] == "copy":
                start, size = op[1:]
                if start < 0 or size < 0 or start + size > len(raw):
                    raise ValueError("Asset source range is invalid")
                pieces.append(raw[start:start + size])
            elif op[0] == "data":
                pieces.append(base64.b64decode(op[1], validate=True))
            else:
                raise ValueError("Unknown asset compatibility operation")
        data = b"".join(pieces)
        if len(data) != item["size"] or api.digest(data) != item["sha256"]:
            raise ValueError(f"Converted asset hash mismatch: {item['path']}")
        prepared[item["path"]] = data
    marker = api.read_json(bundle / api.MARKER)
    for name, data in prepared.items():
        path = api.inside(bundle, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        marker["files"][name] = api.digest(data)
    marker["assets_ready"] = True
    api.write_json(bundle / api.MARKER, marker)


def main():
    parser = argparse.ArgumentParser(description="Install the full UE 5.8 MCP backport using only a UE 5.7.4 installation.")
    parser.add_argument("--engine57", type=Path, required=True)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prepare-only", action="store_true", help="Build a reusable bundle without installing into a project")
    args = parser.parse_args()
    if not args.prepare_only and not args.project:
        parser.error("Provide --project or --prepare-only")
    if api.engine_version(args.engine57) != "5.7.4":
        raise ValueError("This verified bundle requires UE 5.7.4")
    if not 1 <= args.port <= 65535:
        raise ValueError("Port must be 1..65535")
    if not args.prepare_only:
        project_path = args.project.resolve()
        if not project_path.is_file() or project_path.suffix != ".uproject":
            raise ValueError("Select an existing .uproject file")
        if (project_path.parent / "Plugins/UE57MCP").exists() or list((project_path.parent / "Plugins").rglob("ModelContextProtocol.uplugin")):
            raise FileExistsError("An MCP installation already exists; back it up outside Plugins before installing")
    work = args.work_dir.resolve()
    recipe = api.read_json(api.DEFAULT_RECIPE)
    assets = api.read_json(api.ROOT / "recipes/assets-5.7.4.json")
    source = licensed_sources.fetch(recipe, assets, work)
    portkit = api.fetch_portkit(work, recipe)
    bundle = work / "host57/Plugins/UE57MCP"
    if bundle.exists():
        marker = api.validate_bundle(bundle, require_assets=False)
        if marker.get("recipe_sha256") != api.digest(json.dumps(recipe, sort_keys=True).encode()):
            raise ValueError("Existing bundle belongs to another recipe; choose a new work directory")
    else:
        count = api.assemble(recipe, {"ue57": args.engine57, "ue58": source, "portkit": portkit}, bundle)
        print(f"Assembled {count} full-port source files", flush=True)
    convert_assets(assets, source, bundle)
    marker = api.read_json(bundle / api.MARKER)
    for path in (api.ROOT / "LICENSES").iterdir():
        if path.is_file():
            relative = "LICENSES/" + path.name
            destination = api.inside(bundle, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(path.read_bytes())
            marker["files"][relative] = api.digest(path.read_bytes())
    for name in ("LICENSE", "NOTICE"):
        path = api.ROOT / name
        destination = bundle / name
        destination.write_bytes(path.read_bytes())
        marker["files"][name] = api.digest(path.read_bytes())
    api.write_json(bundle / api.MARKER, marker)
    project = api.create_host(work)
    api.build(args.engine57, project)
    api.validate_bundle(bundle)
    if not args.prepare_only:
        print(f"Installed: {api.install(bundle, args.project, args.port)}", flush=True)
    else:
        print(f"Full backport ready: {bundle}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Full backport failed: {error}", file=sys.stderr)
        sys.exit(1)
