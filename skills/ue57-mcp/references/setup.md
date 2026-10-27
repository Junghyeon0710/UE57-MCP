# Setup

The repository includes actual plugin source. Put the downloaded repository folder at `YourProject/Plugins/UE57MCP`, with `UE57MCP.uplugin` directly inside it. For native graph and widget editing, separately copy `Optional/UE57MCPNative` to `YourProject/Plugins/UE57MCPNative` and build it with that project's UE 5.7 installation. Core Python tools do not require a C++ build or a separate Python installation. No UE 5.8, gated download or binary ZIP is needed.

Open the editor and look for `UE57-MCP 2.0.0` in Output Log. The default URL is `http://127.0.0.1:8000/mcp`. Set `Saved/UE57MCP/server.json` to change the port. Use manual client configuration for a custom port; the Claude plugin supplies port 8000 by default.

[Repository setup](https://github.com/Junghyeon0710/UE57-MCP/blob/main/docs/setup.md) and [client setup](https://github.com/Junghyeon0710/UE57-MCP/blob/main/docs/clients.md).
