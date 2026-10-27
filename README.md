# UE57-MCP

Use MCP and editor toolsets in **Unreal Engine 5.7.4 on Windows x64**. The verified configuration registers **55 toolsets and 858 tools**. This is an unofficial backport of Epic's UE 5.8.4 tooling.

**Bring your own UE 5.7.4 installation.** The payload contains only project plugins: MCP, toolsets, their binaries and UE 5.7 assets. It contains no engine installation or editor executable. Recipients do not need to install or run UE 5.8 or compile the plugins.

> **Release status:** the complete ZIP and installer are prepared and locally tested. No protected download release has been published. `install-release` currently stops before downloading or changing a project. The public repository alone is not yet a complete downloadable installation. [Publication status](docs/prebuilt.md)

[Clients](docs/clients.md) | [Compatibility](docs/compatibility.md) | [Verification](docs/verification.json) | [Licensing](docs/licensing.md)

## Requirements

- Windows x64 and **Epic Launcher UE 5.7.4, BuildId `47537391`**.
- Git and Python 3.10 or newer.
- An Epic-linked GitHub account with access to [EpicGames/UnrealEngine](https://github.com/EpicGames/UnrealEngine), for the protected plugin download. [Connect your accounts](https://www.unrealengine.com/ue-on-github).
- GitHub authentication through Git Credential Manager, `gh auth login`, or a locally configured `GH_TOKEN` / `GITHUB_TOKEN`. Never put tokens in project files or chat.

Other 5.7 patch releases and custom source builds need a matching plugin build. Your own C++ game may still need its normal compiler and SDK; the plugins do not replace the game's build tools.

## Install for UE 5.7

Close the target project's editor. Once the release status above is published, run this in PowerShell with your own paths:

```powershell
git clone https://github.com/Junghyeon0710/UE57-MCP.git
cd UE57-MCP
python scripts/ue57_mcp.py install-release `
  --engine57 'C:/Epic/UE_5.7' `
  --project 'C:/Projects/MyGame/MyGame.uproject'
```

The installer checks your engine, authenticates to the private distribution fork, verifies its membership in Epic's UnrealEngine network, and downloads **only the pinned plugin ZIP**. It checks the ZIP's SHA256, size, every packaged file and all module BuildIds before installation. It never clones the engine repository or reads a UE 5.8 installation. Authentication stays in memory and is not forwarded to the release-file host.

Installation uses `Plugins/UE57MCP`. Plugins enable themselves locally. The installer preserves `.uproject` and `Config/DefaultGame.ini`. MCP auto-start settings go into `Saved/Config/WindowsEditor`; the GameFeatureData rule goes into the local plugin's config layer. Existing project rules are retained. Local settings are backed up under `Saved/UE57MCP`. Existing MCP installations are rejected instead of overwritten.

For Git projects, the installer adds the plugins and generated Saved state to `.git/info/exclude`. It makes no commits or pushes and refuses to modify local configuration that Git already tracks.

Open the project in UE 5.7 and verify:

```powershell
python scripts/ue57_mcp.py verify
```

The default endpoint is `http://127.0.0.1:8000/mcp`. Use `install-release --port 8001` for another port and set the same URL in your client. See [client setup](docs/clients.md).

### Install an existing ZIP offline

If you already have the complete ZIP from an authorized distribution channel, installation itself needs no GitHub connection:

```powershell
python scripts/ue57_mcp.py install-prebuilt `
  --archive 'C:/Downloads/UE57-MCP-5.7.4-Win64-v1.2.0.zip' `
  --engine57 'C:/Epic/UE_5.7' `
  --project 'C:/Projects/MyGame/MyGame.uproject'
```

Check the checksum against [the pinned descriptor](releases/ue5.7.4-win64.json). Internal hashes detect corruption; obtain the ZIP from a trusted publisher.

## Claude Code and Codex

After installing the editor plugins, Claude Code can install this repository's usage skill, hook and default MCP connection:

```text
/plugin marketplace add Junghyeon0710/UE57-MCP
/plugin install ue57-mcp@ue57-mcp
```

The Claude plugin installs client guidance and configuration. Use `install-release` or `install-prebuilt` for the editor plugins. The SessionStart hook uses Python and does not need Git Bash. Codex setup and manual configurations are in [Clients](docs/clients.md).

## Toolsets and limits

The package includes Actor, Asset, Blueprint, Material, UMG, MVVM, Niagara, Animation, Sequencer, Control Rig, PCG, Dataflow, Cloth, GAS, Gameplay Tags, StateTree, Physics, Conversation, Game Features, MetaHuman settings, Semantic Search and Slate automation tools.

- UE 5.8 Animation Mixer layers/transitions and some UE 5.8-only Cloth fields and engine nodes are unavailable in UE 5.7.
- Full MetaHuman workflows need the optional UE 5.7 **MetaHuman Creator Core Data** component.
- **Semantic Search requires your own captioning and embedding model endpoints.** No model server or model weights are included.
- MCP returns a single JSON response; SSE progress streaming is unavailable.
- Verification covers the Win64 editor, not every input combination, packaged games or other platforms.

Read [Compatibility](docs/compatibility.md) for precise scope and Semantic Search setup.

## Build and contribute

Recipients use the prebuilt plugins. Package authors can follow [Building and releasing](docs/building.md); original source assembly requires licensed UE 5.7.4 and UE 5.8.4 installations.

```powershell
python -m unittest discover -s tests -v
python scripts/check_public_tree.py
```

Public CI runs engine-free installer tests on Windows and Linux. The engine build and editor checks in [verification.json](docs/verification.json) are separate local tests.

## License and attribution

Original installer code, compatibility changes and documentation: Apache-2.0. The usage skill adapts [Epic's MIT-licensed Claude Code example](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin), retaining its notice in `LICENSES`.

The engine-derived payload remains under the **Unreal Engine EULA**, not Apache-2.0 or MIT. Its selected distribution path is Epic's UnrealEngine GitHub network. This public repository contains the installer and metadata. FAISS, OpenBLAS and bridge plugin notices are retained in the package. See [Licensing](docs/licensing.md) and `NOTICE`.
