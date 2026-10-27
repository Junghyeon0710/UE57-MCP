"""엔진 없이 경로 검증, 조립 무결성, 로컬 설치와 복구를 검사한다."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("installer",ROOT/"scripts/ue57_mcp.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="ue57-test-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.source=self.root/"source";self.source.mkdir()
        (self.source/"base.txt").write_bytes(b"first\r\nsecond\r\n")
        self.recipe={"format":1,"source_versions":{},"sources":{"a":{"root":"fixture","path":"base.txt","sha256":m.digest((self.source/"base.txt").read_bytes())}},
            "files":[{"path":"Example/result.txt","mode":"text","sha256":m.digest(b"first\nchanged\n"),"pieces":[["copy","a",0,1],["text","changed\n"]]}]}
    def assemble(self):
        return m.assemble(self.recipe,{"fixture":self.source},self.root/"output",False)
    def bundle(self):
        b=self.root/"bundle";b.mkdir()
        (b/"payload.txt").write_text("fixture",encoding="utf-8")
        m.write_json(b/m.MARKER,{"assets_ready":True,"files":{"payload.txt":m.digest(b"fixture")}})
        return b
    def project(self,git=False):
        p=self.root/"game/Sample.uproject";m.write_json(p,{"FileVersion":3,"EngineAssociation":"5.7"})
        if git:subprocess.run(["git","init","-q",str(p.parent)],check=True,capture_output=True)
        return p
    def test_assembly_preserves_verified_semantics(self):
        self.assertEqual(self.assemble(),1)
        self.assertEqual((self.root/"output/Example/result.txt").read_bytes(),b"first\nchanged\n")
    def test_wrong_source_hash_fails_before_output(self):
        (self.source/"base.txt").write_text("different")
        with self.assertRaises(ValueError):self.assemble()
        self.assertFalse((self.root/"output").exists())
    def test_wrong_result_hash_is_atomic(self):
        self.recipe["files"][0]["sha256"]="0"*64
        with self.assertRaises(ValueError):self.assemble()
        self.assertFalse((self.root/"output").exists())
    def test_path_traversal_rejected(self):
        for rel in ["../escape","/absolute","C:/outside","a\\b"]:
            with self.subTest(rel=rel),self.assertRaises(ValueError):m.inside(self.root,rel)
    def test_existing_output_not_overwritten(self):
        self.assemble()
        with self.assertRaises(FileExistsError):self.assemble()
    def test_invalid_source_range_rejected(self):
        self.recipe["files"][0]["pieces"]=[["copy","a",0,50]]
        with self.assertRaises(ValueError):self.assemble()
    def test_duplicate_target_rejected(self):
        self.recipe["files"].append(self.recipe["files"][0])
        with self.assertRaises(ValueError):self.assemble()
    def test_ini_preserves_arrays_and_other_sections(self):
        text="[Other]\nKeep=True\n[Asset]\n+Types=Existing\n"
        result=m.ini_section(text,"Asset",{"+Types":"New"})
        self.assertIn("+Types=Existing",result);self.assertIn("+Types=New",result);self.assertIn("Keep=True",result)
    def test_ini_replaces_only_requested_key(self):
        result=m.ini_section("[MCP]\nPort=1\nKeep=True\n[Other]\nPort=2\n","MCP",{"Port":"8000"})
        self.assertIn("Port=8000",result);self.assertIn("Keep=True",result);self.assertIn("[Other]\nPort=2",result)
    def test_install_preserves_project_descriptor_and_ignores_plugins(self):
        p=self.project(True);before=p.read_bytes();b=self.bundle()
        target=m.install(b,p)
        self.assertEqual(p.read_bytes(),before)
        ignored=subprocess.check_output(["git","-C",str(p.parent),"check-ignore",str(target/"payload.txt")],text=True)
        self.assertIn("payload.txt",ignored)
        self.assertTrue((target/"AllToolsets/Config/Game.ini").exists())
        saved=p.parent/"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini"
        self.assertTrue(subprocess.check_output(["git","-C",str(p.parent),"check-ignore",str(saved)],text=True))
    def test_existing_gamefeature_rule_is_preserved(self):
        p=self.project();config=p.parent/"Config/DefaultGame.ini";config.parent.mkdir()
        original='[/Script/Engine.AssetManagerSettings]\n+PrimaryAssetTypesToScan=(PrimaryAssetType="GameFeatureData",CustomRule=True)\n'
        config.write_text(original,encoding="utf-8")
        target=m.install(self.bundle(),p)
        self.assertEqual(config.read_text(encoding="utf-8"),original)
        self.assertFalse((target/"AllToolsets/Config/Game.ini").exists())
    def test_required_third_party_archives_are_copied(self):
        bundle=self.bundle();lib=bundle/"SemanticSearch/Source/ThirdParty/example.lib"
        lib.parent.mkdir(parents=True);lib.write_bytes(b"synthetic archive fixture")
        data=m.read_json(bundle/m.MARKER);data["files"][lib.relative_to(bundle).as_posix()]=m.digest(lib.read_bytes());m.write_json(bundle/m.MARKER,data)
        target=m.install(bundle,self.project())
        self.assertEqual((target/lib.relative_to(bundle)).read_bytes(),lib.read_bytes())
        m.validate_bundle(target)
    def test_tracked_local_settings_are_not_modified(self):
        p=self.project(True);settings=p.parent/"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini"
        settings.parent.mkdir(parents=True);settings.write_text("[Personal]\nValue=1\n")
        subprocess.run(["git","-C",str(p.parent),"add",str(settings)],check=True,capture_output=True)
        with self.assertRaises(ValueError):m.install(self.bundle(),p)
        self.assertEqual(settings.read_text(),"[Personal]\nValue=1\n")
    def test_install_refuses_existing_plugin(self):
        p=self.project();target=p.parent/"Plugins/Old/ModelContextProtocol.uplugin";target.parent.mkdir(parents=True);target.write_text("{}")
        with self.assertRaises(FileExistsError):m.install(self.bundle(),p)
        self.assertEqual(target.read_text(),"{}")
    def test_failed_install_restores_settings(self):
        p=self.project();settings=p.parent/"Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini"
        settings.parent.mkdir(parents=True);settings.write_bytes(b"[Personal]\r\nValue=1\r\n")
        original=settings.read_bytes();bundle=self.bundle()
        with patch.object(m,"write_json",side_effect=OSError("simulated record failure")):
            with self.assertRaises(OSError):m.install(bundle,p)
        self.assertEqual(settings.read_bytes(),original)
        self.assertFalse((p.parent/"Plugins/UE57MCP").exists())
    def test_incomplete_bundle_rejected(self):
        b=self.bundle();data=m.read_json(b/m.MARKER);data["assets_ready"]=False;m.write_json(b/m.MARKER,data)
        with self.assertRaises(ValueError):m.install(b,self.project())
    def test_modified_bundle_rejected(self):
        b=self.bundle();(b/"payload.txt").write_text("changed")
        with self.assertRaises(ValueError):m.validate_bundle(b)
    def test_usage_hook_walks_upward(self):
        spec=importlib.util.spec_from_file_location("hook",ROOT/"hooks/unreal-context.py")
        hook=importlib.util.module_from_spec(spec);spec.loader.exec_module(hook)
        p=self.project();child=p.parent/"Source/Nested";child.mkdir(parents=True)
        self.assertIn("Sample.uproject",hook.context(child));self.assertIsNone(hook.context(self.source))

if __name__=="__main__":unittest.main()
