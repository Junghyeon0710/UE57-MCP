"""5.7의 공개 Python API를 JSON 값과 객체 참조로 연결한다."""
from collections import OrderedDict
import contextlib
import fnmatch
import inspect
import io
import json
import math
from pathlib import Path

class Runtime:
    """에디터 메인 스레드에서 객체 참조·리플렉션·도구 실행을 관리한다."""
    def __init__(self,unreal):
        self.ue=unreal;self.references=OrderedDict()
        self.namespace={"unreal":unreal,"runtime":self}
        self.saved=Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()))/"UE57MCP"
    def reference(self,path):
        if path in self.references:return self.references[path]
        obj=self.ue.find_object(None,path) or self.ue.load_object(None,path)
        if obj is None:raise ValueError("Object not found: "+path)
        return obj
    def api_type(self,name):
        if not isinstance(name,str) or not name or name.startswith("_"):raise ValueError("Expected a public Unreal API type name")
        value=getattr(self.ue,name,None)
        if value is None:raise ValueError("Unreal API type is unavailable in this editor: "+name)
        return value
    def decode(self,value):
        if isinstance(value,list):return [self.decode(item) for item in value]
        if not isinstance(value,dict):return value
        if "$ref" in value:return self.reference(value["$ref"])
        if "$class" in value:
            name=value["$class"]
            if name.startswith("/"):
                result=self.ue.load_class(None,name)
                if result is None:raise ValueError("Class not found: "+name)
                return result
            return self.api_type(name)
        if "$subsystem" in value:return self.ue.get_editor_subsystem(self.api_type(value["$subsystem"]))
        if "$enum" in value:return getattr(self.api_type(value["$enum"]),value["value"])
        if "$struct" in value:
            struct=self.api_type(value["$struct"])(**{key:self.decode(item) for key,item in value.items() if not key.startswith("$")})
            if "$text" in value and not struct.import_text(value["$text"]):raise ValueError("Struct text could not be imported")
            return struct
        return {key:self.decode(item) for key,item in value.items()}
    def encode(self,value,depth=0):
        if isinstance(value,float) and not math.isfinite(value):return str(value)
        if value is None or isinstance(value,(str,int,float,bool)):return value
        if depth>8:return str(value)
        if isinstance(value,self.ue.Object):
            path=value.get_path_name();self.references[path]=value;self.references.move_to_end(path)
            while len(self.references)>2048:self.references.popitem(last=False)
            return {"$ref":path,"$type":type(value).__name__}
        if isinstance(value,dict):return {str(key):self.encode(item,depth+1) for key,item in value.items()}
        if isinstance(value,(list,tuple,set)) or type(value).__name__ in {"Array","Set"}:
            return [self.encode(item,depth+1) for item in value]
        if type(value).__name__=="Map":return {str(key):self.encode(item,depth+1) for key,item in value.items()}
        field_names={"Vector":("x","y","z"),"Vector2D":("x","y"),"IntPoint":("x","y"),
            "IntVector":("x","y","z"),"Rotator":("pitch","yaw","roll"),"Quat":("x","y","z","w"),
            "LinearColor":("r","g","b","a"),"Color":("r","g","b","a"),
            "Transform":("translation","rotation","scale3d"),"Margin":("left","top","right","bottom"),
            "Anchors":("minimum","maximum")}.get(type(value).__name__)
        if field_names:
            return {"$struct":type(value).__name__,**{name:self.encode(getattr(value,name),depth+1) for name in field_names}}
        # 구조체 상수도 같은 구조체를 반환할 수 있으므로 모든 디스크립터를 재귀 순회하지 않는다.
        if callable(getattr(value,"export_text",None)):
            return {"$struct":type(value).__name__,"$text":value.export_text()}
        enum_name=getattr(value,"name",None)
        if isinstance(enum_name,str) and hasattr(type(value),enum_name):return {"$enum":type(value).__name__,"value":enum_name}
        return str(value)
    def resolve(self,target):
        if isinstance(target,dict):return self.decode(target)
        if target=="unreal":return self.ue
        if isinstance(target,str):return self.reference(target) if target.startswith("/") else self.api_type(target)
        raise ValueError("Use an Unreal type name or a tagged object/subsystem reference")
    def invoke(self,target,method,args=None,kwargs=None):
        if not isinstance(method,str) or method.startswith("_"):raise ValueError("Use a public API method name")
        obj=self.resolve(target);function=getattr(obj,method,None)
        if not callable(function):raise ValueError("Method is unavailable: "+method)
        return self.encode(function(*self.decode(args or []),**self.decode(kwargs or {})))
    def type_names(self,pattern="*",limit=200):
        return [name for name in dir(self.ue) if not name.startswith("_") and fnmatch.fnmatchcase(name.lower(),pattern.lower())][:max(1,min(limit,2000))]
    def describe(self,name,pattern="*",limit=80):
        obj=self.api_type(name);members=[]
        for member in dir(obj):
            if member.startswith("_") or not fnmatch.fnmatchcase(member.lower(),pattern.lower()):continue
            value=getattr(obj,member,None)
            members.append({"name":member,"callable":callable(value),"documentation":(inspect.getdoc(value) or "")[:8000]})
            if len(members)>=max(1,min(limit,500)):break
        return {"name":name,"documentation":(inspect.getdoc(obj) or "")[:8000],"members":members}
    def properties(self,target):
        obj=self.resolve(target);result=[]
        for name in dir(type(obj)):
            if name.startswith("_"):continue
            descriptor=inspect.getattr_static(type(obj),name,None)
            if not inspect.isdatadescriptor(descriptor):continue
            try:value=obj.get_editor_property(name)
            except Exception:continue
            result.append({"name":name,"value":self.encode(value),"documentation":(inspect.getdoc(descriptor) or "")[:1000]})
        return result
    def read_properties(self,target,names):
        obj=self.resolve(target)
        return {name:self.encode(obj.get_editor_property(name)) for name in names}
    def write_properties(self,target,values):
        obj=self.resolve(target);decoded={key:self.decode(value) for key,value in values.items()}
        before={key:obj.get_editor_property(key) for key in decoded}
        with self.ue.ScopedEditorTransaction("UE57 MCP: set properties"):
            if hasattr(obj,"modify"):obj.modify()
            try:
                for key,value in decoded.items():obj.set_editor_property(key,value)
            except Exception:
                for key,value in before.items():obj.set_editor_property(key,value)
                raise
        return self.read_properties(target,list(decoded))
    def execute_python(self,code):
        buffer=io.StringIO();self.namespace["result"]=None
        with contextlib.redirect_stdout(buffer):exec(compile(code,"<ue57-mcp>","exec"),self.namespace,self.namespace)
        return {"result":self.encode(self.namespace.get("result")),"stdout":buffer.getvalue()[-65536:]}
    def native(self,operation,arguments):
        bridge=getattr(self.ue,"UE57MCPNativeLibrary",None)
        if bridge is None:raise ValueError("This tool needs the optional UE57MCPNative plugin. Install its source and build it using UE 5.7; see docs/setup.md.")
        result=json.loads(bridge.execute(operation,json.dumps(arguments,ensure_ascii=False)))
        if not result.get("ok"):raise RuntimeError(result.get("error","Native editor operation failed"))
        return result
