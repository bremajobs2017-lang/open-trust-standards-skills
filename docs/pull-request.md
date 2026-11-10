# Implement initial library of 20 trust standards Agent Skills

This change turns the planning repository into a working pre-release library: seven accessibility skills, seven cybersecurity skills, and six AI governance skills. Every skill includes standard frontmatter, concrete procedures, local input contracts, a synthetic example, expected behavior, validation guidance, limitations, and official references.

The Python 3.12+ `trust-skills` CLI provides offline HTML, SBOM, API, source-code, secrets, inventory, risk, evaluation, evidence-mapping, and reporting assistance. Shared reports preserve evidence gaps and human review requirements. The helpers do not make conformance, certification, endorsement, or legal compliance claims.

Validation includes deterministic tests for every skill, malformed-input cases, metadata, redaction and report safety, lint, formatting, skill validation, and package builds. The GitHub Actions workflow adds Python 3.12–3.14 checks on Linux and Windows; hosted CI results must be checked after publishing this branch.

Standards mappings are deliberately bounded: CSF and AI RMF functions, SSDF practice groups, selected WCAG/ARIA checks, and explicit SBOM/OpenAPI edition subsets. Browser/assistive-technology tests, runtime security testing, vulnerability feeds, actual AI evaluations, and end-to-end host-agent integration require separate human review.

Implementation was AI-assisted. No real personal data, live credentials, or restricted standards text is included. Maintainer review and CI approval are required before merging.
