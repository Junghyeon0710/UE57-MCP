# UE57-MCP — full UE 5.8 MCP backport

Install the UE 5.8 MCP server and its ported editor toolsets into **Unreal Engine 5.7.4**, without installing UE 5.8. This installs the existing full backport: **33 plugins, 55 registered toolsets, and 858 tools**, including UMG, Semantic Search, animation, PCG, Niagara, Dataflow, Cloth, MVVM, Blueprints, materials, and editor operations.

**First installation requires Windows, UE 5.7.4, Git, an Epic-linked GitHub account with access to `EpicGames/UnrealEngine`, and Visual Studio 2022 C++ build tools with a Windows SDK.** The installer downloads the required official source/dependency files and compiles the plugins locally. This repository is an installation kit, not a precompiled drag-and-drop plugin archive. No UE 5.8 editor installation, engine build, or new UnrealEngine fork is required.

## Install

1. [Link your Epic and GitHub accounts](https://www.unrealengine.com/en-US/ue-on-github), accept the organization invitation, and confirm you can open [EpicGames/UnrealEngine](https://github.com/EpicGames/UnrealEngine). Git must be signed in with that account.
2. Download this repository with **Code → Download ZIP** and extract it, or clone it.
3. Close the target project's Unreal Editor. Double-click **`Install.cmd`**, then choose its `.uproject` file. The installer detects a Launcher UE 5.7 installation. Allow the first source fetch and C++ build to finish.
4. Open the project with UE 5.7.4. Connect your MCP client to **`http://127.0.0.1:8000/mcp`**.

For a custom engine location, run from the extracted repository:

```powershell
.\Install.ps1 -Project "C:\Projects\MyGame\MyGame.uproject" -Engine57 "C:\Engines\UE_5.7"
```

The resulting plugins are installed under `MyGame/Plugins/UE57MCP/`. The installer preserves the `.uproject` and tracked project configuration and adds the generated plugin directory to the project's **local Git exclude** file. It refuses to overwrite an existing MCP installation. See [setup and upgrades](docs/setup.md).

## What you get

- Epic's MCP implementation and the existing complete ported toolset catalog, with the same discovery interface: `list_toolsets`, `describe_toolset`, and `call_tool`.
- The full UMG and Semantic Search plugins, native editor bridges, FAISS/OpenBLAS dependencies, and nine converted PCG/Cloth assets.
- Matching agent guidance in `skills/ue57-mcp`, Claude plugin metadata/hooks, and client setup examples.
- Reproducible, hash-checked source and asset compatibility recipes. Original engine files come directly from Epic using your access; they are not redistributed in this public repository.

See the [55-toolset catalog](docs/toolsets.md) and [all 858 tool names](docs/tool-catalog.json). Run `python scripts/verify.py` while the editor is open to compare every registered tool name with the expected catalog.

## Compatibility

This is an unofficial community backport, not an Epic-supported UE 5.7 release. Registered tool counts do **not** guarantee that every UE 5.8 engine capability is available in UE 5.7. Animation Mixer layers/transitions and some new Cloth fields/nodes are unavailable; SSE progress streaming is not supported by the UE 5.7 HTTP server. Full MetaHuman generation needs the optional Creator Core Data installation.

Semantic Search is included, but searching requires configuring your own embedding and asset-description model endpoints. No model service or API subscription is supplied. See [Semantic Search](docs/semantic-search.md) and [compatibility details](docs/compatibility.md).

The previous `v2` reduced `ue57.*` implementation is superseded by this full backport installer. It is not used by this installation path.

## Documentation

- [Setup and troubleshooting](docs/setup.md)
- [MCP clients and agent skills](docs/clients.md)
- [Build and source provenance](docs/building.md)
- [Licensing and distribution](docs/licensing.md)
- [Verification record](docs/verification.json)

The original installer/compatibility code is Apache-2.0. Downloaded Epic source and generated engine plugins remain governed by the Unreal Engine EULA; third-party components retain their own licenses.
