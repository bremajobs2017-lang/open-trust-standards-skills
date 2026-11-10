# QA evidence matrix

Date: 2026-11-10 (Asia/Calcutta). Branch: `feat/v0.2-qa-hardening`, based on updated main `0409ec6`. This work makes no release, certification, or independent semantic-verification claim. PASS means only the named check completed in the recorded environment.

## Independent v0.1.0 source-ZIP evidence supplied by the owner

The independent environment's OS, Python version, dependency versions and exact run timestamp were not supplied. Evidence received on 2026-11-10; this is not an invented execution date or a rerun here.

| Command/check | Observed outcome | Untested scope |
| --- | --- | --- |
| Count `SKILL.md` | 20 found | Actual host discovery/activation NOT VERIFIED |
| `python -m pytest -q` | 144 passed | Bounded helper tests, not human compliance assessment |
| `PYTHONPATH=src python -m trust_skills validate --root .` | 20 skills, 16 sources structurally checked | Live URLs and semantic content NOT VERIFIED |
| CLI `--help` and `list` | Worked | Clean sdist/wheel installation NOT VERIFIED in that run |
| Ruff lint/format and `python -m build` | **NOT VERIFIED**: tools absent | Prior maintainer successes do not fill independent gaps |

## Current maintainer workspace

Windows, Python 3.14.3, PyYAML 6.0.3, pytest 9.2.0, Ruff 0.17.4, build 1.6.1, setuptools 84.2.1. Commands below use the `.venv` interpreter explicitly because the host's `python` alias is unreliable. Results are local maintainer evidence, not independent QA. Temporary-directory access is approved for pytest/build/venv steps that the sandbox otherwise blocks.

| Date | Exact command/check | Observed outcome | Untested scope |
| --- | --- | --- | --- |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --tb=short` | PASS: 206 passed, including all original 144 tests | No actual Codex host, browser, API or real-model test |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m ruff check src tests scripts` | PASS | Does not assess domain correctness |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m ruff format --check src tests scripts` | PASS: 24 Python files | Formatting only |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m trust_skills validate --root .` | PASS: 20 skills, 16 registry entries | Source-only structural checks |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m trust_skills registry --registry standards/registry.yaml` | PASS: structural-only; network_requested=false, semantic_status=not-assessed | No network or semantic assessment |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m build --no-isolation` | PASS: 0.2.0.dev0 sdist and wheel built | Does not install artifacts |
| 2026-11-10 | `.\.venv\Scripts\python.exe -m pip download --only-binary=:all: --dest tmp/qa-wheelhouse -r requirements/smoke.txt` | PASS: PyYAML/setuptools wheels prepared for this Python/platform | Not other ABIs or dependency security |
| 2026-11-10 | `.\.venv\Scripts\python.exe scripts/install_smoke.py --wheelhouse tmp/qa-wheelhouse` | PASS: separate fresh sdist/wheel venvs, pip check, import isolation, help/list, three examples in two formats, source-required refusal and explicit-source validation | No host skill installation/activation |

No failed product test was waived. Initial sandbox temporary-directory failures were rerun with approved access. Dependency wheel download initially failed under sandbox network restrictions and succeeded with approved network access. Smoke summaries record artifact SHA-256 values under ignored `tmp/install-smoke-*/result.json`; CI logs and local QA observations are distinct. New fixtures were separately authored from scenario rationale, but independent human sign-off remains NOT VERIFIED.

## Still NOT VERIFIED

- Hosted GitHub Actions outcomes for this branch; configured matrices are not run evidence.
- Python 3.12/3.13 and Linux in this local workspace.
- Actual Codex discovery, explicit/implicit activation, nonactivation, and adversarial instruction resistance; use [the manual plan](codex-integration-test-plan.md).
- Live retrieval of all 16 registry sources/supporting URLs in this QA run. The network option is not enabled automatically; mock HTTP tests are not source retrievals.
- Independent semantic review of standards content/mappings, independent human curation sign-off on the new fixtures, rendered accessibility, full format schema validation, vulnerability-feed assessments, real-model evaluations, or control effectiveness.

The wheel intentionally contains only CLI code. Source validation needs a checkout/extracted sdist. The clean-install script verifies that limitation rather than concealing it. See [QA policy](qa-policy.md), [fixture provenance](fixtures.md), and [registry verification](registry-verification.md).
