"""Separate registry structure checks from explicitly requested HTTP retrieval evidence."""

import multiprocessing
import queue
import time
from datetime import UTC, date, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .core import InputError, read_text, sanitize
from .metadata import load_yaml

ALLOWED_HOSTS = frozenset(
    {
        "agentskills.io",
        "www.w3.org",
        "www.nist.gov",
        "csrc.nist.gov",
        "nvlpubs.nist.gov",
        "asvs.owasp.org",
        "api-security.owasp.org",
        "genai.owasp.org",
        "cyclonedx.org",
        "spdx.github.io",
        "spec.openapis.org",
        "arxiv.org",
        "learn.chatgpt.com",
        "community.owasp.org",
        "owasp.org",
        "www.owasp.org",
    }
)
STATUSES = {"maintainer-reviewed", "not-reviewed", "verified-official-source"}


def checked_url(url):
    if not isinstance(url, str):
        raise InputError("Registry URLs must be text")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or parsed.query
        or parsed.fragment
        or any(ord(c) < 33 for c in url)
    ):
        raise InputError(
            "URL must be HTTPS on a reviewed official host, without credentials, queries, fragments, or custom ports"
        )
    return url


def load_registry(path):
    registry = load_yaml(read_text(path))
    if (
        not isinstance(registry, dict)
        or not isinstance(registry.get("sources"), list)
        or not registry["sources"]
    ):
        raise InputError("Registry requires a nonempty sources array")
    seen = set()
    for source in registry["sources"]:
        if not isinstance(source, dict):
            raise InputError("Registry sources must be objects")
        for key in (
            "id",
            "title",
            "edition",
            "official_url",
            "verification_status",
            "verified_on",
            "verification_scope",
        ):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise InputError("Registry source fields must be nonempty text")
        if source["id"] in seen:
            raise InputError("Duplicate registry source ID")
        seen.add(source["id"])
        if source["verification_status"] not in STATUSES:
            raise InputError("Unknown registry review status")
        try:
            date.fromisoformat(source["verified_on"])
            checked_url(source["official_url"])
            supporting = source.get("supporting_urls", [])
            if not isinstance(supporting, list):
                raise InputError("supporting_urls must be an array")
            for url in supporting:
                checked_url(url)
        except ValueError as exc:
            raise InputError("Invalid registry date or URL") from exc
    return registry


class RedirectRecorder(HTTPRedirectHandler):
    def __init__(self, on_redirect=None):
        self.redirects = []
        self.on_redirect = on_redirect

    def redirect_request(self, request, fp, code, msg, headers, newurl):
        target = urljoin(request.full_url, newurl)
        # Record blocked redirect attempts too; the target is not fetched.
        self.redirects.append({"from_url": request.full_url, "http_status": code, "to_url": target})
        if self.on_redirect:
            self.on_redirect(self.redirects[-1])
        if len(self.redirects) > 5:
            raise InputError("Redirect limit exceeded")
        checked_url(target)
        return super().redirect_request(request, fp, code, msg, headers, target)


def retrieve(url, timeout, on_redirect=None):
    recorder = RedirectRecorder(on_redirect)
    result = {
        "requested_url": url,
        "final_url": None,
        "http_status": None,
        "redirects": recorder.redirects,
        "retrieval_status": "failed",
        "failure": None,
        "semantic_status": "not-assessed",
    }
    try:
        checked_url(url)
        request = Request(
            url, headers={"User-Agent": "trust-skills-reference-check/0.2", "Accept": "*/*"}
        )
        with build_opener(recorder).open(request, timeout=timeout) as response:
            result.update(
                final_url=response.geturl(),
                http_status=response.status,
                retrieval_status="retrieved",
            )
            # Headers/status only. Neither HTML nor PDFs are executed or interpreted.
    except HTTPError as exc:
        result.update(http_status=exc.code, final_url=exc.geturl(), failure="HTTPError")
        exc.close()
    except (URLError, OSError, InputError, ValueError) as exc:
        result["failure"] = type(exc).__name__
    return sanitize(result)


def _worker(url, timeout, output):
    result = retrieve(
        url, timeout, lambda event: output.put({"event": "redirect", "data": sanitize(event)})
    )
    output.put({"event": "done", "data": result})


def bounded_retrieve(url, timeout):
    """A parent deadline also bounds slow DNS, TLS, headers, and redirect chains."""
    context = multiprocessing.get_context("spawn")
    output = context.Queue()
    process = context.Process(target=_worker, args=(url, timeout, output), daemon=True)
    process.start()
    redirects = []
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                event = output.get(timeout=max(0, deadline - time.monotonic()))
            except queue.Empty:
                return {
                    "requested_url": url,
                    "final_url": None,
                    "http_status": None,
                    "redirects": redirects,
                    "retrieval_status": "timeout",
                    "failure": "DeadlineExceeded",
                    "semantic_status": "not-assessed",
                }
            if event["event"] == "done":
                return event["data"]
            redirects.append(event["data"])
    finally:
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        output.close()


def verify_registry(path, *, live=False, timeout=5.0, fetch=None):
    if not 0.1 <= timeout <= 30:
        raise InputError("Timeout must be between 0.1 and 30 seconds per URL")
    registry = load_registry(path)
    result = {
        "mode": "live-url" if live else "structural-only",
        "sources_checked": len(registry["sources"]),
        "network_requested": live,
        "semantic_status": "not-assessed",
        "retrievals": [],
    }
    if not live:
        return result
    fetch = fetch or bounded_retrieve
    for source in registry["sources"]:
        for url in (source["official_url"], *source.get("supporting_urls", [])):
            entry = fetch(url, timeout)
            entry.update(
                source_id=source["id"],
                retrieved_at=datetime.now(UTC).isoformat(),
                semantic_status="not-assessed",
            )
            result["retrievals"].append(entry)
    return sanitize(result)
