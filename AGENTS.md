# Agent instructions

## Scope and status

Work only in this repository and within the user's requested scope. The owner has explicitly authorized implementation of the 20 skills listed in README.md. Preserve unrelated user changes; do not create repositories, modify unrelated projects, force-push, or merge into main automatically.

## Working practices

- Inspect existing files and Git status before making changes. Preserve unrelated user edits.
- Keep changes focused, reviewable, and consistent with the README roadmap.
- Never commit credentials, personal information, confidential assessment evidence, or proprietary standards text.
- Use clear Markdown, descriptive links, and accessible tables and examples.
- Identify the exact source and version when mapping requirements to a standard. Separate requirements, recommendations, assumptions, and evidence gaps.
- Do not claim certification, compliance, test execution, or standards coverage without supporting evidence.
- Security testing requires explicit authorization and a defined target scope.

## Skill implementation

Each skill lives in skills/<name>/SKILL.md and follows the Agent Skills specification. Define its purpose, triggers, inputs, prerequisites, workflow, safeguards, outputs, examples, validation criteria, limitations, and official references. Include human review checkpoints for consequential decisions. Avoid unnecessary dependencies and duplication.

Shared Python 3.12+ tools live in src/trust_skills. Run `python -m pip install -e ".[dev]"`, `python -m ruff check src tests`, `python -m ruff format --check src tests`, `python -m pytest -q`, and `trust-skills validate --root .`. Every skill needs a synthetic example and meaningful deterministic tests. Keep the CLI catalog, standards registry, skill documentation, and test coverage synchronized. No network access or input execution belongs in local review helpers.

## Validation and reporting

For documentation changes, check accuracy, internal links, Markdown structure, and accidental sensitive data. Run relevant existing checks for code or scripts when introduced. Report what changed, what was verified, and any unresolved limitations. Never invent successful checks.
