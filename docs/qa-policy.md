# QA, dependency, and CI policy

## Evidence labels

Use **PASS**, **FAIL**, or **NOT VERIFIED** with date, command, environment, scope, and evidence. Keep independent ZIP QA, maintainer workspace checks, clean-artifact installation tests, hosted CI, live URL retrieval, and manual host observations separate. Tool availability alone is not a passing check. Never infer semantic standards validation, conformance, certification, or endorsement from code tests or metadata.

## Dependencies and actions

The public package keeps bounded dependency ranges in `pyproject.toml`; development CI uses exact versions in `requirements/qa.txt` and `requirements/smoke.txt`. These pins make the tested selection explicit; they do not prove absence of vulnerabilities or cover every version allowed by public ranges. The environment's bundled pip, Python installations, runner images, and downloaded wheels remain separate supply-chain assumptions. Wheels are not hash-locked in this initial policy; artifact SHA-256 values in smoke evidence identify builds but do not authenticate dependencies.

Review pin updates in a pull request: verify official project/release provenance, Python/platform support, available advisories, dependency changes, and test/build/install results. Do not run automatic unreviewed upgrades or treat an advisory search as a guarantee. Never put a credential in an index URL or committed requirements file.

Third-party GitHub Actions must use full commit SHAs with human-readable version comments. The initial pins were resolved using upstream `git ls-remote` on 2026-11-10:

- `actions/checkout` v4.2.2: `11bd71901bbe5b1630ceea73d27597364c9af683`.
- `actions/setup-python` v5.6.0: `a26af69be951a213d495a4c3e4e4022e16d87065`.

These are retained, verified version pins, not a claim that they are the latest releases or vulnerability-free. Review upstream release notes and security advisories when updating. CI uses read-only contents permission, disables persisted checkout credentials, and does not use `pull_request_target`, deployment secrets, release/tag creation, or merge permissions.

## What GitHub Actions runs

For pushes to `main`/`feat/**`, pull requests and manual workflow dispatch, the six-job matrix uses Python 3.12/3.13/3.14 on Windows/Linux. Each job installs the pinned QA toolset and the local CLI, runs Ruff lint/format checks over `src`, `tests`, and `scripts`, validates the source skills, runs pytest, performs offline registry structural checks, builds sdist/wheel without fetching build-time dependencies, downloads pinned install dependencies into a wheelhouse, then executes the clean-install smoke script.

Each smoke run creates two fresh venvs without system/user packages, removes inherited Python/pip configuration (including external install targets and import paths), disables pip indexes and caches, installs one built artifact per environment from the prepared wheelhouse, checks import origin, runs `pip check`, CLI help/list, three flagship JSON/Markdown examples, source-validation failure without source data, and successful validation against the extracted sdist. Workspaces and `result.json` are retained under ignored `tmp/` locally; job logs contain the summary. Downloading QA/install wheels and provisioning Python/actions are network operations; review helpers and artifact installation itself stay offline.

## What it does not run

Hosted results remain NOT VERIFIED until a particular workflow run is inspected. CI does not launch Codex, test actual skill discovery/activation/nonactivation, evaluate model behavior or prompt-injection resistance, open browsers/screen readers, attack APIs, run real AI models, fetch standards URLs, assess copyrighted standard text, validate full SBOM/OpenAPI schemas, query vulnerability feeds, measure control effectiveness, or issue a compliance verdict. The [manual Codex plan](codex-integration-test-plan.md) and [QA matrix](qa-matrix.md) track these gaps.
