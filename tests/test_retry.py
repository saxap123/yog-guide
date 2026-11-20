"""Unit tests for the retry logic of scraper/fetch.py. No network: the HTTP
session is a fake object and time.sleep is replaced, so tests run instantly.

Run:  python -m unittest discover -s tests -v     (from the yog-guide folder)
"""

import sys
import unittest
from pathlib import Path
from unittest import mock

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))
import fetch  # noqa: E402


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload if payload is not None else {"ok": True}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._payload


class FakeSession:
    """Returns / raises the scripted outcomes in order and records the calls."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.headers = {}
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append({"url": url, "params": dict(params), "timeout": timeout})
        o = self.outcomes.pop(0)
        if isinstance(o, Exception):
            raise o
        return o


class RetryTest(unittest.TestCase):
    def setUp(self):
        self.sleeps = []
        p1 = mock.patch.object(fetch.time, "sleep", side_effect=self.sleeps.append)
        p2 = mock.patch.object(fetch.random, "uniform", return_value=0.0)  # no polite pause
        p3 = mock.patch.object(fetch, "log")                               # quiet output
        for p in (p1, p2, p3):
            p.start()
            self.addCleanup(p.stop)

    def api(self, outcomes):
        s = FakeSession(outcomes)
        return fetch.Api(session=s), s

    def test_timeout_then_502_then_success(self):
        api, s = self.api([requests.Timeout("read timed out"), FakeResponse(502),
                           FakeResponse(200, {"query": {"x": 1}})])
        self.assertEqual(api.get(action="query"), {"query": {"x": 1}})
        self.assertEqual(len(s.calls), 3)
        self.assertEqual(self.sleeps, [2, 4])                     # backoff 2 s, then 4 s
        self.assertTrue(all(c["timeout"] == 30 for c in s.calls))  # 30 s timeout on each try
        self.assertEqual(s.calls[0]["params"]["format"], "json")

    def test_gives_up_after_five_retries(self):
        api, s = self.api([requests.Timeout("t"), FakeResponse(502), requests.Timeout("t"),
                           FakeResponse(502), requests.ConnectionError("c"), FakeResponse(502)])
        with self.assertRaises(RuntimeError) as cm:
            api.get(action="query")
        self.assertIn("gave up", str(cm.exception))
        self.assertEqual(len(s.calls), 6)                         # 1 try + 5 retries
        self.assertEqual(self.sleeps, [2, 4, 8, 16, 32])

    def test_429_and_maxlag_are_retried(self):
        api, s = self.api([FakeResponse(429),
                           FakeResponse(200, {"error": {"code": "maxlag", "info": "lag"}}),
                           FakeResponse(200, {"ok": 1})])
        self.assertEqual(api.get(action="query"), {"ok": 1})
        self.assertEqual(self.sleeps, [2, 4])

    def test_invalid_json_is_retried(self):
        bad = FakeResponse(200)
        bad.json = mock.Mock(side_effect=ValueError("not json"))   # e.g. HTML error page
        api, s = self.api([bad, FakeResponse(200, {"ok": 1})])
        self.assertEqual(api.get(action="query"), {"ok": 1})
        self.assertEqual(self.sleeps, [2])

    def test_real_api_error_is_not_retried(self):
        api, s = self.api([FakeResponse(200, {"error": {"code": "badvalue", "info": "x"}})])
        with self.assertRaises(RuntimeError):
            api.get(action="query")
        self.assertEqual(len(s.calls), 1)
        self.assertEqual(self.sleeps, [])

    def test_404_is_retried_as_http_error(self):
        # raise_for_status -> HTTPError (a RequestException) -> retried like other network errors
        api, s = self.api([FakeResponse(404), FakeResponse(200, {"ok": 1})])
        self.assertEqual(api.get(action="query"), {"ok": 1})
        self.assertEqual(self.sleeps, [2])

    def test_polite_pause_between_requests(self):
        fetch.random.uniform.return_value = 1.5
        api, s = self.api([FakeResponse(200, {"a": 1}), FakeResponse(200, {"b": 2})])
        with mock.patch.object(fetch.time, "monotonic", return_value=100.0):
            api.get(action="query")      # first call: last=0 -> no wait
            api.get(action="query")      # second call right after -> waits 1.5 s
        self.assertEqual(self.sleeps, [1.5])


if __name__ == "__main__":
    unittest.main()
