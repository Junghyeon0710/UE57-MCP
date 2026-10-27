"""5.8 없는 설치와 압축 무결성·빌드 호환성 검사를 합성 데이터로 검증한다."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]

def load(name, relative):
    spec=importlib.util.spec_from_file_location(name,ROOT/relative)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

api=load("installer","scripts/ue57_mcp.py")
prebuilt=load("prebuilt","scripts/prebuilt_bundle.py")

class PrebuiltTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory(prefix="ue57-prebuilt-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)
        self.engine=self.root/"only-engine57"
        api.write_json(self.engine/"Engine/Build/Build.version",{"MajorVersion":5,"MinorVersion":7,"PatchVersion":4})
        api.write_json(self.engine/"Engine/Binaries/Win64/UnrealEditor.modules",{"BuildId":"fixture-build"})
        self.bundle=self.root/"bundle"
        self.modules=self.bundle/"ModelContextProtocol/Binaries/Win64/UnrealEditor.modules"
        api.write_json(self.modules,{"BuildId":"fixture-build","Modules":{"ModelContextProtocol":"UnrealEditor-ModelContextProtocol.dll"}})
        (self.modules.parent/"UnrealEditor-ModelContextProtocol.dll").write_bytes(b"synthetic module fixture")
        lib=self.bundle/"SemanticSearch/Source/ThirdParty/example.lib"
        lib.parent.mkdir(parents=True);lib.write_bytes(b"required synthetic static library")
        (self.modules.parent/"generated.lib").write_bytes(b"excluded build output")
        api.write_json(self.bundle/api.MARKER,{"assets_ready":True,"files":{lib.relative_to(self.bundle).as_posix():api.digest(lib.read_bytes())}})
        self.project=self.root/"game/Sample.uproject"
        api.write_json(self.project,{"FileVersion":3,"EngineAssociation":"5.7"})
        self.archive=self.root/"package.zip"
        mock=patch.object(prebuilt.platform,"system",return_value="Windows")
        mock.start();self.addCleanup(mock.stop)

    def pack(self):
        return prebuilt.pack(self.bundle,self.engine,self.archive,api)

    def rewrite(self, edit):
        with zipfile.ZipFile(self.archive) as archive:
            entries={name:archive.read(name) for name in archive.namelist()}
        edit(entries)
        with zipfile.ZipFile(self.archive,"w") as archive:
            for name,data in entries.items():archive.writestr(name,data)

    def test_roundtrip_requires_only_engine57_and_preserves_project(self):
        original=self.project.read_bytes();result=self.pack()
        self.assertEqual(result["sha256"],api.digest(self.archive.read_bytes()))
        target=prebuilt.install_archive(self.archive,self.engine,self.project,8003,api)
        self.assertEqual(original,self.project.read_bytes())
        self.assertTrue((target/"SemanticSearch/Source/ThirdParty/example.lib").is_file())
        self.assertFalse((target/"ModelContextProtocol/Binaries/Win64/generated.lib").exists())
        self.assertTrue((target/"Licenses/FAISS-v1.13.2.license").is_file())
        self.assertTrue((target/"Licenses/OpenBLAS-v0.3.31.license").is_file())
        self.assertTrue((target/"Licenses/Engine-tools-NOTICE.txt").is_file())
        self.assertIn("ServerPortNumber=8003",(self.project.parent/"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini").read_text())
        self.assertFalse((self.root/"engine58").exists())

    def test_different_engine_build_rejected_before_install(self):
        self.pack()
        api.write_json(self.engine/"Engine/Binaries/Win64/UnrealEditor.modules",{"BuildId":"different"})
        with self.assertRaisesRegex(ValueError,"BuildId"):
            prebuilt.install_archive(self.archive,self.engine,self.project,8000,api)
        self.assertFalse((self.project.parent/"Plugins").exists())

    def test_changed_payload_rejected_before_install(self):
        self.pack()
        self.rewrite(lambda entries:entries.update({"plugins/ModelContextProtocol/Binaries/Win64/UnrealEditor-ModelContextProtocol.dll":b"changed"}))
        with self.assertRaisesRegex(ValueError,"integrity"):
            prebuilt.install_archive(self.archive,self.engine,self.project,8000,api)
        self.assertFalse((self.project.parent/"Plugins").exists())

    def test_unlisted_archive_payload_rejected(self):
        self.pack();self.rewrite(lambda entries:entries.update({"plugins/extra.txt":b"extra"}))
        with self.assertRaisesRegex(ValueError,"unlisted"):
            prebuilt.install_archive(self.archive,self.engine,self.project,8000,api)

    def test_traversal_in_manifest_rejected(self):
        self.pack()
        def edit(entries):
            metadata=json.loads(entries["prebuilt.json"])
            metadata["files"]["../escaped.txt"]=api.digest(b"escape")
            entries["plugins/../escaped.txt"]=b"escape"
            entries["prebuilt.json"]=json.dumps(metadata).encode()
        self.rewrite(edit)
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            prebuilt.install_archive(self.archive,self.engine,self.project,8000,api)
        self.assertFalse((self.root/"escaped.txt").exists())

    def test_missing_compiled_module_rejected(self):
        (self.modules.parent/"UnrealEditor-ModelContextProtocol.dll").unlink()
        with self.assertRaisesRegex(ValueError,"missing"):self.pack()
        self.assertFalse(self.archive.exists())

    def test_mixed_module_build_ids_rejected(self):
        api.write_json(self.bundle/"Other/Binaries/Win64/UnrealEditor.modules",{"BuildId":"other","Modules":{}})
        with self.assertRaisesRegex(ValueError,"BuildId"):self.pack()

    def test_archive_path_aliases_rejected(self):
        for name in ["../a","/a","a\\b","C:/a","a//b","a/./b","a./b","a /b"]:
            with self.subTest(name=name),self.assertRaises(ValueError):prebuilt.safe_relative(name)

if __name__=="__main__":unittest.main()
