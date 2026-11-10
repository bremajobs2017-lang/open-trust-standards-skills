# CLI and input contracts

`trust-skills list` lists the 20 helpers. `trust-skills validate --root PATH` validates the source library's frontmatter, required content sections, catalog, example presence, and registry IDs. It requires the source repository; the wheel alone does not carry the library directory.

`trust-skills run NAME --input FILE [--format json|markdown] [--output NEW_FILE] [--fail-on-findings]` reads one local UTF-8 artifact, up to 5 MB. Text skills read HTML, Python, or text; all others read JSON. No helper sends requests or executes input code. No clocks, random IDs, or network results enter reports, so identical inputs produce deterministic output. File output uses exclusive creation and refuses to overwrite existing files, including the input file.

Exit codes: **0** means analysis completed (findings may exist); **1** means findings exist and `--fail-on-findings` was requested; **2** means usage, input, or output failure. No findings is not a compliance verdict. Nonfinite JSON literals, numeric overflow, and duplicate object keys are rejected. Error diagnostics avoid input snippets and private paths.

## Report envelope

Standard output and saved reports use UTF-8, including when Windows pipes inherit a legacy code page. Markdown uses escaped evidence tables and explicit reference fields.

Every review returns `schema_version`, `skill`, `assessment`, `summary.finding_count`, `findings`, `artifacts`, and `limitations`. A finding has `code`, `location`, `message`, `reference`, and `severity`. Most findings use `review`; selected dangerous-code and secret candidates use `high`. These local priorities are not standards-defined severities. `reference` uses a registry ID plus an optional verified topic identifier.

JSON and Markdown output apply selected credential redaction. Markdown escapes active HTML and Markdown syntax in input-derived content. Redaction is incomplete: review and sanitize evidence before sharing. No raw matched value, hash, source excerpt, or original file path appears in a secret-scanner finding.

## Inputs by skill

Runnable examples and detailed field contracts live inside each skill folder. Mandatory text fields must be nonempty. Record IDs must be unique within their collection.

| Helper | Input and meaningful behavior |
| --- | --- |
| `wcag-audit-planner` | JSON `scope`, `owner`, `level`, `pages`; proposes representative page-type/journey samples and retains critical pages. |
| `accessible-html-review` | HTML; checks language, title, missing image alt, selected names and ARIA references, duplicate IDs. |
| `aria-pattern-review` | HTML; checks selected role states, current slider value, dialog naming candidates, and ID references. |
| `keyboard-navigation-test` | HTML; identifies positive/invalid tabindex and custom click handlers; provides manual sequence tests. |
| `accessible-forms-review` | HTML; checks selected explicit, wrapping, and ARIA label associations and image-submit alternatives. |
| `accessible-design-system` | JSON `color_pairs`; opaque sRGB contrast with unrounded AA screening decisions. |
| `accessibility-report-generator` | JSON `findings`; validates a WCAG identifier subset, aggregates priorities/status, retains method provenance. |
| `threat-model-generator` | JSON `assets`, `flows`; validates endpoints and proposes boundary-aware threat hypotheses. |
| `secure-code-review` | Python source; AST checks for selected risky calls and `shell=True`, including simple import aliases. |
| `dependency-sbom-review` | CycloneDX 1.5/1.6/1.7 or SPDX 2.3 JSON (2.3.1 documentation); reviews component identity, version, license evidence and selected references. |
| `secrets-exposure-audit` | Text; credential-assignment, selected provider-token and private-key patterns, with redacted line findings. |
| `api-security-review` | OpenAPI 3.0.x/3.1.x JSON; security inheritance/override, anonymous alternatives, scheme references, object-ID review needs, root HTTP servers. |
| `nist-csf-control-mapper` | JSON `controls`; candidate mappings to GV, ID, PR, DE, RS, RC and evidence gaps. |
| `secure-development-lifecycle` | JSON `controls`; SSDF 1.1 PO, PS, PW, RV practice-group evidence gaps. |
| `ai-system-inventory` | JSON `systems`; validates ownership/lifecycle and flags deployed monitoring or stakeholder gaps. |
| `ai-risk-register` | JSON `risks`; validates dates/ratings, calculates local ordinal priorities and residual scores, flags approval gaps. |
| `ai-model-card-generator` | JSON model metadata and `evaluations`; structures supplied claims and flags missing slices. |
| `ai-evaluation-planner` | JSON `system_id`, `owner`, `decision`, `metrics`; compares supplied observations with local thresholds or leaves tests `not_run`. |
| `ai-governance-controls-mapper` | JSON `controls`; candidate mappings to GOVERN, MAP, MEASURE, MANAGE and evidence gaps. |
| `llm-application-security-review` | JSON `system_id`, `owner`, `controls`; checks evidence presence for ten OWASP 2025 LLM risk topics. |

## Explicit subsets and policies

Accessibility reporting accepts these verified WCAG 2.2 identifiers: `1.1.1`, `1.3.1`, `1.4.3`, `1.4.10`, `1.4.11`, `2.1.1`, `2.1.2`, `2.4.2`, `2.4.3`, `2.4.7`, `2.4.11`, `2.5.8`, `3.1.1`, `3.3.1`, `3.3.2`, `4.1.2`. This is not a complete checklist. Duplicate IDs are reported as a potential ARIA association issue, not as the removed WCAG 4.1.1 criterion. Human findings require a reviewer role or pseudonymous reviewer ID.

Risk ratings are local integers 1–5. The local score is likelihood × impact, high at 15+, medium at 6+, otherwise low. Both residual ratings are required if either is supplied. Accepted or closed status without `approval_evidence` is an evidence gap; evidence presence is not approval validation. Dates are validated for calendar syntax, not overdue status. Cross-file inventory links require human verification.

Evaluation metrics use `at_least` or `at_most` and numeric `threshold`, optional `observed`; equality meets the local threshold. No observation yields `not_run`. This tool never runs an evaluation or approves release.

Framework mapping deliberately rejects subcategory/task IDs because only function/practice-group mappings have been implemented. SBOM review checks selected metadata quality rather than full schemas; empty or unasserted license data is a review gap, not an automatic format violation. External references are never fetched. Unknown LLM control keys are rejected to catch misspellings; evidence strings remain unverified.
