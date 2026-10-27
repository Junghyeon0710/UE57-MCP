# Licensing and distribution

This public repository distributes original installation code, compatibility recipes, agent guidance, and notices. It does not contain Epic engine implementation files, complete engine assets, or compiled engine plugin binaries. The installer obtains the required originals directly from Epic using the installing user's authorized GitHub access.

The original code in this repository is Apache-2.0 unless a file states otherwise. That license does not relicense Epic's source, converted assets, generated plugins, or external PortKit components. Original notices are retained in downloaded and assembled files.

The Unreal Engine EULA governs the fetched Epic source and generated plugin bundle. Section 5(a)(i) addresses distribution of Engine Code and public Engine Tools distribution. A public GitHub repository containing installation instructions does not grant permission to upload the resulting engine-derived plugins to that repository. See the [Unreal Engine EULA](https://www.unrealengine.com/eula/unreal).

The asset compatibility recipe contains references to exact licensed source bytes and generated 5.7 serialization changes. Source hashes are mandatory; the recipe is not a standalone asset download. The source-code recipe likewise requires the original licensed source files before assembly.

FAISS and OpenBLAS retain the notices in `LICENSES/FAISS-v1.13.2.license` and `LICENSES/OpenBLAS-v0.3.31.license`. External PortKit components retain their source notices. Epic's separately published Claude skills example is MIT-licensed; its license does not apply to the engine's MCP implementation.

Keep downloaded sources, assembled plugins, binaries, and converted assets local. The installer adds local project exclusions where Git is available. This workflow does not create or publish an UnrealEngine fork.
