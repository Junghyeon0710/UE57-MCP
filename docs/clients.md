# Client setup

Copy the editor plugin source as described in [README](../README.md), then open the project in UE 5.7. The original server starts automatically at `http://127.0.0.1:8000/mcp`.

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

See [OpenAI's MCP documentation](https://developers.openai.com/codex/mcp). For usage guidance, copy `skills/ue57-mcp` into your personal Codex skills directory. The editor plugin does not modify personal Codex settings.

## Other ports

Set `Saved/UE57MCP/server.json` to `{"port":8001,"auto_start":true}` and restart the editor. Update the client URL too. For an immediate restart, use Unreal's Python console: `import ue57_mcp; ue57_mcp.stop(); ue57_mcp.start(8001)`.

```powershell
python scripts/verify.py --url http://127.0.0.1:8001/mcp
```

The core server uses three meta-tools: `list_toolsets`, `describe_toolset`, `call_tool`. Use the live schema, and reuse returned object references. The original implementation has `ue57.*` toolsets, not the historical Epic backport's names.
