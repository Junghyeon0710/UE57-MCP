---
name: ue57-mcp
description: "Operate a running Unreal Engine 5.7 editor through UE57-MCP. Use for live scene, asset, Blueprint, widget, material, Niagara, PCG, Dataflow, Control Rig, Sequencer and editor test actions. Excludes conceptual documentation and other engines."
---

# UE 5.7 MCP

This skill targets the UE57-MCP compatibility package for Unreal Engine 5.7.4.

You are wired into a live Unreal Editor through the `unreal-mcp-57` MCP server. The server exposes hundreds of tools across 30+ toolsets (actors, blueprints, materials, Niagara, Sequencer, Control Rigs, GAS, automation tests, Live Coding, and more) registered through Unreal's `ToolsetRegistry`. Use it to inspect and mutate live editor state instead of telling the user to do it manually.

You don't need to memorize tool names. The flow below has you discover them on demand.

Use the `unreal-mcp-57` connection configured by this package. The optional UE 5.8 proxy is not built or verified here.

## First step every time: discover the tool you need, then dispatch it via `call_tool`

Tool search is on by default, so the MCP server advertises only three meta-tools for the whole session: `list_toolsets`, `describe_toolset`, and `call_tool`. Tool names like `BlueprintTools.create` or `SequencerTools.create_level_sequence` are **not in `tools/list`**. They are dispatched server-side through `call_tool` and never registered as native MCP tools. This is deliberate. It keeps your context window small and the prompt cache warm.

When you start work:

1. Call `list_toolsets` to see what's registered, then `describe_toolset` on the candidate(s) to read their tool schemas. If you already know which toolset you need (the user said "make a Blueprint" → the Blueprint toolset), skip the listing and go straight to `describe_toolset` to confirm the available tools and their signatures.
2. Invoke the tool with `call_tool`: pass `toolset_name`, `tool_name`, and an `arguments` object matching the schema you just read. The result comes back on the same turn. No extra round-trip needed.
3. Top-level dispatch (omitting `toolset_name`) is reserved for tools registered directly on the MCP server and is rejected for `call_tool` itself.

Missing tools do not prove that the editor is stopped. Check the configured `unreal-mcp-57` connection and the editor Output Log. Verify recovery with a read-only tool call. See `references/setup.md` for setup and `references/operations.md` for limits.

## Safety rules

Follow these rules to protect live editor state.

- **Save first, then save again.** Tell the user to save the project (or call `AssetTools` save APIs) before any bulk change, and again after. MCP edits are not always undoable, especially across compilation boundaries. Treat anything that touches multiple assets as a destructive operation that needs a recovery point.
- **Wait for compilation.** If C++ or shader compilation is in flight, your tool calls will hang or fail in confusing ways. To rebuild C++ from the running editor, drive `LiveCodingToolset.CompileLiveCoding` and wait on its result instead of asking the user to switch to the IDE. That tool blocks until the compile actually finishes and surfaces MSVC diagnostics.
- **Control concurrent calls.** MCP accepts concurrent requests and handles dispatch synchronization. Asynchronous tools can overlap, and request order does not guarantee execution or completion order. Serialize dependent calls and mutations that can affect the same asset or editor state. Use parallel calls only for independent work when the tools support safe overlap. Multiple agents can use one editor, but their conflicting changes can cause adverse effects.
- **Always check the result.** Blueprint compilation, widget creation, material edits: many tools return a status that flips between success and failure with no exception thrown on the wire. Read the response before moving on. Treat anything that isn't an explicit success as a stop.
- **Mind PIE.** Editor-only tools (asset creation in particular) behave differently while Play-in-Editor is active. If a result looks wrong, check whether PIE is running and stop it if so.

## Project skills

A project or plugin can register **Agent Skills**: named bundles of instructions that capture workflow knowledge the agent wouldn't otherwise have (a project's naming conventions, folder layout, required setup steps, or the canonical sequence for a multi-step task). These are separate from the toolsets themselves and are reached through the agent skill toolset (`AgentSkillToolset`), not through `list_toolsets`.

Check for them the same way you discover tools, and do it whenever you start unfamiliar work in a project rather than just once:

1. Call `AgentSkillToolset.ListSkills` (through `call_tool`) to see what skills the project registers. Each entry carries a short description of what it covers and when it applies.
2. If a skill's description looks relevant to what the user asked, call `AgentSkillToolset.GetSkills` on it to load the full instructions, then follow them.
3. If nothing matches, fall back to the tool-discovery flow above.

A relevant project skill's instructions take precedence over your generic defaults: it exists precisely because the project's way of doing something differs from the obvious one.

## Reference files

- `references/setup.md`: first-time MCP server setup, client configuration, and optional proxy installation.
- `references/operations.md`: console commands, settings, proxy recovery, and troubleshooting for missing tools or failed calls.


## UE 5.7 compatibility

Read `references/setup.md` for installation and `references/operations.md` for the verified limits. The runtime is a locally assembled backport. Check the live schema before using a 5.8 API. Animation Mixer layers/transitions and UE 5.8-only solver fields are unavailable; Semantic Search needs model endpoints.
