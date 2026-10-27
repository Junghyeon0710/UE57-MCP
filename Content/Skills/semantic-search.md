# Configure metadata semantic search

This implementation indexes asset names, paths and class metadata. It does not analyze thumbnails or reproduce Epic's image-caption pipeline.

Configure `ue57.semantic_search` with an OpenAI-compatible embedding base URL and model. Use zero dimensions to let the model choose its default, or the model's supported dimension. Captioning is optional and describes supplied metadata as text. Model servers and weights are not included.

API keys are read from the editor process environment: `UE57_MCP_EMBEDDING_KEY` and `UE57_MCP_CAPTION_KEY`. Configure them locally before launching the editor; do not commit them or send them in chat.

Index a small content root first. `index_assets` and `search` return a job ID; inspect `get_job` until it completes or fails. Requests run outside the editor main thread. A completed indexing job records the model and dimensions. Reindex after changing models. `find_similar` uses a stored vector and does not request a model.

Indexing sends the selected metadata to your configured endpoint. Preserve an existing index if a job fails; investigate its error before retrying a large request.
