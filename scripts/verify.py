"""실행 중인 에디터에서 전체 이식본의 실제 도구 등록을 검사한다."""
import argparse
import json
import re
from pathlib import Path
from ue57_mcp import MCPClient


def content(result):
    if result.get("isError"):
        raise RuntimeError(str(result))
    if "structuredContent" in result:
        return result["structuredContent"]
    text = "\n".join(x.get("text", "") for x in result.get("content", []) if x.get("type") == "text")
    try:
        return json.loads(text)
    except ValueError:
        return text


def verify(url):
    client = MCPClient(url)
    tools = client.request("tools/list")["tools"]
    if not {"list_toolsets", "describe_toolset", "call_tool"} <= {x["name"] for x in tools}:
        raise ValueError("Official MCP discovery tools are missing")
    listing = content(client.request("tools/call", {"name": "list_toolsets", "arguments": {}}))
    if not isinstance(listing, str):
        raise ValueError("Unexpected toolset list; is the old reduced server still running?")
    names = re.findall(r"^- ([\w]+\.[\w.]+):", listing, re.M)
    catalog = []
    for name in names:
        schema = content(client.request("tools/call", {"name": "describe_toolset", "arguments": {"toolset_name": name}}))
        if schema["name"] != name:
            raise ValueError("Toolset schema name mismatch")
        catalog.append({"name": name, "tools": [x["name"] for x in schema["tools"]]})
    expected = json.loads((Path(__file__).resolve().parents[1] / "docs/tool-catalog.json").read_text(encoding="utf-8"))
    actual_set = {(s["name"], t) for s in catalog for t in s["tools"]}
    expected_set = {(s["name"], t) for s in expected["toolsets"] for t in s["tools"]}
    if actual_set != expected_set:
        raise ValueError(f"Tool catalog mismatch: {len(expected_set - actual_set)} missing, {len(actual_set - expected_set)} unexpected")
    return {"status": "verified", "toolset_count": len(catalog), "tool_count": len(actual_set), "toolsets": catalog}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = verify(args.url)
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "toolsets"}, indent=2))
