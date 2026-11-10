import json
import queue
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request

import pytest

from trust_skills.cli import main
from trust_skills.core import InputError
from trust_skills.registry import (
    RedirectRecorder,
    bounded_retrieve,
    checked_url,
    load_registry,
    retrieve,
    verify_registry,
)

REGISTRY = Path(__file__).resolve().parents[1] / "standards/registry.yaml"


def test_parent_deadline_preserves_redirect_and_terminates_worker(monkeypatch):
    events = [
        {
            "event": "redirect",
            "data": {
                "from_url": "https://www.w3.org/",
                "to_url": "https://www.w3.org/TR/",
                "http_status": 302,
            },
        }
    ]
    state = {}

    class Output:
        def get(self, timeout):
            assert 0 <= timeout <= 0.2
            if events:
                return events.pop()
            raise queue.Empty

        def close(self):
            state["closed"] = True

    class Process:
        def start(self):
            pass

        def is_alive(self):
            return True

        def terminate(self):
            state["terminated"] = True

        def join(self, timeout):
            assert timeout == 1

    class Context:
        def Queue(self):
            return Output()

        def Process(self, **kwargs):
            return Process()

    monkeypatch.setattr("trust_skills.registry.multiprocessing.get_context", lambda *a: Context())
    result = bounded_retrieve("https://www.w3.org/", 0.2)
    assert result["retrieval_status"] == "timeout" and len(result["redirects"]) == 1
    assert state == {"closed": True, "terminated": True}


def test_cli_live_failure_returns_one_and_writes_evidence(tmp_path, monkeypatch):
    result = {
        "mode": "live-url",
        "semantic_status": "not-assessed",
        "retrievals": [
            {
                "retrieval_status": "timeout",
                "http_status": None,
                "redirects": [],
                "retrieved_at": "2026-11-10T00:00:00+00:00",
            }
        ],
    }
    monkeypatch.setattr("trust_skills.cli.verify_registry", lambda *a, **k: result)
    output = tmp_path / "synthetic-evidence.json"
    assert main(["registry", "--registry", str(REGISTRY), "--live", "--output", str(output)]) == 1
    assert json.loads(output.read_text())["semantic_status"] == "not-assessed"


def test_structural_check_never_calls_network():
    def forbidden(*args):
        pytest.fail("Network used without opt-in")

    result = verify_registry(REGISTRY, fetch=forbidden)
    assert result["mode"] == "structural-only" and result["sources_checked"] == 16
    assert not result["retrievals"] and not result["network_requested"]
    assert result["semantic_status"] == "not-assessed"


def test_live_results_record_dates_failures_and_redirects_without_promoting_semantics():
    def synthetic(url, timeout):
        assert timeout == 0.5
        return {
            "requested_url": url,
            "final_url": url,
            "http_status": 503,
            "redirects": [{"from_url": url, "to_url": url, "http_status": 302}],
            "retrieval_status": "failed",
            "failure": "HTTPError",
            "semantic_status": "verified",
        }

    before = REGISTRY.read_bytes()
    result = verify_registry(REGISTRY, live=True, timeout=0.5, fetch=synthetic)
    assert result["retrievals"] and all(
        e["retrieved_at"].endswith("+00:00") for e in result["retrievals"]
    )
    assert all(
        e["semantic_status"] == "not-assessed" and e["http_status"] == 503 and e["redirects"]
        for e in result["retrievals"]
    )
    assert REGISTRY.read_bytes() == before


@pytest.mark.parametrize(
    "url",
    [
        "http://www.w3.org/",
        "https://127.0.0.1/",
        "https://localhost/",
        "https://www.w3.org.evil.invalid/",
        "https://user:synthetic@www.w3.org/",
        "file:///private",
        "https://www.w3.org/?token=synthetic",
    ],
)
def test_disallowed_destinations(url):
    with pytest.raises(InputError):
        checked_url(url)


def test_redirect_blocked_and_recorded_before_fetch():
    recorder = RedirectRecorder()
    with pytest.raises(InputError):
        recorder.redirect_request(
            Request("https://www.w3.org/"), None, 302, "Found", {}, "https://localhost/private"
        )
    assert recorder.redirects[0]["http_status"] == 302


@pytest.mark.parametrize(
    "failure",
    [URLError("synthetic timeout"), HTTPError("https://www.w3.org/", 404, "synthetic", {}, None)],
)
def test_http_failures_are_evidence(monkeypatch, failure):
    class Opener:
        def open(self, *args, **kwargs):
            raise failure

    monkeypatch.setattr("trust_skills.registry.build_opener", lambda *args: Opener())
    result = retrieve("https://www.w3.org/", 0.2)
    assert result["retrieval_status"] == "failed"
    assert result["semantic_status"] == "not-assessed"


def test_http_success_is_not_semantic_verification(monkeypatch):
    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def geturl(self):
            return "https://www.w3.org/"

    class Opener:
        def open(self, *args, **kwargs):
            return Response()

    monkeypatch.setattr("trust_skills.registry.build_opener", lambda *args: Opener())
    result = retrieve("https://www.w3.org/", 0.2)
    assert result["retrieval_status"] == "retrieved" and result["semantic_status"] == "not-assessed"


@pytest.mark.parametrize("timeout", [0, -1, 31, float("inf"), float("nan")])
def test_invalid_deadlines(timeout):
    with pytest.raises(InputError):
        verify_registry(REGISTRY, timeout=timeout)


def test_registry_duplicate_ids(tmp_path):
    data = load_registry(REGISTRY)
    data["sources"].append(data["sources"][0])
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(InputError):
        load_registry(path)


def test_cli_structural_output_and_refuses_overwrite_before_network(tmp_path, monkeypatch):
    output = tmp_path / "evidence.json"
    assert main(["registry", "--registry", str(REGISTRY), "--output", str(output)]) == 0
    assert json.loads(output.read_text())["mode"] == "structural-only"
    monkeypatch.setattr(
        "trust_skills.cli.verify_registry", lambda *a, **k: pytest.fail("network attempted")
    )
    before = output.read_bytes()
    assert main(["registry", "--registry", str(REGISTRY), "--live", "--output", str(output)]) == 2
    assert output.read_bytes() == before
