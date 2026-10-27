#!/usr/bin/env python3
"""로컬 에디터의 MCP 연결과 공개 도구 모음 스키마를 검사한다."""
import argparse
import json
from pathlib import Path
import re
import urllib.request

class Client:
    """HTTP 세션과 순차 JSON-RPC 식별자를 관리한다."""
    def __init__(self,url):
        self.url=url;self.session=None;self.sequence=0
        self.request("initialize",{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"ue57-mcp-verifier","version":"2.0.0"}})
        self.request("notifications/initialized",notification=True)
    def request(self,method,params=None,notification=False):
        self.sequence+=1;body={"jsonrpc":"2.0","method":method}
        if not notification:body["id"]=self.sequence
        if params is not None:body["params"]=params
        headers={"Content-Type":"application/json","Accept":"application/json, text/event-stream"}
        if self.session:headers["Mcp-Session-Id"]=self.session
        request=urllib.request.Request(self.url,json.dumps(body).encode(),headers)
        with urllib.request.urlopen(request,timeout=60) as response:
            self.session=response.headers.get("Mcp-Session-Id") or self.session
            data=response.read()
        if not data:return None
        message=json.loads(data)
        if "error" in message:raise RuntimeError(str(message["error"]))
        return message["result"]
    def call(self,name,arguments):
        result=self.request("tools/call",{"name":name,"arguments":arguments})
        if result.get("isError"):raise RuntimeError(str(result))
        if "structuredContent" in result:return result["structuredContent"]
        return "\n".join(block.get("text","") for block in result.get("content",[]) if block["type"]=="text")

def verify(url):
    client=Client(url);client.request("ping")
    names={tool["name"] for tool in client.request("tools/list")["tools"]}
    if not {"list_toolsets","describe_toolset","call_tool"}<=names:raise ValueError("MCP discovery tools are missing")
    listing=client.call("list_toolsets",{})
    groups=re.findall(r"^- ([\w.]+):",listing,re.M)
    schemas=[client.call("describe_toolset",{"toolset_name":group}) for group in groups]
    status=client.call("call_tool",{"toolset_name":"ue57.editor","tool_name":"status","arguments":{}})
    return {"status":"connected","toolsets":len(schemas),"tools":sum(len(schema["tools"]) for schema in schemas),"editor":status}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Verify UE57-MCP in the running editor")
    parser.add_argument("--url",default="http://127.0.0.1:8000/mcp")
    parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    result=verify(args.url)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2))
