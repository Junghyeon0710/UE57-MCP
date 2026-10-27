# Setup

Use [the repository installation guide](https://github.com/Junghyeon0710/UE57-MCP). After protected release publication, recipients can use `install-release` with an Epic-linked GitHub account and UE 5.7.4 only. An existing authorized ZIP can be installed offline with `install-prebuilt`. Neither path requires UE 5.8 or plugin compilation. Check the README for the actual publication status. The public skill package does not include that ZIP. Alternatively, package authors can assemble from licensed local UE 5.7.4/5.8.4 installations. Install the complete bundle, then open the target project in UE 5.7.

The default client endpoint is `http://127.0.0.1:8000/mcp`. The repository's Claude plugin supplies a static default `.mcp.json`; use manual configuration for a different port. [Client setup](https://github.com/Junghyeon0710/UE57-MCP/blob/main/docs/clients.md)

The SessionStart hook uses Python, discovers an enclosing `.uproject`, and emits a short context note. A working hook does not establish a working MCP connection. Run `python scripts/ue57_mcp.py verify` from the repository, or make a read-only editor call after inspecting the schema.

Connection failure: verify the project is open, check Output Log for MCP startup, and ensure only one editor owns the configured port. Console commands: `ModelContextProtocol.StartServer 8000` and `ModelContextProtocol.StopServer`. No optional proxy is built or verified by this package.
