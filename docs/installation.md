# Installation and agent use

This library has two parts: portable skill instructions in `skills/`, and a shared Python CLI in `src/trust_skills`. Installing a skill folder does not install Python or the CLI. The wheel supplies the CLI; the Git checkout and source distribution also contain skills, examples, registry, and tests. No package has been published to PyPI by this change.

## Install the local CLI

Use Python 3.12 or later. From the cloned repository, create an isolated environment and install the local project:

```sh
python -m venv .venv
# Linux/macOS
. .venv/bin/activate
python -m pip install -e ".[dev]"
trust-skills list
trust-skills validate --root .
```

On Windows PowerShell, use an explicit interpreter if the `python` command resolves to a Microsoft Store alias. Activation is optional:

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\trust-skills.exe list
.\.venv\Scripts\trust-skills.exe validate --root .
```

Replace `-3.14` with your installed Python version (3.12+). For runtime use without development tools, install with `python -m pip install .`. Initial installation requires an approved dependency source. The review helpers themselves work offline.

## Codex

Codex discovers local skills under `.agents/skills` in a repository or `~/.agents/skills` for a user. It also supports its skill installer. See the [official OpenAI skill documentation](https://learn.chatgpt.com/docs/build-skills) for current discovery and invocation behavior.

For local use, copy selected folders from this repository's `skills/` into the chosen host's skill directory, retaining the folder name and `examples/`. Copy the repository LICENSE alongside your distribution. Inspect the destination first and do not overwrite an existing skill. Installing all 20 is optional; a smaller relevant selection keeps discovery focused. This repository does not automatically modify your agent configuration or install into other projects.

Example for a single repo-local installation, run from the repository where you deliberately want the skill available:

```powershell
$sourceSkill = 'C:\path\to\open-trust-standards-skills\skills\accessible-html-review'
$skillDestination = Join-Path (Get-Location) '.agents\skills\accessible-html-review'
if (Test-Path -LiteralPath $skillDestination) { throw 'Skill already exists; inspect it before updating.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $skillDestination) -Force | Out-Null
Copy-Item -LiteralPath $sourceSkill -Destination $skillDestination -Recurse
```

Use `/skills` or mention `$accessible-html-review` in Codex. If the skill does not appear, restart Codex. Ensure the agent's execution environment can find `trust-skills` or provide the explicit path to its virtual-environment executable. For reusable distribution, OpenAI recommends plugin packaging; this initial library supplies portable source folders rather than an OpenAI marketplace plugin.

## Other compatible agents

The instructions follow the [Agent Skills specification](https://agentskills.io/specification) with standard frontmatter only. Host discovery, permissions, and tool invocation remain host-specific.

For Claude Code, copy a selected skill into `.claude/skills/<name>/` in the intended project (or its documented personal location), preserving examples and avoiding existing folders. Invoke `/accessible-html-review`. See [Claude Code's official skills guide](https://code.claude.com/docs/en/skills). The `$skill-name` text inside our examples is Codex invocation syntax; adapt that user prompt to the host's syntax.

For another host, follow its official instructions for adding a skill directory. If it cannot execute Python, use the documented procedures manually and clearly state that automated helpers were not run. No end-to-end host integration has been tested as part of the Python suite.

## Try the three flagship examples

From the source repository, with the CLI installed:

```sh
trust-skills run accessible-html-review --input skills/accessible-html-review/examples/input.html
trust-skills run dependency-sbom-review --input skills/dependency-sbom-review/examples/input.json
trust-skills run ai-risk-register --input skills/ai-risk-register/examples/input.json --format markdown
```

The first and third examples deliberately contain review gaps. These examples use synthetic data, not production evidence. Each skill's `SKILL.md` states its expected result and manual validation work.
