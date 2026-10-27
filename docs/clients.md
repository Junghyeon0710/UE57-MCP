# Clients and agent skills

Install the editor plugins using `Install.cmd` first, then open the UE 5.7.4 project. The agent-side Claude plugin/skill does not itself install engine plugins.

MCP endpoint: `http://127.0.0.1:8000/mcp`. Use the port chosen during installation if different.

## Claude Code

```text
claude mcp add --transport http unreal-mcp-57 http://127.0.0.1:8000/mcp
```

The repository also contains `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.mcp.json`, hooks, and `skills/ue57-mcp`. Add the repository through your client's local/plugin marketplace workflow to load that guidance. Do not register duplicate servers for the same endpoint.

## Codex

```text
codex mcp add unreal-mcp-57 --url http://127.0.0.1:8000/mcp
```

Copy `skills/ue57-mcp` into your agent's skill directory when you want the matching workflow guidance. The MCP server remains the editor plugin installation; skills explain how to use it.

## Tool discovery

1. Call `list_toolsets`.
2. Call `describe_toolset` with `toolset_name` for the relevant group.
3. Call `call_tool` with `toolset_name`, `tool_name`, and `arguments` matching that schema.

Use the original backport names, such as `UMGToolSet.UMGToolSet`, `SemanticSearchToolset.SemanticSearchToolset`, and `ToolsetRegistry.AgentSkillToolset`. Do not use the superseded reduced server's `ue57.*` names or `$ref` object encoding. Many official tool arguments use `{"refPath":"/Game/Example.Example"}`; follow each actual schema.

Use `ToolsetRegistry.AgentSkillToolset` to discover/read installed engine skills, including the converted PCG skills. Refresh cached schemas after replacing the old v2 server.
