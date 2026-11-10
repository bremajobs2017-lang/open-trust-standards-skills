# Registry structure, retrieval, and semantic review

Three different kinds of evidence must stay separate:

1. **Structural validation:** required fields, unique IDs, supported status values, parseable dates, official-host HTTPS URLs, and library reference links. This does not contact sources or verify editions or content.
2. **URL retrieval:** opt-in HTTP status/redirect/failure observations at a recorded UTC time. A 200 response might be a login page, error page, changed edition, or unrelated content.
3. **Semantic review:** a qualified reviewer reads authoritative content, checks the selected edition and mapped identifiers, and records rationale and limits. Neither a successful HTTP response nor local metadata performs this review.

The registry's `verification_status`, `verified_on`, and `verification_scope` are historical maintainer assertions, now labeled `maintainer-reviewed`. They are not independent QA results. `independent_url_retrieval: not-recorded` explicitly describes the repository's current evidence; a separate retrieval report does not silently rewrite it. Legacy `verified-official-source` remains readable for backward compatibility and must not be interpreted as independent verification.

## Commands

These commands work from a source checkout with the CLI installed:

```sh
# Offline: no network, even when registry fields say maintainer-reviewed.
trust-skills registry --registry standards/registry.yaml

# Explicit opt-in: requests primary and supporting URLs; writes a NEW evidence file.
trust-skills registry --registry standards/registry.yaml --live --timeout 5 --output retrieval-2026-11-10.json
```

The second command is an example, not evidence that it was run. Run it only when you choose network verification. Existing output files are refused before requests start. Exit 0 means structural success or all requested URLs retrieved; exit 1 means at least one retrieval failed/timed out; exit 2 means an input/output error. Successful retrievals always have `semantic_status: not-assessed`.

Each retrieval records `source_id`, `requested_url`, UTC `retrieved_at`, `final_url`, `http_status`, redirect hops/statuses, `retrieval_status` and `failure`. The tool requests response headers/status using GET and closes without reading the body. HTTP retrieval is not body integrity, title, clause, edition, license, or conformance verification. It never executes content or sends authentication credentials.

## Bounds and tests

The timeout is 0.1–30 seconds **per URL**, default 5. A parent process enforces the deadline across DNS, TLS, headers, and redirects, then terminates the worker with up to one second of cleanup. URLs are checked sequentially, so total time depends on the number of primary/supporting URLs. Five redirects are followed; attempted blocked hops are recorded. Only HTTPS on the explicit reviewed-host allowlist is permitted. Credentials, query strings, fragments, arbitrary ports, literal local addresses and unreviewed hosts are rejected. A legitimate new redirect host requires maintainer review of the allowlist; do not bypass it automatically.

Default tests mock HTTP successes, failures, redirects, and deadlines without making external requests. These tests verify tooling behavior, not availability of the 16 sources. CI does not opt in to live retrieval. Transport evidence does not alter the registry or imply semantic approval. Recheck reports for sensitive redirect data before sharing; redaction covers selected patterns only.
