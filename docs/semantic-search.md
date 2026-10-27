# Semantic Search

The full backport includes Epic's Semantic Search core, FAISS/OpenBLAS, asset processing, index storage, HTTP model connections, and `SemanticSearchToolset.SemanticSearchToolset` (`Search` and `FindSimilar`). It also provides **Tools → Semantic Search** in the UE 5.7 editor.

The plugin is installed with the other toolsets. Model inference is a separate requirement: no hosted server, model weights, or API subscription are included.

1. Open **Editor Preferences → Plugins → Semantic Search**.
2. Set **Indexed Paths** to a small content folder for the first index.
3. Configure **Captioning Base URL** and **Captioning Model** for an OpenAI-compatible endpoint that accepts images and structured JSON responses. The plugin appends `/chat/completions` to the base URL.
4. Configure **Embedding Base URL**, **Embedding Model**, and **Embedding Dimension** to match your embedding endpoint. The plugin appends `/embeddings` and sends the `dimensions` parameter.
5. Enter API keys locally if required. The captioning and embedding models may use different providers or local servers.
6. Run `SemanticSearch.IndexAll` in the editor console, then inspect `SemanticSearch.IndexStats`. Indexing sends the selected assets' thumbnails/metadata and generated descriptions to the endpoints you configure.
7. Call `Search` or `FindSimilar`, using the running tool schema. Rebuild the index after changing embedding models or dimensions.

Search combines semantic embedding similarity with BM25 keyword matching. An unset endpoint produces a configuration error; this does not indicate that the toolset was omitted. Provider compatibility and natural-language result quality depend on the chosen models. Earlier integration tests used deterministic local HTTP fixtures, not a quality benchmark of a real model.
