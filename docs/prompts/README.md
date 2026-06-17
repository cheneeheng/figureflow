# figureflow prompt pack

Few-shot examples for an LLM authoring figureflow diagrams. Pair these with
`llms.txt` (the condensed spec) and the JSON Schema shipped at
`figureflow/static/figureflow.schema.json`.

- [`json_examples.md`](json_examples.md) — two JSON-emission examples against the schema.
- [`mermaid_examples.md`](mermaid_examples.md) — two mermaid examples inside the supported subset.
- [`repair_loop.md`](repair_loop.md) — one repair-loop transcript (broken input → error → fix).

Authoring rules the examples demonstrate:

- Emit topology only — **never invent coordinates**. Omit `position`; the
  renderer auto-lays unplaced nodes using `layout_direction`.
- Use only the eight built-in shapes.
- On an error, read every line, fix all of them, and re-emit once.
