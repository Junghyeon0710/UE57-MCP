# Licensing

The source under `Content/Python` and `Optional/UE57MCPNative` is independently written for this project and licensed under **Apache-2.0**. It uses the public API of the recipient's installed Unreal Engine 5.7. This repository does not include Epic engine source, engine binaries, UE 5.8 UAssets or a modified copy of Epic's MCP/toolset plugins.

The server uses Python's standard library and the Python runtime included with Unreal Editor. The optional C++ plugin includes public engine headers during compilation; those headers and engine libraries are supplied by the user's engine installation, not redistributed here. Unreal Engine remains subject to the user's separate Epic license.

Agent instructions and repository packaging originally referenced [Epic's public Claude Code example](https://github.com/EpicGames/unreal-engine-skills-for-claude-code-plugin). Its MIT notice is retained in `LICENSES/Epic-skills-MIT.txt` and `NOTICE`. The current server/toolsets and matching usage instructions are original source.

Earlier repository revisions contained a local assembly recipe for an engine-derived UE 5.8 backport. Those historical records do not change the license of Epic engine code. That installer and the unpublished protected-ZIP download path have been removed from the current source distribution. The current plugin does not fetch or reconstruct that engine code.

No model server, model weights, FAISS/OpenBLAS binaries or third-party editor bridge code are included.
