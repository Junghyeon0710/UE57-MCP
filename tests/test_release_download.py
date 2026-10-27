"""라이선스 접근 확인과 고정 다운로드 무결성을 엔진·네트워크 없이 검증한다."""
import copy
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("release_download",ROOT/"scripts/release_download.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Client:
    """검사 순서와 요청 경로를 기록하는 합성 GitHub 응답을 제공한다."""
    def __init__(self,descriptor,payload):
        self.payload=payload;self.calls=[]
        self.repo={"private":True,"fork":True,"source":{"full_name":m.UPSTREAM}}
        self.release={"draft":False,"tag_name":descriptor["tag"],"assets":[{
            "id":123,"name":descriptor["asset"],"state":"uploaded","size":descriptor["bytes"],
            "digest":"sha256:"+descriptor["sha256"]}]}
    def json(self,path):
        self.calls.append(path)
        return self.release if "/releases/" in path else self.repo
    def open(self,path,binary=False):
        self.calls.append(path)
        return io.BytesIO(self.payload)

class ReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(prefix="ue57-download-test-")
        self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.payload=b"synthetic archive fixture"
        self.descriptor={"format":1,"status":"published","repository":"fixture/EngineFork","tag":"v1",
            "asset":"plugins.zip","bytes":len(self.payload),"sha256":hashlib.sha256(self.payload).hexdigest()}
        self.client=Client(self.descriptor,self.payload)

    def fetch(self):return m.fetch(self.descriptor,self.root/"cache",self.client)

    def test_download_checks_network_and_pinned_payload(self):
        target=self.fetch()
        self.assertEqual(target.read_bytes(),self.payload)
        self.assertEqual(self.client.calls,["/repos/fixture/EngineFork","/repos/fixture/EngineFork/releases/tags/v1","/repos/fixture/EngineFork/releases/assets/123"])
        self.assertFalse(target.with_name(target.name+".partial").exists())

    def test_unpublished_release_stops_before_credentials_or_writes(self):
        self.descriptor["status"]="pending_publication"
        with patch.object(m,"github_token") as credentials:
            with self.assertRaisesRegex(ValueError,"not published"):
                m.fetch(self.descriptor,self.root/"cache")
            credentials.assert_not_called()
        self.assertFalse((self.root/"cache").exists())

    def test_unrelated_or_public_repository_rejected_before_payload(self):
        for changes in [{"private":False},{"fork":False},{"source":{"full_name":"other/Engine"}}]:
            with self.subTest(changes=changes):
                client=Client(self.descriptor,self.payload);client.repo.update(changes)
                with self.assertRaisesRegex(ValueError,"Epic"):
                    m.fetch(self.descriptor,self.root/"cache",client)
                self.assertEqual(len(client.calls),1)

    def test_replaced_release_asset_rejected(self):
        self.client.release["assets"][0]["digest"]="sha256:"+"0"*64
        with self.assertRaisesRegex(ValueError,"digest"):self.fetch()
        self.assertFalse((self.root/"cache").exists())

    def test_corrupt_download_is_removed(self):
        self.client.payload=b"x"*len(self.payload)
        with self.assertRaisesRegex(ValueError,"SHA256"):self.fetch()
        self.assertEqual(list((self.root/"cache").iterdir()),[])

    def test_truncated_or_oversized_download_is_removed(self):
        for payload in [b"small",self.payload+b"extra"]:
            self.client.payload=payload
            with self.subTest(size=len(payload)),self.assertRaises(ValueError):self.fetch()
            self.assertEqual(list((self.root/"cache").iterdir()),[])

    def test_existing_partial_download_is_not_deleted(self):
        cache=self.root/"cache";cache.mkdir();partial=cache/"plugins.zip.partial";partial.write_bytes(b"another process")
        with self.assertRaisesRegex(ValueError,"partial"):self.fetch()
        self.assertEqual(partial.read_bytes(),b"another process")

    def test_cached_zip_is_rehashed_and_access_is_still_checked(self):
        target=self.fetch();self.client.calls=[]
        self.assertEqual(self.fetch(),target)
        self.assertEqual(len(self.client.calls),2)
        target.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"Cached"):self.fetch()
        self.assertEqual(target.read_bytes(),b"changed")

    def test_descriptor_paths_and_hashes_rejected(self):
        for key,value in [("repository","../.."),("repository","https://example.com/x"),("asset","../x.zip"),("tag","../x"),("sha256","short"),("bytes",0)]:
            data=copy.deepcopy(self.descriptor);data[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_descriptor(data)

    def test_authorization_not_forwarded_to_asset_host(self):
        request=urllib.request.Request(m.API+"/repos/fixture/EngineFork/releases/assets/123")
        request.add_unredirected_header("Authorization","Bearer synthetic-fixture")
        redirected=m.GitHubRedirect().redirect_request(request,None,302,"Found",{},"https://release-assets.githubusercontent.com/example")
        self.assertIsNone(redirected.get_header("Authorization"))
        with self.assertRaisesRegex(ValueError,"redirect"):
            m.GitHubRedirect().redirect_request(request,None,302,"Found",{},"https://example.com/asset")

    def test_access_error_has_actionable_message_without_token(self):
        client=m.GitHub("synthetic-fixture")
        with patch.object(client.opener,"open",side_effect=urllib.error.HTTPError(m.API,404,"Not Found",{},None)):
            with self.assertRaisesRegex(ValueError,"EpicGames/UnrealEngine") as error:client.json("/repos/fixture/EngineFork")
        self.assertNotIn("synthetic-fixture",str(error.exception))

    def test_release_download_through_install_needs_only_engine57(self):
        from test_prebuilt import api,prebuilt
        engine=self.root/"only-engine57"
        api.write_json(engine/"Engine/Build/Build.version",{"MajorVersion":5,"MinorVersion":7,"PatchVersion":4})
        api.write_json(engine/"Engine/Binaries/Win64/UnrealEditor.modules",{"BuildId":"fixture-build"})
        bundle=self.root/"bundle"
        modules=bundle/"ModelContextProtocol/Binaries/Win64/UnrealEditor.modules"
        api.write_json(modules,{"BuildId":"fixture-build","Modules":{"ModelContextProtocol":"UnrealEditor-ModelContextProtocol.dll"}})
        (modules.parent/"UnrealEditor-ModelContextProtocol.dll").write_bytes(b"synthetic module")
        api.write_json(bundle/api.MARKER,{"assets_ready":True,"files":{}})
        project=self.root/"game/Sample.uproject";api.write_json(project,{"FileVersion":3,"EngineAssociation":"5.7"})
        original=project.read_bytes()
        with patch.object(prebuilt.platform,"system",return_value="Windows"):
            archive=self.root/"fixture.zip";packed=prebuilt.pack(bundle,engine,archive,api)
            descriptor=dict(self.descriptor,bytes=packed["bytes"],sha256=packed["sha256"],platform="Win64",engine_version="5.7.4",engine_build_id="fixture-build")
            client=Client(descriptor,archive.read_bytes())
            with patch.object(m,"github_token",return_value="synthetic-fixture"),patch.object(m,"GitHub",return_value=client):
                target=m.install(descriptor,engine,project,8004,self.root/"cache",api,prebuilt)
        self.assertEqual(project.read_bytes(),original)
        self.assertTrue((target/"Licenses/FAISS-v1.13.2.license").is_file())
        self.assertIn("ServerPortNumber=8004",(project.parent/"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini").read_text())
        self.assertFalse((self.root/"engine58").exists())

if __name__=="__main__":unittest.main()
