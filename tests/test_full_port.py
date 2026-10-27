"""실제 원본 없이 전체 이식 설치의 무결성 및 의존 파일 검증을 검사한다."""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import full_port
import licensed_sources
import ue57_mcp as api


class FullPortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def asset_fixture(self):
        source = self.root / "source"
        bundle = self.root / "bundle"
        source.mkdir(); bundle.mkdir()
        (source / "asset").write_bytes(b"original content")
        api.write_json(bundle / api.MARKER, {"files": {}, "assets_ready": False})
        spec = {"files": [{"source": "asset", "source_sha256": api.digest(b"original content"),
            "path": "Example/Content/asset.uasset", "size": 11, "sha256": api.digest(b"new content"),
            "operations": [["data", base64.b64encode(b"new").decode()], ["copy", 8, 8]]}]}
        return spec, source, bundle

    def test_asset_conversion_requires_original_and_matches_target(self):
        spec, source, bundle = self.asset_fixture()
        full_port.convert_assets(spec, source, bundle)
        self.assertEqual((bundle / spec["files"][0]["path"]).read_bytes(), b"new content")
        self.assertTrue(api.validate_bundle(bundle)["assets_ready"])

    def test_wrong_asset_original_leaves_bundle_unmodified(self):
        spec, source, bundle = self.asset_fixture()
        (source / "asset").write_bytes(b"wrong")
        with self.assertRaises(ValueError): full_port.convert_assets(spec, source, bundle)
        self.assertFalse(api.read_json(bundle / api.MARKER)["assets_ready"])
        self.assertFalse((bundle / "Example").exists())

    def test_bad_asset_range_rejected(self):
        spec, source, bundle = self.asset_fixture()
        spec["files"][0]["operations"] = [["copy", -1, 10]]
        with self.assertRaises(ValueError): full_port.convert_assets(spec, source, bundle)

    def test_text_hash_allows_only_line_ending_normalization(self):
        (self.root / "source").write_bytes(b"one\r\ntwo\r\n")
        recipe = {"sources": {"a": {"root": "test", "path": "source", "normalized_text": True,
            "sha256": api.digest(b"one\ntwo\n")}}}
        self.assertEqual(api.load_sources(recipe, {"test": self.root})["a"][1], ["one\n", "two\n"])
        (self.root / "source").write_bytes(b"different\n")
        with self.assertRaises(ValueError): api.load_sources(recipe, {"test": self.root})

    def dependency_fixture(self):
        data = b"prefixwantedSuffix"
        packed = gzip.compress(data)
        ph = hashlib.sha1(data).hexdigest()
        fh = hashlib.sha1(b"wanted").hexdigest()
        xml = f'''<DependencyManifest BaseUrl="https://cdn.unrealengine.com/dependencies">
        <Files><File Name="Engine/test" Hash="{fh}" /></Files>
        <Blobs><Blob Hash="{fh}" PackHash="{ph}" PackOffset="6" Size="6" /></Blobs>
        <Packs><Pack Hash="{ph}" RemotePath="UnrealEngine-fixture" Size="{len(data)}" CompressedSize="{len(packed)}" /></Packs>
        </DependencyManifest>'''.encode()
        return xml, packed

    def test_dependency_download_extracts_and_verifies_only_requested_file(self):
        xml, packed = self.dependency_fixture()
        with patch("urllib.request.urlopen", return_value=io.BytesIO(packed)):
            licensed_sources.download_dependencies(self.root, xml, {"Engine/test"})
        self.assertEqual((self.root / "Engine/test").read_bytes(), b"wanted")
        with patch("urllib.request.urlopen", side_effect=AssertionError("Cache should be reused")):
            licensed_sources.download_dependencies(self.root, xml, {"Engine/test"})

    def test_corrupt_pack_rejected_before_writing(self):
        xml, packed = self.dependency_fixture()
        with patch("urllib.request.urlopen", return_value=io.BytesIO(packed[:-1])):
            with self.assertRaises(ValueError): licensed_sources.download_dependencies(self.root, xml, {"Engine/test"})
        self.assertFalse((self.root / "Engine/test").exists())


if __name__ == "__main__": unittest.main()
