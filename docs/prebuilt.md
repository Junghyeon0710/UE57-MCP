# Prebuilt plugin distribution

The ZIP contains **project plugins only**: MCP, toolsets, their Win64 DLLs, required ThirdParty libraries, eight PCG Skill assets and one UE 5.7 Cloth template. There is no engine installation or editor executable. Use your own Epic Launcher UE 5.7.4, BuildId `47537391`. Recipients do not need UE 5.8 or plugin compilation.

## Publication status

The prepared v1.2.0 package is 32,342,721 bytes and contains 1,066 payload files. Its SHA256 and version metadata are in [the release descriptor](../releases/ue5.7.4-win64.json).

**The package is not yet published.** The private distribution fork has not been created and no protected release is enabled. The ZIP, installer and English documentation are prepared. `install-release` refuses unpublished descriptors before authentication, download or project changes.

The prepared downloader is configured for `Junghyeon0710/UE57-MCP-Engine`, a **private fork of EpicGames/UnrealEngine**, with release tag `ue57-mcp-v1.2.0`. This is not an active download link yet. The descriptor will change to `published` only after the protected release is uploaded and a real download is verified.

[Epic's EULA sections 5(a) and 6(d)](https://www.unrealengine.com/eula/unreal) specify permitted Engine Tools distribution channels. This path retains Epic's network and access controls. The installer downloads only the plugin ZIP, never the engine repository. This public repository does not host the engine-derived ZIP.

## Recipient access

1. Link Epic and GitHub using [Epic's official instructions](https://www.unrealengine.com/ue-on-github), and accept the organization invitation if required.
2. Confirm that your account can open [EpicGames/UnrealEngine](https://github.com/EpicGames/UnrealEngine). A 404 can indicate missing access.
3. Authenticate locally with `gh auth login`, Git Credential Manager, or a suitable local token. Public-repository-only credentials are insufficient.
4. After publication, run [the install-release command](../README.md#install-for-ue-57).

Credentials remain in memory and are not forwarded to the release-file host. Access errors stop installation. Repository access is required; a UE 5.8 installation is unnecessary.

## Offline installation

Use `install-prebuilt` with an authorized ZIP as shown in the README. Compare the checksum with the public descriptor:

```powershell
Get-FileHash 'C:/Downloads/UE57-MCP-5.7.4-Win64-v1.2.0.zip' -Algorithm SHA256
```

Every payload file and module BuildId is checked. An engine mismatch stops installation. Do not edit `.modules` files to bypass it; use a matching build. [Build instructions](building.md)

## Redistribution

The ZIP retains engine copyright notices, bridge licenses, Apache-2.0 LICENSE/NOTICE and FAISS/OpenBLAS license texts. Open-source notices do not relicense Epic's engine code. Further distribution must follow the applicable terms. [Licensing](licensing.md)
