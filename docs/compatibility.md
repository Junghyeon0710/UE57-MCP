# Compatibility and limits

This version is an original implementation against UE 5.7's public APIs, with source included. It replaces the earlier source-assembly/ZIP distribution approach. **It is not Epic's official MCP implementation and does not preserve the historical 55-toolset / 858-tool interface.**

Verified engine: **UE 5.7.4 Win64 Editor**. The Python startup accepts UE 5.7 versions, but other 5.7 patch releases and platforms have not been validated. Native binaries must be built against the recipient's installed engine.

## Capability boundaries

- Actor, asset, property and material tools use UE 5.7 Python APIs.
- Native Blueprint tools support graph inspection, reflected function-call nodes, named pin defaults/connections and compile diagnostics. They are not a complete Blueprint graph-authoring framework.
- Native widget tools support Blueprint creation and tree editing. They do not automatically migrate every animation, binding or MVVM reference when restructuring a widget.
- Domain groups discover and invoke loaded editor APIs. They do not implement absent APIs, load every optional engine plugin or recreate UE 5.8-only features.
- PCG, Niagara, Control Rig, Dataflow, Cloth, MVVM, StateTree, GAS and MetaHuman availability depends on enabled engine components. Full MetaHuman workflows may also need Creator Core Data.
- Material recompile reports request submission, not a full shader diagnostics result.
- Semantic Search indexes **names, paths and class metadata**, optionally described by a text model. There is no thumbnail captioning pipeline or custom Content Browser UI.
- Transport returns JSON responses. SSE progress/event streaming is not implemented.
- Editor build and mutation checks do not establish packaged-game, PIE gameplay, visual design or every engine API combination.

Use `ue57.editor.status` to check the engine and native bridge, and discover actual types/methods before calling an optional domain. Missing APIs return errors rather than fabricated success results.
