# Open Trust Standards Skills

Planned Agent Skills for accessibility, cybersecurity, and AI governance—designed to help teams translate trust standards into practical, reviewable work.

## Project status

This repository is in its planning stage. The 20 skills below are a proposed roadmap; no skills have been implemented yet. Scope, standards mappings, and validation criteria will be refined before implementation.

## Planned skills

| # | Area | Planned skill | Intended outcome |
| --- | --- | --- | --- |
| 1 | Accessibility | Accessibility requirements and scoping | Define user needs, accessibility targets, and acceptance criteria. |
| 2 | Accessibility | WCAG assessment planning | Prepare a structured assessment against an identified WCAG version and level. |
| 3 | Accessibility | Keyboard and focus review | Review keyboard access, navigation order, and visible focus. |
| 4 | Accessibility | Screen reader and semantic review | Review structure, names, roles, and assistive technology behavior. |
| 5 | Accessibility | Accessible content and documents | Review content clarity, document structure, and alternative text. |
| 6 | Accessibility | Accessibility remediation and evidence | Prioritize findings and document fixes and verification evidence. |
| 7 | Cybersecurity | Security requirements and risk scoping | Identify assets, boundaries, security requirements, and risk assumptions. |
| 8 | Cybersecurity | Threat modeling | Document threats, abuse cases, mitigations, and residual risks. |
| 9 | Cybersecurity | Secure architecture review | Review trust boundaries, data flows, and architectural controls. |
| 10 | Cybersecurity | Identity and access review | Assess authentication, authorization, and least privilege. |
| 11 | Cybersecurity | Dependency and supply chain review | Review dependency provenance, vulnerabilities, and software inventory. |
| 12 | Cybersecurity | Secure configuration and secrets review | Identify configuration weaknesses and unsafe secret handling. |
| 13 | Cybersecurity | Incident readiness and response planning | Prepare response roles, playbooks, and evidence handling procedures. |
| 14 | AI governance | AI system inventory and classification | Document AI use cases, ownership, impact, and risk classification. |
| 15 | AI governance | AI impact and risk assessment | Assess affected stakeholders, foreseeable harms, and risk treatments. |
| 16 | AI governance | Data governance and provenance | Review data sources, permissions, quality, and lineage. |
| 17 | AI governance | Model evaluation and assurance | Define evaluation criteria and document performance and safety evidence. |
| 18 | AI governance | Fairness and transparency review | Assess disparate impacts and prepare understandable disclosures. |
| 19 | AI governance | Human oversight and accountability | Define decision authority, escalation paths, and oversight controls. |
| 20 | AI governance | AI monitoring and governance evidence | Plan ongoing monitoring, change review, and governance records. |

## Design principles

- **Evidence first:** distinguish verified findings from assumptions and missing information.
- **Human accountability:** keep consequential decisions and approvals with responsible people.
- **Traceable standards:** identify the source, version, scope, and limitations of every standards mapping.
- **Accessible outputs:** write clear guidance and produce artifacts usable by diverse teams.
- **Responsible operation:** minimize sensitive data collection and require authorization for security testing.

Potential reference frameworks include WCAG, OWASP guidance, the NIST Cybersecurity Framework, the NIST AI Risk Management Framework, and relevant ISO/IEC standards. These are candidate references, not claims of certification, endorsement, or complete coverage. Standards text will not be reproduced without appropriate rights.

## Intended skill structure

Each future skill is expected to include a `SKILL.md` with its purpose, triggers, prerequisites, workflow, safeguards, expected outputs, and validation criteria. Supporting references, templates, or scripts will be added only where needed. The final directory layout will be established when implementation begins.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes and [AGENTS.md](AGENTS.md) for repository-specific agent instructions. Report vulnerabilities through the process in [SECURITY.md](SECURITY.md).

This project supports assessment and decision-making; its outputs do not establish legal compliance or replace qualified professional review.

## License

Licensed under the [Apache License 2.0](LICENSE).
