# Decision Log

### Entry 001

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-04T00:00:00Z
**Task:** Create "manuals" for figureflow.

**Context:** The user asked to "create manuals." The word "manuals" names a document
*type*, not a location, and the `ceh-documentation:user-operator-guide` skill mandates that
new docs live under `docs/guide/`. I had already written `docs/manual/` into CLAUDE.md and
README before invoking the skill, creating an internal conflict.
**Decision:** Followed the skill's standard and placed the manual under `docs/guide/`,
titling the document a "User Manual" to honor the word "manuals." Reconciled the earlier
`docs/manual/` references in CLAUDE.md and README to `docs/guide/`. Built it as a
single-audience (end-user) guide — figureflow is an in-process library widget with no
operator/infra surface — so the operator-runbook subtree was dropped.
**Impact / Risk:** Low. A reader expecting a literal `docs/manual/` path won't find it, but
README and CLAUDE.md both link to `docs/guide/`.
**Outcome:** 10-file cross-linked manual created under `docs/guide/`; no stale `docs/manual`
references remain.

### Entry 002

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-04T00:00:00Z
**Task:** Create "runnable examples."

**Context:** Four `examples/*.py` already existed but each ended in a bare `flow` expression
that does nothing when run as a script — and the interactive widget only renders inside a
notebook, so "runnable" is ambiguous (CLI script vs. Jupyter notebook).
**Decision:** Restructured each example to build the diagram at module level (notebook- and
import-friendly) *and* print an inspectable text summary under `if __name__ == "__main__"`,
so they run from a terminal. Added `examples/README.md` with run instructions. Chose plain
`.py` (idiomatic for anywidget) over generating `.ipynb` files by hand to avoid malformed
notebook JSON. `custom_component.py` inlines its JS via a `data:` URL so it works in a
notebook with no external file server.
**Impact / Risk:** Low. Scripts can't show the live canvas; this is documented in each file
and in the examples README.
**Outcome:** All four examples run cleanly (`python examples/<name>.py`); verified.

### Entry 003

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-04T00:00:00Z
**Task:** Documentation refresh (scope decision touching code).

**Context:** The task was docs (README, CLAUDE.md, manuals, examples). The module docstring
at the top of `src/figureflow/__init__.py` still read "Skeleton surface … only the
render+sync loop is wired up … Later iterations fill the stubbed methods," directly
contradicting the implemented MVP. The coding contract discourages editing code not in scope.
**Decision:** Treated the stale module docstring as documentation within the task's intent
and refreshed it to describe the implemented surface. Did not touch any executable code.
**Impact / Risk:** Minimal — docstring text only; the 44-test suite still passes.
**Outcome:** Docstring updated; tests green.
