---
name: ue57-mcp
description: Use the full UE 5.8 MCP backport in a running Unreal Engine 5.7 editor for assets, Blueprints, UMG, materials, animation, PCG, Niagara, Dataflow and other registered editor toolsets. Discover the live Epic tool schemas before making calls.
---

# UE 5.7 full MCP backport

This skill matches the full backport installed by Junghyeon0710/UE57-MCP: 55 toolsets and 858 registered tools on UE 5.7.4. The earlier reduced `ue57.*` server is superseded.

## Workflow

1. Call `list_toolsets`, then `describe_toolset` only for the relevant groups using `toolset_name`.
2. Call `call_tool` with `toolset_name`, `tool_name`, and `arguments` from the schema. Preserve returned object references; many schemas use `{"refPath":"/Game/Example.Example"}`. Do not translate them into the old server's `$ref` format.
3. Inspect errors and returned compile diagnostics. Serialize dependent editor changes and save affected assets when appropriate to the user's request.
4. For built-in procedural workflow guidance, discover the tools in `ToolsetRegistry.AgentSkillToolset` and read the relevant installed skill. Do not load every skill or tool schema for a focused task.

UMG operations use `UMGToolSet.UMGToolSet`. Semantic Search uses `SemanticSearchToolset.SemanticSearchToolset`; it requires configured model endpoints and an index. A registered schema is not proof that the external model service is configured.

UE 5.8 Animation Mixer layers/transitions and some new Cloth nodes/fields are unavailable in UE 5.7. Do not claim all arguments or every 5.8 engine capability work merely because 858 tools are registered. SSE progress streaming is unavailable. Full MetaHuman generation requires optional Creator Core Data.

Read [setup](references/setup.md) for connection problems and [operations](references/operations.md) for compatibility/error handling.
