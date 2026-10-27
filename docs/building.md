# Building and releasing

This workflow is for package authors. Recipients use [the prebuilt installation](../README.md#install-for-ue-57) and need only UE 5.7.4.

## Build from licensed local sources

Install Git, Python 3.10+, UE 5.7.4 and UE 5.8.4 with Engine Source/editor binaries, and the Visual Studio C++ toolchain/Windows SDK required by UE 5.7. Use a short work path on Windows.

```powershell
python scripts/ue57_mcp.py bootstrap `
  --engine57 'C:/Epic/UE_5.7' `
  --engine58 'C:/Epic/UE_5.8' `
  --work-dir 'C:/UE57MCPBuild'
```

Bootstrap fetches the pinned public PortKit dependency, checks 927 source references, assembles 982 files, builds an isolated C++ editor host and regenerates eight PCG Skill assets and one Cloth template. It does not modify either engine installation. Source versions and hashes must match.

After an interrupted build, `resume` accepts the same engine paths and work directory. After failed asset generation, fix the cause and use a fresh work directory. Existing outputs are not deleted or overwritten automatically. [Recipe format](recipe-format.md)

## Package plugins only

```powershell
python scripts/ue57_mcp.py pack-prebuilt `
  --bundle 'C:/UE57MCPBuild/host57/Plugins/UE57MCP' `
  --engine57 'C:/Epic/UE_5.7' `
  --output 'C:/UE57Packages/UE57-MCP-5.7.4-Win64-v1.2.0.zip'
```

Packaging validates source hashes, asset readiness, all module BuildIds and referenced DLLs. It includes source ThirdParty LIB files and the license notices. Intermediate/Saved directories, PDBs and generated link libraries are excluded. The JSON manifest records every file hash. Existing archives are not overwritten.

## Protected publication

1. Use a private fork of `EpicGames/UnrealEngine` inside Epic's GitHub network. Confirm the repository is private and its API `source.full_name` is `EpicGames/UnrealEngine`. Obtain account-owner authorization before creating a new fork.
2. Create a draft plugin release with the intended tag. No local engine clone is needed.
3. Upload only the reviewed plugin ZIP and its SHA256 text. Preserve all engine and ThirdParty notices.
4. Publish the protected release, download the asset as a licensed recipient, compare the SHA256, and install it into a fresh UE 5.7 project.
5. Confirm auto-start, MCP handshake and tool schemas. Update `releases/ue5.7.4-win64.json` with the exact repository, tag, asset, SHA256, byte count and `published` status only after successful verification.
6. Update README/publication status and verification records, then run public CI checks and publish only the installer/documentation changes to the public repository.

Do not attach engine-derived payloads to the independent public repository or CI. The GitHub network access controls must remain in place. [Licensing](licensing.md)

## Local development install

```powershell
python scripts/ue57_mcp.py install --bundle 'C:/UE57MCPBuild/host57/Plugins/UE57MCP' --project 'C:/Projects/MyGame/MyGame.uproject'
python scripts/ue57_mcp.py build --engine57 'C:/Epic/UE_5.7' --project 'C:/Projects/MyGame/MyGame.uproject'
```

Blueprint-only projects use the host-built binaries. For a custom C++ editor target, pass `build --target YourTarget`. To uninstall, close the editor, remove only the installed `Plugins/UE57MCP` directory, and restore the relevant local Saved preferences using `Saved/UE57MCP/installation-backup.json`. Preserve unrelated settings.
