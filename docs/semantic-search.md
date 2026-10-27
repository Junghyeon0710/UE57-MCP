# Semantic metadata search

The original search toolset indexes asset names, paths and class metadata using an OpenAI-compatible embedding endpoint. It optionally asks a text model to describe that metadata. It does not inspect thumbnails and includes no model server or weights.

## Configure

Use `ue57.semantic_search.configure` with:

```json
{
  "embedding_url": "http://127.0.0.1:1234/v1",
  "embedding_model": "your-embedding-model",
  "dimensions": 0,
  "caption_url": "",
  "caption_model": ""
}
```

The URLs are API base URLs; the plugin appends `/embeddings` or `/chat/completions`. Zero dimensions uses the embedding model's default. Supply a positive dimension only if supported by the model. Optional captioning accepts text metadata, not images.

For authenticated services, set `UE57_MCP_EMBEDDING_KEY` and/or `UE57_MCP_CAPTION_KEY` in the editor process's local environment before launch. Never commit keys or paste them into chat. Settings and index files live in `Saved/UE57MCP`.

## Index and search

1. Start with a small folder using `index_assets(root='/Game/YourFolder', max_assets=100)`.
2. Poll `get_job(job_id=...)` until the job completes or fails.
3. Call `search(query='wooden furniture', top_k=10)` and inspect its job result.
4. Use `find_similar` on a stored asset vector when no new model request is needed.

Model requests run outside the editor main thread. Only one semantic job runs at a time. A failed index build preserves the prior index. Changing the model/base URL requires reindexing; vector dimensions must match. Indexing sends selected metadata to the configured service.

Fixed-response HTTP tests verify the pipeline and ranking mechanics. They do not prove natural-language search quality for a real model.
