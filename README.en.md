# UE57-MCP

Local compatibility tooling for **Unreal Engine 5.7.4 / Windows x64 Editor**. The verified configuration registers **55 toolsets and 858 tools**. This is an unofficial backport of UE 5.8.4 tooling.

This public repository contains installer code, compatibility recipes, asset regeneration scripts, a Claude Code usage skill, hooks and verification tools. **Recipients of a complete prebuilt ZIP need only UE 5.7.4.** Building that ZIP initially requires licensed UE 5.7.4 and UE 5.8.4 installations with Engine Source and editor binaries. This independent public repository does not distribute Unreal Engine source, libraries, executables or assets. [Licensing](docs/licensing.md)

## UE 5.7-only installation

Install Windows x64, Git, Python 3.10+ and Epic Launcher UE 5.7.4 with BuildId `47537391`. Obtain the complete ZIP through an authorized distribution channel. **Cloning this public repository does not currently download the ZIP; a public download is not available here.** See [package distribution status](docs/prebuilt.md).

Close the project editor, then run:

```powershell
git clone https://github.com/Junghyeon0710/UE57-MCP.git
cd UE57-MCP
python scripts/ue57_mcp.py install-prebuilt --archive 'C:/Downloads/UE57-MCP-5.7.4-Win64.zip' --engine57 'C:/Epic/UE_5.7' --project 'C:/Projects/MyGame/MyGame.uproject'
```

This path never reads or launches UE 5.8. Plugin binaries and regenerated UE 5.7 assets are included. It validates the engine BuildId, file hashes and module DLLs before installation. Your own C++ game may still require its normal toolchain. Open the project in UE 5.7 and run `python scripts/ue57_mcp.py verify`.

## Build a package from local sources

Install Git, Python 3.10+ and the C++ toolchain/Windows SDK required by UE 5.7. In PowerShell, replace these example paths:

```powershell
git clone https://github.com/Junghyeon0710/UE57-MCP.git
cd UE57-MCP
python scripts/ue57_mcp.py bootstrap --engine57 'C:/Epic/UE_5.7' --engine58 'C:/Epic/UE_5.8' --work-dir 'C:/UE57MCPBuild'
python scripts/ue57_mcp.py install --bundle 'C:/UE57MCPBuild/host57/Plugins/UE57MCP' --project 'C:/Projects/MyGame/MyGame.uproject'
python scripts/ue57_mcp.py build --engine57 'C:/Epic/UE_5.7' --project 'C:/Projects/MyGame/MyGame.uproject'
```

Keep the work path short on Windows. Bootstrap validates the pinned local source hashes, fetches the pinned public PortKit dependency, assembles 982 files, builds an isolated editor target, and regenerates eight PCG Skill assets and one Cloth template in UE 5.7. It does not modify either engine installation. Blueprint-only projects use the host-built plugins and skip the game target build. If the C++ project editor target has a custom name, pass `build --target YourTarget`.

Close the project editor before installation. Existing MCP installations are rejected rather than overwritten. Installation uses `Plugins/UE57MCP`, local Saved configuration, a plugin-local GameFeatureData config layer, and Git's local exclude file. It preserves the tracked project descriptor and DefaultGame.ini. Previous local configuration is backed up under `Saved/UE57MCP`.

Open the project in UE 5.7 and verify:

```powershell
python scripts/ue57_mcp.py verify
```

See [client setup](docs/clients.md), [compatibility](docs/compatibility.md), [verification](docs/verification.json), and the [recipe format](docs/recipe-format.md). After an interrupted build, use `resume` with the same engine paths and work directory. After a failed asset generation, use a fresh work directory.

## Limits

The backport includes animation/Sequencer, Control Rig, Dataflow, Cloth, MVVM/UMG, Niagara system editing, PCG, gameplay and editor tools. It does not provide UE 5.8 Animation Mixer layers/transitions or all UE 5.8 solver properties and engine nodes. MetaHuman requires its optional Creator Core Data for full character workflows. Semantic Search needs captioning/embedding model endpoints and uses a separate search window. SSE progress streaming is unavailable. This is Win64 Editor validation, not exhaustive coverage of every tool/input, packaged games or other platforms.

Installer and original compatibility changes: Apache-2.0. The usage skill adapts Epic's MIT-licensed public Claude plugin. Generated engine code remains under the Unreal Engine EULA and applicable third-party terms. See `NOTICE`.
