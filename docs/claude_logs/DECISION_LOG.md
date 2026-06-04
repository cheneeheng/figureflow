# Decision Log

### Entry 001

**Type:** Decision
**Mode:** Autonomous
**Timestamp:** 2026-06-04T00:00:00Z
**Task:** Implement the pyxyflow SKELETON (docs/planning/SKELETON.md).

**Context:** The plan's module tree lists `src/pyxyflow/static/widget.js` as a
"PREBUILT bundle (esbuild output; checked in / built in CI)". Producing it
requires `npm install && npm run build`, which is (a) a build step gated by the
coding contract unless explicitly requested, and (b) dependent on network access
that is not guaranteed in this environment.

**Decision:** Scaffold all front-end source (`js/index.js`) and the maintainer
build config (`package.json`) but do NOT run the esbuild bundle. Treat
`widget.js` as the CI/maintainer-built artifact the plan describes: git-ignore it
and force-include it into the wheel via hatchling `artifacts`. The Python unit
surface (Shape/Node/Edge/Flow, `to_dict`, `positions`) is fully functional
without the bundle; rendering requires running `npm run build` first, which is
documented in the README.

**Impact / Risk:** A fresh checkout cannot render the widget until `npm run
build` is run. This matches the plan's documented maintainer flow
("npm install && npm run build, then pip install -e ."). No functional risk to
the Python API.

**Outcome:** Skeleton sources committed; bundle left to the maintainer/CI build.
