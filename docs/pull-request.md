# Harden pre-release QA toward v0.2.0

v0.1.0's source-ZIP tests did not establish clean artifact installation, actual Codex activation, live URL retrieval, or independently verified lint/build results. This change adds separate fresh-venv sdist/wheel installation checks, an opt-in manual host checklist, explicit structural versus live registry verification, stronger synthetic negative tests, and separately curated fixture expectations with documented heuristic limits.

The wheel intentionally remains CLI-only; source data and host skill installation are documented separately. URL retrieval records UTC time, redirects, status and failures under bounded timeouts and always leaves semantic verification not assessed. Registry review fields are maintainer assertions rather than independent QA evidence. Actions use full SHA pins, and CI uses an explicit QA dependency selection.

Validation and exact commands are recorded in [the QA matrix](qa-matrix.md). Hosted CI, actual agent-host behavior, live source availability, semantic standards interpretation, independent human fixture review and domain compliance assessments remain separate unverified work. This implementation is AI-assisted and does not claim certification or endorsement.

No merge, tag, release, push, or PR creation is authorized by this local commit. Owner approval is required before publishing the branch or opening the PR.
