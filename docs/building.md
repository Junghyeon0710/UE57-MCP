# Build the optional native source plugin

The Python MCP server runs when the repository folder is installed at `YourProject/Plugins/UE57MCP`. The optional `UE57MCPNative` plugin provides original C++ code for APIs not exposed to Python: Blueprint graphs, compile diagnostics and Widget Blueprint trees.

## C++ project

Install the main plugin and copy its `Optional/UE57MCPNative` folder to `YourProject/Plugins/UE57MCPNative`. Close the editor and build its Editor target using the **same UE 5.7 installation** you will run:

```powershell
& 'C:/Epic/UE_5.7/Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.exe' `
  MyGameEditor Win64 Development `
  '-Project=C:/Projects/MyGame/MyGame.uproject' `
  -NoHotReloadFromIDE
```

Use the real Editor target name if it differs from `MyGameEditor`. Visual Studio C++ tools and a compatible Windows SDK are required.

## Blueprint-only project

Build the native plugin using the engine's standard BuildPlugin command, then copy the produced plugin directory into the project alongside `UE57MCP`:

```powershell
& 'C:/Epic/UE_5.7/Engine/Build/BatchFiles/RunUAT.bat' BuildPlugin `
  '-Plugin=C:/Dev/UE57-MCP/Optional/UE57MCPNative/UE57MCPNative.uplugin' `
  '-Package=C:/UE57MCPNativeBuild' `
  -TargetPlatforms=Win64
```

Use a fresh, short output directory. This requires the C++ build tools but does not require UE 5.8. Binaries built for another engine BuildId may not load; rebuild against the installed engine rather than editing `.modules` files.

The repository ships original source. Build outputs, PDBs, Unreal intermediate directories and engine files are excluded from public Git.
