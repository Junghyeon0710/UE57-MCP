"""공개 소스 MCP의 실제 HTTP 규약·메인 스레드 실행·검색을 검증한다."""
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"Content/Python"))
from ue57_mcp.protocol import Registry,Protocol
from ue57_mcp.server import MCPServer,MainThreadQueue
from ue57_mcp.semantic import SearchIndex,cosine
from ue57_mcp.runtime import Runtime
from ue57_mcp.toolsets import register_domain

class SourceProtocolTests(unittest.TestCase):
    def setUp(self):
        self.registry=Registry()
        def echo(value):return {"value":value}
        def fail():raise ValueError("expected tool failure")
        self.registry.add("ue57.test","echo",echo,"Echo a structured argument",True)
        self.registry.add("ue57.test","fail",fail,"Return a tool error")
        self.protocol=Protocol(self.registry,lambda function:function())
    def test_live_schema_required_arguments_and_structured_result(self):
        schema=self.registry.describe("ue57.test")
        self.assertEqual(schema["tools"][0]["inputSchema"]["required"],["value"])
        message={"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"call_tool","arguments":{
            "toolset_name":"ue57.test","tool_name":"echo","arguments":{"value":{"nested":[1,True,"text"]}}}}}
        response=self.protocol.handle(message)
        self.assertEqual(response["result"]["structuredContent"],{"value":{"nested":[1,True,"text"]}})
    def test_tool_failure_is_not_success(self):
        response=self.protocol.handle({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"call_tool","arguments":{
            "toolset_name":"ue57.test","tool_name":"fail"}}})
        self.assertTrue(response["result"]["isError"])
    def test_invalid_requests_and_notifications(self):
        self.assertEqual(self.protocol.handle([])["error"]["code"],-32600)
        self.assertIsNone(self.protocol.handle({"jsonrpc":"2.0","method":"notifications/initialized"}))
        self.assertEqual(self.protocol.handle({"jsonrpc":"2.0","id":1,"method":"missing"})["error"]["code"],-32601)

class SourceHTTPTests(unittest.TestCase):
    def setUp(self):
        registry=Registry()
        self.server=MCPServer(registry,lambda function:function(),0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.close)
    def close(self):
        self.server.shutdown();self.server.server_close();self.thread.join(timeout=2)
    def request(self,message,headers=None,method="POST"):
        connection=http.client.HTTPConnection("127.0.0.1",self.server.server_address[1],timeout=3)
        try:
            connection.request(method,"/mcp",json.dumps(message),{"Content-Type":"application/json",**(headers or {})})
            response=connection.getresponse();data=response.read()
            return response.status,response.getheader("Mcp-Session-Id"),json.loads(data) if data else None
        finally:connection.close()
    def test_initialize_session_ping_and_notifications(self):
        status,session,body=self.request({"jsonrpc":"2.0","id":1,"method":"initialize","params":{}})
        self.assertEqual(status,200);self.assertTrue(session)
        self.assertEqual(body["result"]["protocolVersion"],"2025-06-18")
        self.assertEqual(self.request({"jsonrpc":"2.0","method":"notifications/initialized"},{"Mcp-Session-Id":session})[0],202)
        self.assertEqual(self.request({"jsonrpc":"2.0","id":2,"method":"ping"},{"Mcp-Session-Id":session})[2]["result"],{})
    def test_origin_host_and_missing_session_rejected(self):
        message={"jsonrpc":"2.0","id":1,"method":"initialize"}
        self.assertEqual(self.request(message,{"Origin":"https://untrusted.example"})[0],403)
        self.assertEqual(self.request(message,{"Host":"untrusted.example"})[0],403)
        self.assertEqual(self.request({"jsonrpc":"2.0","id":2,"method":"ping"})[0],404)

class SourceQueueTests(unittest.TestCase):
    def test_engine_work_executes_on_tick_thread(self):
        queue=MainThreadQueue(timeout=2);results=[]
        worker=threading.Thread(target=lambda:results.append(queue.execute(threading.get_ident)))
        worker.start();deadline=time.monotonic()+2
        while worker.is_alive() and time.monotonic()<deadline:
            queue.tick();time.sleep(0.001)
        worker.join(timeout=1);queue.close()
        self.assertEqual(results,[threading.get_ident()])
    def test_timeout_cancels_queued_mutation(self):
        queue=MainThreadQueue(timeout=0.01);mutations=[]
        with self.assertRaisesRegex(RuntimeError,"timed out"):
            queue.execute(lambda:mutations.append("unexpected"))
        queue.tick();queue.close()
        self.assertEqual(mutations,[])
        with self.assertRaisesRegex(RuntimeError,"stopped"):queue.execute(lambda:None)

class SourceSerializationTests(unittest.TestCase):
    def test_struct_constants_are_not_recursively_traversed(self):
        class Object:pass
        class CustomStruct:
            @property
            def constant(self):raise AssertionError("Struct constants must not be inspected")
            def export_text(self):return "(Value=42)"
        runtime=object.__new__(Runtime);runtime.ue=SimpleNamespace(Object=Object)
        self.assertEqual(runtime.encode(CustomStruct()),{"$struct":"CustomStruct","$text":"(Value=42)"})
    def test_domain_discovery_filters_before_limiting_results(self):
        namespace=SimpleNamespace(**{f"AType{index}":None for index in range(2200)},Texture2D=None)
        runtime=SimpleNamespace(ue=namespace)
        registry=Registry();register_domain(registry,runtime,"texture",["Texture*"])
        self.assertEqual(registry.call("ue57.texture","list_types",{}),["Texture2D"])

class SourceSemanticTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.index=SearchIndex(temporary.name)
        self.index.configure("http://127.0.0.1:1234/v1","fixture",2)
        self.index.embed=lambda text,config:[1.0,0.0] if "red" in text else [0.0,1.0]
    def wait(self,job):
        deadline=time.monotonic()+2
        while time.monotonic()<deadline:
            result=self.index.job_status(job["job_id"])
            if result["state"]!="running":return result
            time.sleep(0.001)
        self.fail("Semantic job did not finish")
    def test_index_query_and_stored_similarity(self):
        result=self.wait(self.index.start_index([{"path":"/Game/red","name":"red"},{"path":"/Game/blue","name":"blue"}]))
        self.assertEqual(result["result"]["indexed"],2)
        result=self.wait(self.index.search("red",2))
        self.assertEqual(result["result"][0]["path"],"/Game/red")
        self.assertAlmostEqual(result["result"][0]["score"],1)
    def test_changed_model_requires_reindex(self):
        self.wait(self.index.start_index([{"path":"/Game/red","name":"red"}]))
        self.index.configure("http://127.0.0.1:1234/v1","other",2)
        with self.assertRaisesRegex(ValueError,"rebuild"):self.index.search("red",1)
    def test_failed_index_job_preserves_previous_index(self):
        self.wait(self.index.start_index([{"path":"/Game/red","name":"red"}]))
        previous=json.loads(json.dumps(self.index.index))
        def fail(text,config):raise ValueError("fixture model failure")
        self.index.embed=fail
        result=self.wait(self.index.start_index([{"path":"/Game/blue","name":"blue"}]))
        self.assertEqual(result["state"],"failed")
        self.assertEqual(self.index.index,previous)
    def test_vector_dimension_mismatch_rejected(self):
        with self.assertRaisesRegex(ValueError,"dimensions"):cosine([1,0],[1,0,0])

if __name__=="__main__":unittest.main()
