# Client setup

Install the editor plugins using [README](../README.md), then open your project in UE 5.7. The default endpoint is `http://127.0.0.1:8000/mcp`. The installer sets local auto-start preferences.

## Claude Code

```text
/plugin marketplace add Junghyeon0710/UE57-MCP
/plugin install ue57-mcp@ue57-mcp
```

The Claude plugin supplies the `unreal-mcp-57` connection on port 8000. Check `/mcp`. Installing the usage skill and hook does not install the editor plugins or launch Unreal.

For manual MCP configuration:

```json
{
  "mcpServers": {
    "unreal-mcp-57": {"type": "http", "url": "http://127.0.0.1:8000/mcp"}
  }
}
```

The Python 3.10+ SessionStart hook finds an enclosing `.uproject` and provides a short context note. Check hook execution and MCP connectivity separately.

## Codex

```powershell
codex mcp add unreal-mcp-57 --url http://127.0.0.1:8000/mcp
codex mcp list
```

Alternatively, add this to your local `~/.codex/config.toml`:

```toml
[mcp_servers.unreal-mcp-57]
url = "http://127.0.0.1:8000/mcp"
```

See [OpenAI's MCP documentation](https://developers.openai.com/codex/mcp). For usage guidance, copy `skills/ue57-mcp` into your personal Codex skills directory. The project installer does not overwrite personal Codex settings.

## Other ports

Use `install-release --port 8001` or `install-prebuilt --port 8001`, and update the client URL. In the editor console, `ModelContextProtocol.StartServer 8001` starts that port; stop an existing server first if needed. A custom port needs manual Claude configuration instead of the default `.mcp.json`.

```powershell
python scripts/ue57_mcp.py verify --url http://127.0.0.1:8001/mcp
```

Discover `list_toolsets`, inspect `describe_toolset`, then use `call_tool` with the live schema. Serialize dependent changes. A successful client connection is not proof that every editor operation will succeed.
