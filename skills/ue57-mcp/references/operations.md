# Operations

Discover current tool schemas and inspect returned errors. The catalog has high-level editing tools plus domain API access; it does not preserve Epic's 5.8 tool interface.

- Start/stop from Unreal's Python console with `import ue57_mcp; ue57_mcp.start(8000)` and `ue57_mcp.stop()`.
- Check `ue57.editor.status` for the current engine and native bridge.
- A native bridge requirement error means graph/widget source has not been built or loaded. Core tools remain available.
- Before retrying a timed-out mutation, inspect the editor state. Queued work can be canceled, but work that had already started may finish.
- Domain APIs depend on engine plugins enabled in the project. Use live type/method discovery instead of guessing names.
- Native Blueprint compile results include diagnostics; material compilation reports request submission. Inspect the editor log for shader failures.
- Semantic Search jobs need configured model endpoints and consistent dimensions. A failed job does not justify an automatic large retry.

[Compatibility](https://github.com/Junghyeon0710/UE57-MCP/blob/main/docs/compatibility.md). Engine/editor tests do not establish gameplay or packaged-runtime behavior.
