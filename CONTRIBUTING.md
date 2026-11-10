# Contributing

Thank you for helping make trust standards practical and accessible.

## Current scope

The owner has authorized the initial 20-skill library. Contributions to skill guidance, safe local tools, synthetic examples, standards traceability, and validation are welcome. Discuss additional skills or major scope changes with the maintainer first.

## Proposing changes

1. Open an issue describing the problem, intended users, proposed outcome, and relevant standards or evidence. Do not include sensitive data.
2. For substantial changes, agree on scope with the maintainer before implementation.
3. Create a focused branch and make a small, reviewable change.
4. Check Markdown, links, factual claims, and any applicable tests.
5. Open a pull request explaining the change, its purpose, verification performed, and limitations.

## Quality expectations

Use Python 3.12+ and install development dependencies with `python -m pip install -e ".[dev]"`. Before submitting, run `python -m ruff check src tests`, `python -m ruff format --check src tests`, `python -m pytest -q`, `trust-skills validate --root .`, and `python -m build`. The CI matrix checks Python 3.12–3.14 on Linux and Windows. See [development guidance](docs/development.md) for architecture and test expectations.

- Use plain, inclusive language and accessible examples.
- Cite authoritative sources and specify standards versions and assessment scope.
- Distinguish normative requirements from project guidance.
- Use synthetic or properly anonymized examples; exclude credentials and confidential material.
- Respect copyright and licensing. Reference proprietary standards instead of copying restricted text.
- Document assumptions and retain human accountability for consequential decisions.
- Disclose material AI assistance and verify generated content before submitting it.

## Community conduct

Treat contributors respectfully. Discuss ideas constructively, welcome different perspectives, and avoid harassment or discriminatory behavior.

## Security reports

Follow [SECURITY.md](SECURITY.md) for vulnerabilities. Do not disclose exploitable details in public issues or pull requests.

## Licensing

By submitting a contribution, you agree that your contribution is provided under this repository's Apache-2.0 license and that you have the right to submit it. Clearly identify any third-party material and its license.
