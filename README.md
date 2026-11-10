# Open Trust Standards Skills

20 Agent Skills for accessibility, cybersecurity, and AI governance—designed to help teams translate trust standards into practical, reviewable work.

## Project status

The released pre-release baseline is v0.1.0: seven accessibility skills, seven cybersecurity skills, and six AI governance skills. This branch develops QA hardening toward v0.2.0 (`0.2.0.dev0` package version); it does not create a release. Every skill has portable instructions, locally checked frontmatter, a synthetic example, an offline helper, and deterministic tests. Human domain review is required before relying on outputs for consequential decisions.

Independent v0.1.0 source-ZIP QA reported 144 passing tests and structural validation of 20 skills/16 registry entries. Independent lint/build, live retrieval of all source URLs, and actual Codex discovery/activation were **NOT VERIFIED**. See the [QA matrix](docs/qa-matrix.md) for evidence separated by environment and scope.

## Skill library

| # | Area | Skill | Capability |
| --- | --- | --- | --- |
| 1 | accessibility | [wcag-audit-planner](skills/wcag-audit-planner/SKILL.md) | Scope and sample a WCAG 2.2 audit. |
| 2 | accessibility | [accessible-html-review](skills/accessible-html-review/SKILL.md) | Check selected static HTML accessibility issues with line evidence. |
| 3 | accessibility | [aria-pattern-review](skills/aria-pattern-review/SKILL.md) | Review selected widget roles, states, names, and references. |
| 4 | accessibility | [keyboard-navigation-test](skills/keyboard-navigation-test/SKILL.md) | Identify focus-order candidates and guide manual keyboard testing. |
| 5 | accessibility | [accessible-forms-review](skills/accessible-forms-review/SKILL.md) | Review field labels, associations, and error-recovery tests. |
| 6 | accessibility | [accessible-design-system](skills/accessible-design-system/SKILL.md) | Calculate color-pair contrast and review component states. |
| 7 | accessibility | [accessibility-report-generator](skills/accessibility-report-generator/SKILL.md) | Prioritize findings while preserving automated/human provenance. |
| 8 | cybersecurity | [threat-model-generator](skills/threat-model-generator/SKILL.md) | Generate boundary-aware threat hypotheses from assets and flows. |
| 9 | cybersecurity | [secure-code-review](skills/secure-code-review/SKILL.md) | Review selected Python calls and shell usage without execution. |
| 10 | cybersecurity | [dependency-sbom-review](skills/dependency-sbom-review/SKILL.md) | Review supported CycloneDX/SPDX component metadata and references. |
| 11 | cybersecurity | [secrets-exposure-audit](skills/secrets-exposure-audit/SKILL.md) | Identify selected credential patterns with redacted findings. |
| 12 | cybersecurity | [api-security-review](skills/api-security-review/SKILL.md) | Review OpenAPI security declarations and authorization test needs. |
| 13 | cybersecurity | [nist-csf-control-mapper](skills/nist-csf-control-mapper/SKILL.md) | Map candidate evidence to six CSF 2.0 functions. |
| 14 | cybersecurity | [secure-development-lifecycle](skills/secure-development-lifecycle/SKILL.md) | Review lifecycle evidence across four SSDF 1.1 practice groups. |
| 15 | ai-governance | [ai-system-inventory](skills/ai-system-inventory/SKILL.md) | Normalize accountable system records and flag evidence gaps. |
| 16 | ai-governance | [ai-risk-register](skills/ai-risk-register/SKILL.md) | Validate, score, and prioritize risks under an explicit local policy. |
| 17 | ai-governance | [ai-model-card-generator](skills/ai-model-card-generator/SKILL.md) | Structure supplied model-use, data, evaluation, and limitation evidence. |
| 18 | ai-governance | [ai-evaluation-planner](skills/ai-evaluation-planner/SKILL.md) | Plan local evaluation gates and compare supplied observations. |
| 19 | ai-governance | [ai-governance-controls-mapper](skills/ai-governance-controls-mapper/SKILL.md) | Map candidate evidence to four AI RMF 1.0 functions. |
| 20 | ai-governance | [llm-application-security-review](skills/llm-application-security-review/SKILL.md) | Review evidence gaps across ten OWASP 2025 LLM risk topics. |

