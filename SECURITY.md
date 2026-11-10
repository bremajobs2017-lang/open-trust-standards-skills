# Security policy

## Supported versions

The initial library is pre-release (package version 0.1.0). There are no supported stable release lines yet. Report vulnerabilities in the current repository version; fixes target the active development branch until reviewed and merged. A release support policy will be established with stable releases.

## Tool boundaries

Local review helpers do not execute input code, send network requests, or validate live credentials. Inputs are limited to 5 MB. Secret detection and output redaction cover selected patterns only and are not a data-loss-prevention system. Use synthetic or approved sanitized artifacts, inspect reports before sharing them, and keep real incident evidence private. Install dependencies from trusted sources in an isolated environment.

## Reporting a vulnerability

Do not report exploitable details, credentials, or sensitive information in a public issue or pull request.

If the repository's **Security** tab offers **Report a vulnerability**, use that private reporting channel. If it is unavailable, open a public issue containing only a request for a private security contact, with no vulnerability details. Wait for the maintainer to establish a private channel before sharing evidence.

A private report should include:

- The affected file, revision, or skill.
- The potential impact and required conditions.
- Minimal reproduction steps using synthetic data.
- Suggested mitigations, if known.

Do not attach live secrets or personal data. If credentials have been exposed, revoke or rotate them promptly through the relevant provider.

## Coordinated handling

The maintainer will assess reports and coordinate remediation and disclosure with the reporter. This project does not currently promise a response time or provide a bug bounty. Please allow remediation before publishing exploitable details.

Only test systems you own or are explicitly authorized to assess. Reporting a vulnerability does not grant authorization to access third-party systems or data.
