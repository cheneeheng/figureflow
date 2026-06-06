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

### Entry 004

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-05T00:00:00Z
**Task:** Create v1.0.0 changelog, tag, and GitHub release.

**Context:** No prior git tags or CHANGELOG existed; pyproject.toml declared version 0.1.0 while the request targets a v1.0.0 release.
**Decision:** (1) Authored CHANGELOG.md in Keep a Changelog format with a single [1.0.0] entry documenting the full MVP surface, since this is the first release. (2) Bumped pyproject.toml version 0.1.0 -> 1.0.0 and the dev-status classifier Beta -> Production/Stable so the published package matches the release tag. Left README/CLAUDE.md "v0.1" narrative untouched as out of scope (flagged to user).
**Impact / Risk:** Version metadata now reflects 1.0.0. Tag and release are outward-facing and were explicitly requested. README/CLAUDE.md status text is now stale.
**Outcome:** Changelog, tag v1.0.0, and release created.

### Entry 005

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-05T00:00:00Z
**Task:** Implement SKELETON_V2 (the v2 multi-transport seam) on branch feat/transport-seam-skeleton-v2.

**Context:** The request was "implement-from-plan skeleton v2." A SKELETON artifact can be read as either (a) the scaffold-plus-honest-gates target the skeleton itself describes, or (b) the full v2 including its three iterations (ITER_V2_01–03). The scope delta is large: (a) is a Python module tree with NotImplementedError gates; (b) additionally fills the sync-core, all three adapters, the JS Transport rewire, and a widget.js rebuild.
**Decision:** Implemented (a) — the SKELETON_V2 scaffold. The implement-from-plan skill resolves a SKELETON to scaffold + stubbed entry points, and SKELETON_V2 §04 explicitly specifies the target skeleton state: `display()` works the v1 way (returns self), and `to_html()/serve()/stop()` are present but raise `NotImplementedError` naming their filling iteration. Created `synccore.py` (gated `diff`/`is_echo` + shared `LOCK`) and the `transport/` package (`base.Transport` ABC fully defined since it *is* the seam; `AnywidgetAdapter`/`StaticExportAdapter`/`ServerAdapter` as honestly-gated stubs). The concrete adapters and JS work belong to the iterations.
**Impact / Risk:** No behavior change to the shipped v1 surface; new methods are additive. User-facing docs (README, docs/guide, examples) were deliberately NOT updated for the gated methods — documenting NotImplementedError stubs as features would mislead; docs travel with each iteration when the methods become functional. No new dependency; transport/ and synccore.py are auto-included by hatchling's src-layout packaging (no pyproject change needed).
**Outcome:** Scaffold in place; tests added asserting the gates and the ABC contract. Tests not run (not requested).

### Entry 006

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-06T00:00:00Z
**Task:** Implement the v2 iter plans (ITER_V2_01–03) on branch feat/v2-transport-adapters — fill the seam scaffolded in Entry 004.

**Context:** Three forks the plans left unresolved. (1) Server concurrency: SKELETON_V2/ITER_V2_03 mandate one `threading.Lock` around mutate-then-snapshot, but the trait observer that broadcasts SSE fires *synchronously inside* the lock-held mutation, so a non-reentrant `Lock` re-acquired by the observer would deadlock. (2) `flow.layout()` over `serve()`: v1 runs dagre client-side via the `_layout_request` trait; the server has no trait sync to the browser, and ITER_V2_03 §05 lists only state/echo handling, not how Python-side layout reaches the browser. (3) Version: SKELETON_V2 frontmatter says "Publishable as v0.2," but the repo shipped v1.0.0 (Entry 004 predates that tag's framing).

**Decision:** (1) The broadcast observer does NOT acquire `synccore.LOCK`; `handle_change` holds the lock around a `hold_trait_notifications()` batch (so observers see the final state once, no intermediate push) and reuses `synccore.is_echo` against `_last_from_client` to drop the origin client's own edit. The lock still serializes concurrent POSTs (its stated job); observer reads are atomic list rebinds. (2) The server adapter observes `_layout_request` and forwards it as an SSE `{kind:"event", name:"layout"}` message; the browser's existing `onEvent("layout")` runs dagre and POSTs the arranged nodes back — matching notebook semantics with no server-specific layout logic. (3) Did NOT bump the version or tag a release — releasing is a separate, explicitly-requested action; the request was "implement the plans."

**Impact / Risk:** (1) Reentrancy-safe and race-safe for the single-user localhost MVP; a pathological case where Python sets state exactly equal to the last client edit would be suppressed (acceptable at this scale, documented in code). (2) Adds a typed SSE message envelope (`kind: "state" | "event"`) the server JS adapter fans out; static/anywidget adapters are unaffected. (3) `pyproject.toml` stays at 1.0.0 — a follow-up `release` (minor bump to 1.1.0, additive `display/to_html/serve/stop`) is left to the user.

**Outcome:** All three adapters implemented (Python + JS), bundle rebuilt, 68 tests pass (incl. live serve()/POST/SSE/echo round-trips). Docs (README, guide, reference, examples, CLAUDE.md) updated since the methods are now functional.

### Entry 007

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-06T00:00:00Z
**Task:** Review the codebase against the v2 iter plans (ITER_V2_01–03) and fix gaps/deviations/errors.

**Context:** The audit found the v2 sections (§03/§04/§05 across the three iters) fully implemented and tested. One latent behavior surfaced that is *not* a v2 finding: the renderer's `skipHistoryRef` (carried in unchanged from v1 ITER_03) is set true on undo/redo restore but consumed by the next `commitSeam`, so the first genuine edit after an undo can skip its history push (lose one undo level). ITER_V2_01's mandate is "behaves identically to v1," and v1's plans (SKELETON.md/ITER_01–06) are outside "all v2 iter plans."

**Decision:** Did NOT modify `skipHistoryRef` logic. It is pre-existing v1 behavior, preserved byte-for-byte by the seam refactor exactly as ITER_V2_01 requires; touching it would be an out-of-scope v1 change. Flagged to the user instead.

**Impact / Risk:** None to v2 compliance. The flagged quirk, if confirmed a bug, belongs to a v1-scoped fix; left for the user to decide.
