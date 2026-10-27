"""5.7 에디터에서 서버 수명과 Slate 틱을 연결한다."""
import atexit
import json
from pathlib import Path

_state=None

def start(port=None):
    """사용자의 Saved 설정을 읽고 로컬 서버를 한 번만 시작한다."""
    global _state
    import unreal
    from .runtime import Runtime
    from .server import MainThreadQueue,serve
    from .toolsets import create_registry
    if _state:return {"running":True,"port":_state["server"].server_address[1]}
    version=unreal.SystemLibrary.get_engine_version()
    if not version.startswith("5.7."):
        unreal.log_warning("UE57-MCP supports UE 5.7; this editor is "+version)
        return {"running":False,"reason":"Engine version is not UE 5.7"}
    runtime=Runtime(unreal)
    config_path=runtime.saved/"server.json"
    config=json.loads(config_path.read_text(encoding="utf-8-sig")) if config_path.exists() else {}
    if port is None and not config.get("auto_start",True):return {"running":False,"reason":"Auto-start is disabled"}
    port=int(port if port is not None else config.get("port",8000))
    registry=create_registry(runtime)
    work=MainThreadQueue(timeout=60)
    try:server=serve(registry,work.execute,port)
    except OSError as error:
        unreal.log_warning("UE57-MCP could not bind localhost port "+str(port)+": "+str(error))
        return {"running":False,"reason":"Port is unavailable","port":port}
    callback=unreal.register_slate_post_tick_callback(work.tick)
    _state={"server":server,"queue":work,"callback":callback,"registry":registry,"runtime":runtime}
    atexit.register(stop)
    unreal.log("UE57-MCP 2.0.0: http://127.0.0.1:"+str(port)+"/mcp; "+str(registry.catalog()))
    return {"running":True,"port":port,**registry.catalog()}

def stop():
    """서버·대기 요청·Slate 콜백을 정리하고 재시작을 허용한다."""
    global _state
    state=_state;_state=None
    if not state:return
    state["queue"].close()
    state["server"].shutdown();state["server"].server_close()
    try:
        import unreal
        unreal.unregister_slate_post_tick_callback(state["callback"])
    except Exception:pass
