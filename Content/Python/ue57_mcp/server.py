"""루프백 HTTP 전송과 메인 스레드 큐를 독립 구현한다."""
from concurrent.futures import Future,TimeoutError
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
import queue
import threading
import time
import uuid
from urllib.parse import urlsplit
from .protocol import Protocol

class MainThreadQueue:
    """HTTP 스레드의 엔진 작업을 Slate 틱에서만 실행한다."""
    def __init__(self,timeout=60):
        self.items=queue.Queue(maxsize=128);self.timeout=timeout;self.closed=False
    def execute(self,function):
        if self.closed:raise RuntimeError("The editor execution queue has stopped")
        future=Future()
        try:self.items.put_nowait((future,function))
        except queue.Full:raise RuntimeError("Editor queue is full; retry after pending work completes") from None
        try:return future.result(timeout=self.timeout)
        except TimeoutError:
            future.cancel()
            raise RuntimeError("Editor call timed out. Check compilation and editor responsiveness before retrying mutations.") from None
    def tick(self,delta_time=0):
        until=time.monotonic()+0.006
        while not self.closed and time.monotonic()<until:
            try:future,function=self.items.get_nowait()
            except queue.Empty:break
            if not future.set_running_or_notify_cancel():continue
            try:future.set_result(function())
            except Exception as error:future.set_exception(error)
    def close(self):
        self.closed=True
        while True:
            try:future,_=self.items.get_nowait()
            except queue.Empty:break
            future.cancel()

class MCPServer(ThreadingHTTPServer):
    """세션과 Origin을 검사하며 엔진 작업의 실행 위치를 제어한다."""
    daemon_threads=True
    block_on_close=False
    allow_reuse_address=True
    def __init__(self,registry,execute,port=8000):
        self.protocol=Protocol(registry,execute)
        self.sessions={};self.session_lock=threading.Lock()
        super().__init__(("127.0.0.1",port),Handler)
    def valid_session(self,value):
        now=time.monotonic()
        with self.session_lock:
            if not value or self.sessions.get(value,0)<now:return False
            self.sessions[value]=now+1800
            return True
    def new_session(self):
        now=time.monotonic()
        with self.session_lock:
            self.sessions={key:expiry for key,expiry in self.sessions.items() if expiry>now}
            if len(self.sessions)>=128:
                self.sessions.pop(min(self.sessions,key=self.sessions.get))
            value=uuid.uuid4().hex;self.sessions[value]=now+1800
            return value

class Handler(BaseHTTPRequestHandler):
    """비브라우저 로컬 MCP 요청을 JSON 응답으로 처리한다."""
    protocol_version="HTTP/1.1"
    def log_message(self,format,*args):pass
    def respond(self,status,payload=None,session=None):
        data=b"" if payload is None else json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.send_header("Cache-Control","no-store")
        self.send_header("Connection","close")
        if session:self.send_header("Mcp-Session-Id",session)
        self.end_headers();self.close_connection=True
        if data:
            try:self.wfile.write(data)
            except (BrokenPipeError,ConnectionResetError):pass
    def allowed(self):
        if self.path!="/mcp":self.respond(404,{"error":"Use /mcp"});return False
        port=self.server.server_address[1]
        if self.headers.get("Host","").lower() not in {f"127.0.0.1:{port}",f"localhost:{port}"}:
            self.respond(403,{"error":"Invalid Host"});return False
        origin=self.headers.get("Origin")
        if origin:
            parsed=urlsplit(origin)
            if parsed.scheme!="http" or parsed.netloc.lower() not in {f"localhost:{port}",f"127.0.0.1:{port}"}:
                self.respond(403,{"error":"Origin is not allowed"});return False
        return True
    def do_POST(self):
        if not self.allowed():return
        if self.headers.get("Transfer-Encoding"):
            self.respond(400,{"error":"Chunked requests are unsupported"});return
        if self.headers.get("Content-Type","").split(";",1)[0].strip()!="application/json":
            self.respond(415,{"error":"Use application/json"});return
        try:length=int(self.headers.get("Content-Length","0"))
        except ValueError:length=0
        if not 0<length<=1024*1024:self.respond(413,{"error":"Invalid request size"});return
        self.connection.settimeout(15)
        try:message=json.loads(self.rfile.read(length).decode("utf-8"))
        except (ValueError,UnicodeError,TimeoutError,OSError):
            self.respond(400,{"error":"Invalid JSON request"});return
        is_initialize=isinstance(message,dict) and message.get("method")=="initialize"
        session=self.headers.get("Mcp-Session-Id")
        if not is_initialize and not self.server.valid_session(session):
            self.respond(404,{"error":"Unknown MCP session; initialize again"});return
        response=self.server.protocol.handle(message)
        if is_initialize and response and "result" in response:session=self.server.new_session()
        self.respond(200 if response is not None else 202,response,session)
    def do_GET(self):
        if self.allowed():self.respond(405,{"error":"This server uses POST JSON responses; SSE is unsupported"})
    def do_DELETE(self):
        if not self.allowed():return
        session=self.headers.get("Mcp-Session-Id")
        if not self.server.valid_session(session):self.respond(404,{"error":"Unknown MCP session"});return
        with self.server.session_lock:self.server.sessions.pop(session,None)
        self.respond(200,{})

def serve(registry,execute,port=8000):
    """HTTP 수신 스레드를 시작하고 에디터 종료 시 정리할 서버를 반환한다."""
    if not isinstance(port,int) or not 1<=port<=65535:raise ValueError("Port must be 1..65535")
    server=MCPServer(registry,execute,port)
    threading.Thread(target=server.serve_forever,name="UE57-MCP-HTTP",daemon=True).start()
    return server
