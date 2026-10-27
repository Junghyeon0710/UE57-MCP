# Setup and troubleshooting

Put the downloaded repository folder at `YourProject/Plugins/UE57MCP`, with `UE57MCP.uplugin` directly inside it. Open the project in UE 5.7. For optional native graph/widget tools, separately copy `Optional/UE57MCPNative` to `YourProject/Plugins/UE57MCPNative` and build it with the same engine. The main plugin runs without that build.

## Startup

Unreal loads `Content/Python/init_unreal.py` through the built-in Python Script Plugin. It starts the original server and registers a Slate post-tick callback. HTTP requests enqueue Unreal operations; engine calls execute on the editor main thread.

Look for `UE57-MCP 2.0.0` in Output Log. The message includes the endpoint and tool counts. The server binds only to IPv4 loopback and validates Host/Origin. It executes editor-privileged code, so use it with a trusted local client.

## Change the port

`Saved/UE57MCP/server.json` is local project configuration:

```json
{"port": 8001, "auto_start": true}
```

Stop a running instance from Unreal's Python console before restarting it:

```python
import ue57_mcp
ue57_mcp.stop()
ue57_mcp.start(8001)
```

Do not run another MCP server on the same port. Update the client URL too. An occupied port produces an Output Log warning rather than overwriting another server.

## Native tools

If `ue57.editor.status` reports `native_bridge: false`, Blueprint graph and Widget Blueprint tree operations need the `UE57MCPNative` source plugin and a matching engine build. Compile it with the same UE 5.7 installation used to open the project. [Build instructions](building.md)

Core Blueprint compilation submits the engine's Python compile request; the native bridge additionally returns compiler diagnostics and error counts. A submitted request alone is not proof of a successful compilation.

## Local Git exclusions

To keep the source plugins personal to a game checkout, add project-relative patterns to that checkout's `.git/info/exclude`:

```gitignore
/Plugins/UE57MCP/
/Optional/UE57MCPNative/
```

Adjust the prefix if the game is inside a larger Git repository. Keep `Saved` and local credentials excluded using the project's normal Unreal ignore rules. Copying these plugins does not edit the project's `.uproject`, make Git commits or push game files.

## Connection failures

Confirm the editor is open, Python startup succeeded and the port is available. Check `ue57_mcp.start()`'s result and Output Log. A stale MCP session requires reinitialization. If a call times out, inspect the editor and ongoing compilation before repeating a mutation. Timed-out queued work is canceled; an operation that had already started may still complete.
