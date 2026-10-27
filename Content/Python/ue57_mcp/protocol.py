"""엔진 코드에 의존하지 않는 MCP JSON-RPC와 도구 모음 레지스트리다."""
import inspect
import json

PROTOCOL = "2025-06-18"

def result_content(value):
    """문자열·구조화된 결과를 MCP 클라이언트가 읽을 수 있는 본문으로 만든다."""
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
    result={"content":[{"type":"text","text":text}]}
    if isinstance(value,dict):result["structuredContent"]=value
    return result

def function_schema(function):
    """도구 함수의 실제 서명에서 입력 스키마와 필수 인수를 구성한다."""
    properties={};required=[]
    types={str:"string",int:"integer",float:"number",bool:"boolean",dict:"object",list:"array"}
    for name,param in inspect.signature(function).parameters.items():
        spec={"type":types[param.annotation]} if param.annotation in types else {}
        if spec.get("type")=="array":spec["items"]={}
        if param.default is inspect.Parameter.empty:required.append(name)
        elif param.default is not None:spec["default"]=param.default
        else:spec={"anyOf":[spec,{"type":"null"}]} if spec else {}
        properties[name]=spec
    return {"type":"object","properties":properties,"required":required,"additionalProperties":False}

class Registry:
    """도구 구현과 공개 스키마를 함께 보관하여 없는 도구의 성공을 방지한다."""
    def __init__(self):
        self.groups={}
    def add(self,group,name,function,description,readonly=False):
        tools=self.groups.setdefault(group,{})
        if name in tools:raise ValueError("Duplicate tool: "+group+"."+name)
        tools[name]={"function":function,"schema":{"name":group+"."+name,"description":description,
            "inputSchema":function_schema(function),"annotations":{"readOnlyHint":readonly,"destructiveHint":not readonly}}}
    def register(self,group,description,readonly=False):
        def decorate(function):
            self.add(group,function.__name__,function,description,readonly)
            return function
        return decorate
    def describe(self,name):
        if name not in self.groups:raise ValueError("Unknown toolset: "+name)
        return {"name":name,"tools":[tool["schema"] for tool in self.groups[name].values()]}
    def call(self,group,name,arguments):
        if group not in self.groups:raise ValueError("Unknown toolset: "+group)
        short=name.removeprefix(group+".")
        if short not in self.groups[group]:raise ValueError("Unknown tool: "+group+"."+name)
        if not isinstance(arguments,dict):raise ValueError("Tool arguments must be an object")
        function=self.groups[group][short]["function"]
        inspect.signature(function).bind(**arguments)
        return function(**arguments)
    def catalog(self):
        return {"toolsets":len(self.groups),"tools":sum(len(group) for group in self.groups.values())}
    def meta_call(self,name,arguments):
        if name=="list_toolsets":
            if arguments:raise ValueError("list_toolsets takes no arguments")
            return "\n".join("- "+group+": UE 5.7 editor toolset ("+str(len(tools))+" tools)" for group,tools in self.groups.items())
        if name=="describe_toolset":return self.describe(arguments["toolset_name"])
        if name=="call_tool":return self.call(arguments["toolset_name"],arguments["tool_name"],arguments.get("arguments",{}))
        raise ValueError("Unknown MCP tool: "+name)

def meta_tools():
    """필요한 도구 모음만 조회하는 MCP 메타 도구 세 개를 제공한다."""
    return [
        {"name":"list_toolsets","description":"List installed UE57-MCP toolsets.","inputSchema":{"type":"object","properties":{},"additionalProperties":False},"annotations":{"readOnlyHint":True}},
        {"name":"describe_toolset","description":"Read the live schema before calling an editor tool.","inputSchema":{"type":"object","properties":{"toolset_name":{"type":"string"}},"required":["toolset_name"],"additionalProperties":False},"annotations":{"readOnlyHint":True}},
        {"name":"call_tool","description":"Execute a discovered tool on the editor main thread.","inputSchema":{"type":"object","properties":{"toolset_name":{"type":"string"},"tool_name":{"type":"string"},"arguments":{"type":"object"}},"required":["toolset_name","tool_name"],"additionalProperties":False},"annotations":{"readOnlyHint":False}}
    ]

class Protocol:
    """도구 호출을 주어진 실행기에 전달하고 JSON-RPC 오류와 도구 오류를 구분한다."""
    def __init__(self,registry,execute):
        self.registry=registry;self.execute=execute
    def handle(self,message):
        if not isinstance(message,dict) or message.get("jsonrpc")!="2.0" or not isinstance(message.get("method"),str):
            return {"jsonrpc":"2.0","id":None,"error":{"code":-32600,"message":"Invalid JSON-RPC request"}}
        identifier=message.get("id");method=message["method"];params=message.get("params",{})
        if "id" not in message:return None
        response={"jsonrpc":"2.0","id":identifier}
        if not isinstance(params,dict):
            response["error"]={"code":-32602,"message":"Parameters must be an object"};return response
        if method=="initialize":
            value={"protocolVersion":PROTOCOL,"capabilities":{"tools":{"listChanged":False}},"serverInfo":{"name":"ue57-mcp","version":"2.0.0"}}
        elif method=="ping":value={}
        elif method=="tools/list":value={"tools":meta_tools()}
        elif method=="tools/call":
            try:value=result_content(self.execute(lambda:self.registry.meta_call(params["name"],params.get("arguments",{}))))
            except Exception as error:
                value=result_content({"error":type(error).__name__,"message":str(error)})
                value["isError"]=True
        else:
            response["error"]={"code":-32601,"message":"Method not found: "+method};return response
        response["result"]=value
        return response
