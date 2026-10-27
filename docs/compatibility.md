# Compatibility

Target: **UE 5.7.4, Windows x64 Editor**. Source baseline: UE 5.8.4. Other OSes, engine patch versions, custom engine build IDs, and packaged game runtimes are not verified.

The installed output contains 33 plugin descriptors and exposes 55 toolsets / 858 registered tools. UMG, Semantic Search, animation, PCG, Niagara, Dataflow, Cloth, MVVM and the editor toolsets are included. This restores the existing full port; it is not the reduced v2 Python API wrapper.

Known limits inherited from the full port:

| Area | Boundary |
| --- | --- |
| Animation | UE 5.8 Animation Mixer layers/transitions do not exist in UE 5.7. Supported sequencer/control-rig operations remain available. |
| Cloth / Dataflow | Some UE 5.8-only node types and fields have no UE 5.7 equivalent. The converted legacy clothing template uses 31 nodes / 36 connections and bypasses the new StripUserAttributes node. |
| HTTP | UE 5.7 HTTPServer does not support the port's SSE progress streaming. Ordinary MCP requests remain supported. |
| Semantic Search | The real ported plugin is included. Model endpoints must be configured; models, hosted inference, and API subscriptions are not supplied. |
| MetaHuman | Full generation requires optional MetaHuman Creator Core Data installed for the target engine. |
| Validation | Catalog equality proves registration and schema availability, not successful execution of every tool with every argument. |

Source and converted asset hashes reproduce the existing validated full port. Fresh installation/build/runtime checks are recorded in [verification.json](verification.json). Earlier tool-specific UMG, MVVM/PCG, animation and Cloth checks are historical evidence and are not represented as a new exhaustive 858-tool test run.
