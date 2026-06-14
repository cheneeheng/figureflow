# Mermaid emission examples

Emit a mermaid flowchart inside the supported subset. figureflow upgrades it to an
interactive canvas. Stay within the grammar in `llms.txt`.

## Example 1 — an approval flow with an edge label

**Prompt:** "Flowchart: submit a request, a reviewer approves or rejects."

```mermaid
flowchart TD
    A([Submit request]) --> B{Reviewer}
    B -->|approve| C[Provision access]
    B -->|reject| D[Send rejection]
    C --> E([Done])
    D --> E
```

## Example 2 — a subgraph (becomes a group) with mixed shapes

**Prompt:** "Show an ETL job: extract from a DB, then a transform stage with two
steps, then load."

```mermaid
flowchart LR
    src[(Source DB)] --> X
    subgraph transform [Transform]
      X[Clean] --> Y[Aggregate]
    end
    Y --> out[(Warehouse)]
```

The `subgraph … end` block imports as a one-level **group**; `X` and `Y` become
its members and drag together on the canvas.
