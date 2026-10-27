# Local assembly recipe

`recipes/ue5.7.4-from-5.8.4.json` records engine versions, the pinned PortKit revision, source-relative paths and SHA256 values, and the construction/hash of every output.

- `sources`: paths inside the `ue57`, `ue58` or `portkit` roots; SHA256 covers original bytes.
- `source` output: uses a local file. Text is normalized to UTF-8 without BOM and LF; binary bytes are retained.
- `pieces`: `copy` references a zero-based, half-open line range; `text` contains original compatibility changes.
- `view: patch-additions`: references additions in the pinned external PortKit patch, excluding `+++` headers and removing the `+` prefix. The patch is not copied into this repository.
- Output `sha256`: covers the assembled bytes. A mismatch discards staging rather than installing it.

For example, `['copy', 's0001', 10, 20]` reads original lines 11 through 20. The reference does not reconstruct the source without the licensed original.

## Assets

The workflow regenerates UE 5.7 assets instead of copying UE 5.8 UAssets:

1. An isolated UE 5.8 data project exports PCG Skill instructions and Cloth node/pin/variable/property data to local JSON.
2. The assembled UE 5.7 tooling is built.
3. An isolated UE 5.7 project recreates and saves the Skill assets and Cloth graph, then checks counts.
4. `.ue57-mcp-bundle.json` records asset hashes and readiness. Incomplete bundles are rejected.

Engine source modifications, other patch releases and manual edits fail source/output hash checks. Extending support requires a separate build and editor verification, followed by updated recipe and verification records. Recipients of the prebuilt ZIP do not run this workflow.
