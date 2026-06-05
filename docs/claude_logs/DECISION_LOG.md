# Decision Log

### Entry 004

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-05T00:00:00Z
**Task:** Implement SKELETON_V2 (the v2 multi-transport seam) on branch feat/transport-seam-skeleton-v2.

**Context:** The request was "implement-from-plan skeleton v2." A SKELETON artifact can be read as either (a) the scaffold-plus-honest-gates target the skeleton itself describes, or (b) the full v2 including its three iterations (ITER_V2_01–03). The scope delta is large: (a) is a Python module tree with NotImplementedError gates; (b) additionally fills the sync-core, all three adapters, the JS Transport rewire, and a widget.js rebuild.
**Decision:** Implemented (a) — the SKELETON_V2 scaffold. The implement-from-plan skill resolves a SKELETON to scaffold + stubbed entry points, and SKELETON_V2 §04 explicitly specifies the target skeleton state: `display()` works the v1 way (returns self), and `to_html()/serve()/stop()` are present but raise `NotImplementedError` naming their filling iteration. Created `synccore.py` (gated `diff`/`is_echo` + shared `LOCK`) and the `transport/` package (`base.Transport` ABC fully defined since it *is* the seam; `AnywidgetAdapter`/`StaticExportAdapter`/`ServerAdapter` as honestly-gated stubs). The concrete adapters and JS work belong to the iterations.
**Impact / Risk:** No behavior change to the shipped v1 surface; new methods are additive. User-facing docs (README, docs/guide, examples) were deliberately NOT updated for the gated methods — documenting NotImplementedError stubs as features would mislead; docs travel with each iteration when the methods become functional. No new dependency; transport/ and synccore.py are auto-included by hatchling's src-layout packaging (no pyproject change needed).
**Outcome:** Scaffold in place; tests added asserting the gates and the ABC contract. Tests not run (not requested).

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

### Entry 1

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-05T00:00:00Z
**Task:** Create v1.0.0 changelog, tag, and GitHub release.

**Context:** No prior git tags or CHANGELOG existed; pyproject.toml declared version 0.1.0 while the request targets a v1.0.0 release.
**Decision:** (1) Authored CHANGELOG.md in Keep a Changelog format with a single [1.0.0] entry documenting the full MVP surface, since this is the first release. (2) Bumped pyproject.toml version 0.1.0 -> 1.0.0 and the dev-status classifier Beta -> Production/Stable so the published package matches the release tag. Left README/CLAUDE.md "v0.1" narrative untouched as out of scope (flagged to user).
**Impact / Risk:** Version metadata now reflects 1.0.0. Tag and release are outward-facing and were explicitly requested. README/CLAUDE.md status text is now stale.
**Outcome:** Changelog, tag v1.0.0, and release created.
