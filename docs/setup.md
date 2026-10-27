# Setup

## Requirements

- Windows x64 and Unreal Engine **5.7.4**, including its bundled Python runtime.
- Git for Windows, signed in to an account with accepted EpicGames organization access. Open `https://github.com/EpicGames/UnrealEngine` while signed in to check access. A public GitHub account alone is insufficient.
- Visual Studio 2022 with **Game development with C++**, a UE 5.7-compatible MSVC toolchain, and Windows SDK. The first installation builds native editor modules, even for Blueprint-only target projects.
- Internet access for the first fetch; subsequent runs reuse verified source and dependency caches.

UE 5.8 does not need to be installed or built. No Python package installation is required.

## Installation

Extract this repository and run `Install.cmd`. Choose your `.uproject`; the Launcher engine path is detected from the registry. For explicit options:

```powershell
.\Install.ps1 -Project "C:\Projects\MyGame\MyGame.uproject" -Engine57 "C:\Engines\UE_5.7" -WorkDir "C:\UE57MCPBuild" -Port 8000
```

Keep the build-cache path short to avoid Windows compiler path limits. The default is `%LOCALAPPDATA%/UE57MCP/5.7.4`. Close the target editor before installation. The installer creates its own temporary C++ host project; your project can remain Blueprint-only.

Plugins are installed in `Plugins/UE57MCP`. Local startup/port settings go into `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini`. The `.uproject` is not rewritten. Existing tracked local settings are protected. When the project uses Git, `.git/info/exclude` excludes the installed plugins and generated Saved data without changing the shared `.gitignore`.

## Verify

Open the project in UE 5.7.4, then run:

```powershell
python scripts/verify.py --url http://127.0.0.1:8000/mcp
```

Expected result: `verified`, **55 toolsets / 858 tools**. This check compares every tool name. It does not execute all tools or require a Semantic Search model service.

## Upgrading from the reduced v2 implementation

Close the editor. Move the old `Plugins/UE57MCP` and, if installed, `Plugins/UE57MCPNative` outside the project's `Plugins` folder as a backup. Then install this version. Do not run two MCP servers on port 8000. The old `ue57.*` tool names are replaced by the full backport's tool names; refresh the client's tool discovery and use the updated skill.

For an existing full backport, keep using it or back it up outside `Plugins` before installing. The installer deliberately refuses to merge or overwrite plugin installations.

## Troubleshooting

- **Repository not found / authentication failed:** verify Epic organization access and Git Credential Manager sign-in. The installer does not bypass source access restrictions.
- **Compiler not found:** install the Visual Studio C++ workload and Windows SDK; then rerun with the same cache.
- **Unexpected source hash or revision:** use a fresh build-cache directory. Do not disable integrity checks or substitute a different engine revision.
- **Editor reports incompatible modules:** confirm the target uses the same UE 5.7.4 installation used for the build. Other patch versions and custom engine build IDs are unverified.
- **Port unavailable / incorrect tool catalog:** stop the old server or choose another port. Refresh the MCP client's cached schemas.
- **Semantic Search reports missing endpoint:** configure model endpoints as described in [Semantic Search](semantic-search.md).
