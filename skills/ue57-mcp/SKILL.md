---
name: ue57-mcp
description: Use the original UE57-MCP server to inspect and edit a running Unreal Engine 5.7 editor, including actors, assets, Blueprints, widgets, materials and available editor APIs. Use its live tool schemas; this is not Epic's UE 5.8 tool interface.
---

# UE57-MCP

This skill matches the source plugins in Junghyeon0710/UE57-MCP. The server exposes three discovery tools: `list_toolsets`, `describe_toolset`, `call_tool`.

## Workflow

1. List toolsets and describe only the relevant group, using `toolset_name`, for example `ue57.actor`.
2. Call `ue57.editor.status` to inspect the engine and optional native bridge when setup or compatibility matters.
3. Use the discovered function schema. Both short and fully qualified tool names are accepted by `call_tool`.
4. Read result/error fields. Serialize dependent editor changes, compile affected Blueprints and save assets when appropriate to the user's request.

Do not use the historical backport's 858-tool names or assume that a UE 5.8-only API exists. Domain toolsets expose the real API types currently loaded in UE 5.7. Missing types indicate unavailable engine plugins/APIs.

## JSON values

Reuse tool-returned object references: `{"$ref":"/Game/Example.Asset"}`. Classes use `{"$class":"StaticMeshActor"}`. Structs use `{"$struct":"Vector","x":0,"y":0,"z":100}`. Enums use `{"$enum":"CollisionEnabled","value":"QUERY_ONLY"}`. Less common structs may use a returned `$text` representation for lossless engine import/export.

Inspect `ue57.object.list_properties` before editing an unfamiliar object or slot. For generic API invocation, inspect `ue57.unreal_api.describe_type` and supply the actual method's positional `args` and named `kwargs`.

## Bundled workflows

Use `ue57.skills.list_skills` and `read_skill` for editor API, Blueprint, widget, material and semantic-search workflows. Native graph/widget operations require the optional `UE57MCPNative` source plugin built against the installed engine. Core Blueprint compilation alone submits a request; the native bridge additionally returns diagnostics.

Semantic Search uses metadata and user-supplied model endpoints. Index/search are asynchronous jobs; inspect job status and handle errors. No models or thumbnail captioning pipeline are bundled.

Read `references/setup.md` for installation and client setup; read `references/operations.md` when troubleshooting errors or timeouts.
