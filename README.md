# UE57-MCP

An MCP plugin, editor toolsets and agent skills for **Unreal Engine 5.7**. The actual source is included in this repository: copy the plugins into your project and use your existing engine. **No UE 5.8 installation, separate plugin download, or Epic GitHub fork is required.**

This is an independently written implementation using UE 5.7's public editor APIs. It does not redistribute Epic's UE 5.8 MCP source. The old engine-backport installer has been replaced; its historical 858-tool count does not describe this implementation.

## Included

| Folder | Purpose | Build requirement |
|---|---|---|
| `UE57MCP.uplugin`, `Content/Python` | Ready-to-load MCP plugin, toolsets and bundled skills | Uses Unreal's included Python runtime; no C++ build |
| `Optional/UE57MCPNative` | Optional Blueprint graph/compile diagnostics and Widget Blueprint tree bridge | Build against your own UE 5.7 engine |
| `skills/ue57-mcp` | Matching English AI-agent instructions | None |
| `.claude-plugin`, `hooks`, `.mcp.json` | Claude Code package and default connection | The optional hook uses Python on PATH |

The current catalog contains **39 toolset groups and 141 entries**. This includes 29 domain groups that discover and invoke the API types actually loaded in your editor. It is not a claim of 141 equivalents of Epic's UE 5.8 tools. [Toolsets and scope](docs/toolsets.md)

## Install

1. [Download this repository](https://github.com/Junghyeon0710/UE57-MCP/archive/refs/heads/main.zip), or clone it with Git.
2. Close Unreal Editor. Put the extracted repository folder at **`YourProject/Plugins/UE57MCP`**. `UE57MCP.uplugin` must be directly inside that folder.
3. Open the project in **UE 5.7**. MCP starts automatically at **`http://127.0.0.1:8000/mcp`**.
4. Connect your MCP client. [Client setup](docs/clients.md)

The result should look like this:

```text
YourProject/
  YourProject.uproject
  Plugins/
    UE57MCP/
      UE57MCP.uplugin
      Content/
        Python/
        Skills/
```

Or clone straight into the project's plugin directory:

```powershell
git clone https://github.com/Junghyeon0710/UE57-MCP.git 'C:/Projects/MyGame/Plugins/UE57MCP'
```

**The MCP server needs no C++ build, UE 5.8, separate download, external Python installation or pip packages.** It uses the Python runtime and editor scripting plugins included with UE 5.7.

### Optional native tools

For Blueprint graph and Widget Blueprint tree editing, copy `Optional/UE57MCPNative` to **`YourProject/Plugins/UE57MCPNative`** and build it using UE 5.7. This optional plugin needs Visual Studio C++ tools and the Windows SDK. It is not built or loaded merely because it is inside the main plugin's `Optional` folder. [Build instructions](docs/building.md)

Tested with **UE 5.7.4 Win64 Editor**. Other 5.7 patch versions and platforms are not yet verified.

## Connect

The server exposes `list_toolsets`, `describe_toolset` and `call_tool`. Discover the live schema before using a tool. The default endpoint is:

```text
http://127.0.0.1:8000/mcp
```

Claude Code can install the matching client skill and configuration after the editor plugin is installed:

```text
/plugin marketplace add Junghyeon0710/UE57-MCP
/plugin install ue57-mcp@ue57-mcp
```

Codex and manual configuration: [Clients](docs/clients.md).

An optional connection check, using any Python 3.10+ available on PATH:

```powershell
python scripts/verify.py
```

## Configuration

Create `YourProject/Saved/UE57MCP/server.json` to change the port or disable auto-start:

```json
{"port": 8001, "auto_start": true}
```

Restart the editor and update your client URL. From Unreal's Python console, `import ue57_mcp; ue57_mcp.stop()` stops the server and `ue57_mcp.start(8001)` starts it on a chosen port. Keep personal settings and model keys outside Git. [Setup and troubleshooting](docs/setup.md)

## Capabilities

High-level tools cover actors, assets, object properties, Blueprints, Widget Blueprints and materials. Domain tools expose discovery and invocation for animation, Sequencer, Control Rig, Niagara, PCG, Dataflow, Cloth, MVVM, AI, GAS, Game Features, MetaHuman, meshes, textures, tables, physics, input, audio and other loaded UE 5.7 APIs.

Domain availability depends on the engine plugins enabled in the project. API discovery does not recreate features absent from UE 5.7. [Compatibility](docs/compatibility.md)

Semantic Search is an original **asset-metadata search** implementation using user-supplied OpenAI-compatible model endpoints. It does not bundle models or analyze thumbnails. Indexing and queries run asynchronously. [Model setup](docs/semantic-search.md)

## Verification and development

- UE 5.7.4 native module build: passed.
- Independent editor checks: **34 core checks plus 8 widget/search/skill checks passed**.
- Semantic HTTP/index/query checks use fixed test responses; real model search quality is not verified.
- Source-only automated tests cover MCP sessions, discovery, tool errors, thread dispatch, serialization and search consistency.

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_tree.py
```

See [verification.json](docs/verification.json) for the exact scope. Public CI does not download or compile Unreal Engine. This is editor tooling; packaged-game behavior and every available API combination are outside the verified scope.

## License

Original plugin/server/toolset source and documentation: **Apache-2.0**. Unreal Engine remains separately licensed by Epic and is supplied by the user. No Epic engine source, engine binaries or UE 5.8 assets are bundled. See [Licensing](docs/licensing.md) and `NOTICE`.
