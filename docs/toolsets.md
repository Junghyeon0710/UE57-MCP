# Toolsets

The current registry has **39 groups / 141 entries**. Twenty-nine groups provide three shared API discovery/invocation tools each. Those are domain views of the actual loaded UE 5.7 Python API, not new implementations of each engine feature.

## High-level groups

| Group | Operations |
|---|---|
| `ue57.editor` | Status, main-thread Python execution, console commands and viewport camera |
| `ue57.unreal_api` | Type discovery, method documentation and public API invocation |
| `ue57.object` | Property discovery, reads, transactional writes and object methods |
| `ue57.actor` | Listing, selection, spawning, duplication, deletion and transforms |
| `ue57.asset` | Search, loading, creation, saving, duplication, renaming, deletion and metadata |
| `ue57.blueprint` | Actor Blueprint creation, compilation, graph inspection, function nodes, pin defaults and connections |
| `ue57.widget` | Widget Blueprint creation, tree inspection, child creation, movement and deletion |
| `ue57.material` | Material/expression creation, connections, material outputs and recompile requests |
| `ue57.skills` | Discover/read the five bundled workflow instructions |
| `ue57.semantic_search` | Model configuration, metadata indexing, asynchronous search, similarity and index management |

Blueprint graph and widget tree operations require `UE57MCPNative`. Property editing and API invocation use tagged JSON values. [API workflow](../Content/Skills/editor-api.md)

## Domain API groups

Each provides `list_types`, `describe_type` and `invoke`:

`animation`, `sequencer`, `control_rig`, `niagara`, `pcg`, `dataflow`, `cloth`, `mvvm`, `behavior_tree`, `state_tree`, `gameplay_abilities`, `gameplay_tags`, `game_features`, `conversation`, `data_registry`, `metahuman`, `physics`, `mesh`, `texture`, `tables`, `landscape`, `camera`, `level`, `input`, `audio`, `slate`, `automation`, `plugins`, `settings`.

For example, discover loaded Niagara types with `ue57.niagara.list_types`, inspect a type's actual methods, then invoke the documented API with positional `args` and named `kwargs`. An empty type list means no matching types are currently loaded. Enable the relevant engine plugin when the project needs it.

## MCP discovery

1. `list_toolsets` with `{}`.
2. `describe_toolset` with `{"toolset_name":"ue57.actor"}`.
3. `call_tool` with the discovered function and arguments.

Example:

```json
{
  "toolset_name": "ue57.actor",
  "tool_name": "spawn_actor",
  "arguments": {
    "actor_class": {"$class": "StaticMeshActor"},
    "location": {"$struct": "Vector", "x": 0, "y": 0, "z": 100},
    "label": "MCP_Test"
  }
}
```

Reuse returned `$ref` values in later calls. Do not assume an Epic UE 5.8 tool name or argument schema exists here.