## Design principles

- **Evidence first:** distinguish verified findings from assumptions and missing information.
- **Human accountability:** keep consequential decisions and approvals with responsible people.
- **Traceable standards:** identify the source, version, scope, and limitations of every standards mapping.
- **Accessible outputs:** write clear guidance and produce artifacts usable by diverse teams.
- **Responsible operation:** minimize sensitive data collection and require authorization for security testing.

References include WCAG 2.2, WAI-ARIA 1.2, NIST CSF 2.0, NIST AI RMF 1.0, NIST SSDF 1.1, OWASP ASVS 5.0.0, OWASP API Security Top 10 (2023), and OWASP LLM Top 10 (2025). The [standards registry](standards/registry.yaml) records selected editions, official URLs, verification status, and scope. These references are not claims of certification, endorsement, or complete coverage. Restricted standards text is not reproduced.

## Quick start

Use Python 3.12+ in an isolated environment:

```sh
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -e ".[dev]"
trust-skills list
trust-skills validate --root .
trust-skills run accessible-html-review --input skills/accessible-html-review/examples/input.html
trust-skills run dependency-sbom-review --input skills/dependency-sbom-review/examples/input.json
trust-skills run ai-risk-register --input skills/ai-risk-register/examples/input.json --format markdown
python -m pytest -q
```

For Windows, Codex, and other compatible agents, read [installation](docs/installation.md). The shared CLI is installed separately from skill folders; examples assume the repository root as the working directory. No package publication or automatic agent configuration is performed.

The wheel intentionally contains the Python CLI, **not** the 20 skill directories. Use a checkout or extracted sdist for skills, examples and source validation. `pip install` never installs or activates these skills in an agent host. See [the opt-in manual Codex checklist](docs/codex-integration-test-plan.md).

## Structure and verification

- `skills/<name>/SKILL.md`: activation, inputs, procedures, outputs, examples, validation, limitations, and official references.
- `skills/<name>/examples/`: safe synthetic runnable inputs.
- `src/trust_skills/`: offline Python tools and the `trust-skills` CLI.
- `tests/`: deterministic behavioral tests for all 20 skills, metadata, privacy, invalid inputs, and reports.
- `standards/registry.yaml`: source verification and edition notes.
- `.github/workflows/ci.yml`: lint, formatting, tests, skill validation, and builds across Python 3.12–3.14 on Linux and Windows.

QA hardening adds fresh-environment sdist/wheel install smoke tests, separately curated synthetic fixtures with documented heuristic limitations, negative tests, and explicit [structural versus live registry checks](docs/registry-verification.md). HTTP retrieval never establishes semantic verification. [QA policy](docs/qa-policy.md) records exact dependency/action pins and what CI does and does not exercise.

See [CLI contracts](docs/cli.md), [development guidance](docs/development.md), [local validation results](docs/validation.md), and [branch publication and PR guidance](docs/publishing.md).

## Assessment boundaries

Automated checks are bounded heuristics and evidence transformations. They do not perform browser or screen-reader testing, send API requests, run models, query vulnerability feeds, prove control effectiveness, or establish legal compliance. Standards mappings use explicit subsets; framework mapping stops at function/practice-group level. Reports distinguish candidates and supplied assertions from human-reviewed conclusions. A report with no findings means only that the implemented checks found none.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes and [AGENTS.md](AGENTS.md) for repository-specific agent instructions. Report vulnerabilities through the process in [SECURITY.md](SECURITY.md).

This project supports assessment and decision-making; its outputs do not establish legal compliance or replace qualified professional review.

## License

Licensed under the [Apache License 2.0](LICENSE).
