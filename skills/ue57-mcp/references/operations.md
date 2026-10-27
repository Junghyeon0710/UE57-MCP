# UE 5.7 operations

The verified configuration registers 55 toolsets / 858 tools. A registration count does not prove every tool/input combination works. Discover the current schema and inspect success/error fields after each call. Serialize dependent changes.

Use `list_toolsets` → `describe_toolset` → `call_tool`. Inspect relevant project Agent Skills through the AgentSkillToolset. Do not assume a tool exists because it appears in UE 5.8 documentation.

Version limits:

- Animation Mixer layers/transitions and some 5.8-only Cloth solver properties are absent.
- `DrawSpline` is interactive; use `CreateSplineFromPoints` for explicit points.
- MetaHuman full character workflows need optional Creator Core Data.
- Semantic Search needs captioning/embedding endpoints. The default configuration is unconfigured; explain its setup error rather than repeatedly retrying it.
- Tool results use JSON responses without SSE progress streaming.
- Use `-RenderOffscreen` for editor mutation tests. Actor creation under `-NullRHI` is explicitly rejected after an engine crash was reproduced in that mode.

See [the detailed compatibility table](https://github.com/Junghyeon0710/UE57-MCP/blob/main/docs/compatibility.md). Build and editor startup are different from PIE, packaged runtime or visual gameplay validation.
