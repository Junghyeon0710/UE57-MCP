# Licensing and distribution boundaries

| Part | License and distribution |
|---|---|
| Original installer, downloader, recipes, compatibility changes and documentation | Apache-2.0 |
| Guidance adapted from Epic's public Claude Code example | MIT; retained in `LICENSES/Epic-skills-MIT.txt` |
| Engine-derived MCP/toolset source, binaries and assets | Unreal Engine EULA and applicable ThirdParty terms; protected distribution through Epic's UnrealEngine GitHub network |

Users supply their own UE 5.7.4 installation. The plugin package contains no engine installation or editor executable. Recipients do not need UE 5.8 installed.

## Separate plugin payload

[Epic's Unreal Engine EULA](https://www.unrealengine.com/eula/unreal), sections 5(a) and 6(d), governs Engine Code and Engine Tools distribution, including modified source and object code. This backport includes Epic engine plugin code. A plugin-only package retains those terms and cannot be relicensed under this repository's Apache-2.0 license.

The selected path is a private fork within Epic's GitHub UnrealEngine network. Its access controls are retained. The downloader verifies that the repository is private, is a fork and has `EpicGames/UnrealEngine` as its network source. Recipients must hold the applicable Epic license and repository access. The installer does not clone or download the engine.

This public repository contains installation code, metadata, recipes, asset regeneration scripts, guidance and tests. It contains no engine source files, compiled editor tools or UAssets. Its public-tree check rejects those files and ZIP archives.

## Third-party notices

- FAISS v1.13.2: MIT. The engine-supplied text is retained in `LICENSES/FAISS-v1.13.2.license`.
- OpenBLAS v0.3.31: BSD-3-Clause. Its supplied text is retained in `LICENSES/OpenBLAS-v0.3.31.license`.
- BlueprintEditorBridge and MaterialGraphDSLBridge retain individual MIT notices inside their plugin directories.
- Assembly uses [UE57-MCP-PortKit](https://github.com/MC-Oruc/UE57-MCP-PortKit) at the revision in `NOTICE`. Its original compatibility code is Apache-2.0; upstream engine code referenced by its patches retains Epic's terms.
- Existing engine dependencies retain the licenses supplied with the recipient's engine. No model server or model weights are included.

`pack-prebuilt` adds this repository's LICENSE, NOTICE and all `LICENSES` texts to the package. Source copyright notices are preserved.

## Local source assembly

Package authors need licensed UE 5.7.4 and UE 5.8.4 for source assembly. Recipes record source paths, SHA256 values, line ranges and original compatibility changes. They read the author's local files; they are not encoded engine source. Engine files and binary payloads stay outside the public repository's commits, releases and CI.
