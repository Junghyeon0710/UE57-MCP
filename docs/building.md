# Reproducible full backport

`scripts/full_port.py` accepts only the installed UE 5.7 engine path. It does not launch or read a UE 5.8 installation.

1. Sparse-fetch the pinned `EpicGames/UnrealEngine` revision `f45729c0b6f097038e72b52d366a62baeca3275b` (`5.8.4-release`) using the user's existing Git authorization.
2. Verify the official dependency manifest, then download only required dependency pack contents from Epic's CDN. Pack and individual file hashes are checked.
3. Fetch the pinned external PortKit revision `8d5615cbfa0ef4d34245c18edf43a1d5306cc6a0` and verify every referenced file.
4. Assemble **982 source/support files** using `recipes/ue5.7.4-from-5.8.4.json`. Text source hashes normalize CRLF/LF only; output hashes remain exact.
5. Apply `recipes/assets-5.7.4.json` to nine official source assets. The recipe contains source byte-range references and 5.7 serialization changes. It requires the exact licensed source assets and reproduces the previously editor-validated 5.7 assets byte-for-byte. It contains no complete `.uasset` files. No 5.8 editor is needed for conversion.
6. Build all native modules in an isolated UE 5.7.4 C++ host, then install the plugins into the target project.

To build without installing into a project:

```powershell
python scripts/full_port.py --engine57 "C:\Engines\UE_5.7" --work-dir "C:\UE57MCPBuild" --prepare-only
```

The reusable output is `C:/UE57MCPBuild/host57/Plugins/UE57MCP`. It is generated locally and must not be committed to this public repository. UE's own derived-data cache and toolchain caches are also used during compilation.

The recipes reproduce the full existing port, including its known compatibility limitations. They are not a promise of equivalence to every future UE 5.8 release. The installer checks the exact engine patch version and source revision rather than silently applying the recipe to another version.

Run `python -m unittest discover -s tests -v` for installer integrity/rollback tests. Run `python scripts/check_public_tree.py` before publishing. Live validation requires the editor and `python scripts/verify.py`.
