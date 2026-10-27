# Compatibility

Verified target: **UE 5.7.4 Win64 Editor**. Original source: **UE 5.8.4**. The configuration registers **55 toolsets and 858 tools**; this is not exhaustive validation of every argument combination.

| Area | Included workflows |
|---|---|
| General editor | Actors, assets, Blueprints, materials, data tables, logs, compilation and automation tests |
| Animation | Sequencer, keyframes, binding tags/conditions/easing, Control Rig, FBX and AnimSequence import/export |
| UMG / MVVM | Widget trees, ViewModels, bindings, conversion functions, widget replacement retaining MVVM references |
| Niagara | Information, components and assets, plus 46 system editing tools |
| Dataflow / Cloth | Graphs, pins, variables, templates, compatible assets, clothing binding and Chaos Cloth conversion |
| PCG | Graphs, parameters, execution-result metadata, eight Skill assets and spline tools |
| Gameplay | GAS, Gameplay Tags, StateTree, Physics, Conversation queries and Game Features |
| MetaHuman | Base character assets, editing sessions, body/skin/eye settings |
| Semantic Search | Search, FindSimilar, indexing and a dedicated Tools > Semantic Search window |

## Engine limits

- **Sequencer Animation Mixer layers/transitions:** unavailable because the corresponding UE 5.8 runtime/UAF support is absent in 5.7.
- **Cloth:** UE 5.8-only fields such as `InnerCollisionThickness`, water-related Aerodynamics and `FictitiousForcesModel` are unavailable. The compatible template bypasses `StripUserAttributes`, retaining 31 nodes and 36 links. Physics equivalence with UE 5.8 is not guaranteed.
- **UE 5.8-only engine nodes/assets:** not added automatically. PCG Skill instructions are retained, but references to UE 5.8-only PCGPrimitives need suitable 5.7 nodes/assets.
- **PCG DrawSpline:** an interactive viewport workflow. Use `CreateSplineFromPoints` for explicit coordinates. Interactive drawing is not exhaustively tested.
- **Semantic Search UI:** a separate window selects results and navigates the Content Browser, replacing integration APIs absent in 5.7.
- **SSE:** the backport returns a single JSON result; progress streaming is unavailable.

## Optional components

Full MetaHuman character creation, preview and texture workflows need **MetaHuman Creator Core Data** in the Epic Launcher UE 5.7 installation options. The installer does not download it. Basic settings checks and completed character generation have different validation scopes.

Game Features behavior depends on the project's actual plugins and data. The installer adds an editor-only GameFeatureData AssetManager rule through a local plugin config layer. It does not add gameplay networking, RPC or replication code.

## Semantic Search models

Search uses a model to describe assets and a text embedding model. Endpoints can be local or hosted OpenAI-compatible APIs. These model services are separate from the MCP server.

1. Open **Editor Preferences > Plugins > Semantic Search**.
2. Add a small content folder to Indexed Paths.
3. Set `Captioning Base URL` and `Captioning Model` for a model supporting images and structured JSON responses. Include the API base path, such as `/v1`; the plugin appends `/chat/completions`.
4. Set `Embedding Base URL`, `Embedding Model` and `Embedding Dimension` for your model. The plugin sends `dimensions` to `/embeddings`.
5. If authentication is required, enter the API key in local preferences.
6. Run `SemanticSearch.IndexAll`, then inspect `SemanticSearch.IndexStats` or the indexing window.

Reindex after changing the model or dimensions. Before configuration the tools return guidance errors; automatic indexing is disabled by default. Indexing sends selected asset thumbnails, metadata and descriptions to the configured endpoints. Fixed-response checks verify the request/index/search path, not a real model's language understanding or search quality. No model server or weights are bundled.
