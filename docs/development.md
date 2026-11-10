# Development and verification

Python 3.12+ is required. Install with `python -m pip install -e ".[dev]"` in an isolated environment. See [installation](installation.md) for Windows interpreter details.

```sh
python -m ruff check src tests scripts
python -m ruff format --check src tests scripts
trust-skills validate --root .
python -m pytest -q
python -m build
```

For the exact CI tool selection, install `requirements/qa.txt`, then install this repository with `python -m pip install --no-deps --no-build-isolation -e .`. Artifact installation tests are a separate command: `python scripts/install_smoke.py --wheelhouse tmp/qa-wheelhouse`, after building and explicitly preparing the wheelhouse as described in [installation](installation.md). See [QA policy](qa-policy.md) and [the evidence matrix](qa-matrix.md). Do not label tools missing from another QA environment as verified because they ran here.

## Architecture

`src/trust_skills/core.py` owns bounded file reading, structural validators, report envelopes, selected credential redaction, and safe serialization. Domain modules implement offline transformations and bounded heuristics. `engine.py` routes the 20 public names explicitly; it never evaluates code or prompts from an input. `metadata.py` uses safe YAML with duplicate-key rejection and enforces both Agent Skills metadata rules and this repository's stricter content contract. `cli.py` handles local files, exit codes, and exclusive output creation.

`skills/<name>/SKILL.md` provides portable instructions, standard YAML frontmatter, exact input contracts, human review steps, expected example behavior, and official references. Its `examples/input.*` is synthetic and executable through the shared CLI. Documentation remains useful without Python; users must state when automation was not run.

`standards/registry.yaml` records selected editions, authoritative URLs, verification dates/status, and verification scope. Update it from official sources before changing mappings. Living references are observations, not immutable releases. Do not claim the registry establishes that every edition is the newest or that every requirement has been implemented.

## Test expectations

Tests include realistic defects, clean cases, malformed inputs, method provenance, unsupported editions, redaction invariants, safe report rendering, no-overwrite behavior, and deterministic outputs. Every skill fixture has behavioral assertions beyond a metadata check. Add a regression test for a demonstrated defect; avoid tests that merely copy implementation wording.

The CI workflow checks lint, formatting, skill validation, tests, and source/wheel builds on Python 3.12, 3.13, and 3.14 on Windows and Linux. Local results and hosted CI results must be reported separately. Browser, screen reader, live API, real-model, and host-agent behavior are not covered by Python unit tests.

## Review before release

- Independently review standards mappings and evidence semantics with domain specialists.
- Exercise representative human workflows in supported agent hosts and assistive technologies.
- Use full official schemas for any SBOM/OpenAPI conformance claims and a current vulnerability source for dependency vulnerability assessments.
- Inspect output for sensitive information before publication; pattern redaction is incomplete.
- Review dependency provenance, supported Python versions, release support, and action version updates.

Contributions may be AI-assisted; contributors remain responsible for source verification, testing, licensing, and clear disclosure. The initial implementation was prepared with AI assistance and deterministic local tests; it has not received an independent standards-body review.
