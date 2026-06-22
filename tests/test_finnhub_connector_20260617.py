from __future__ import annotations

import unittest
from unittest.mock import patch

from core import finnhub_connector as fh


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None):
        self.calls.append((url, dict(params or {})))
        if not self.responses:
            raise AssertionError("No fake response left")
        return self.responses.pop(0)


class FinnhubConnectorTests(unittest.TestCase):
    def test_normalize_key_copy_paste_forms(self):
        token = "abcDEF1234567890"
        self.assertEqual(fh.normalize_api_key(f"  '{token}'  "), token)
        self.assertEqual(fh.normalize_api_key(f"token={token}"), token)
        self.assertEqual(fh.normalize_api_key(f"https://finnhub.io/api/v1/news?category=forex&token={token}"), token)
        self.assertEqual(fh.normalize_api_key(f"abc\u200bDEF\n1234567890"), token)

    def test_valid_forex_news_key_connects(self):
        client = FakeClient([FakeResponse(200, [])])
        with patch.object(fh, "_shared_http_client", return_value=client):
            result = fh.validate_connection("valid_token_123456")
        self.assertTrue(result["ok"])
        self.assertEqual(result["validation_endpoint"], "FOREX_NEWS")
        self.assertEqual(client.calls[0][1]["category"], "forex")

    def test_forex_403_falls_back_instead_of_rejecting_key(self):
        client = FakeClient([
            FakeResponse(403, {"error": "You don't have access to this resource"}),
            FakeResponse(200, [{"headline": "General item"}]),
        ])
        with patch.object(fh, "_shared_http_client", return_value=client):
            result = fh.validate_connection("valid_token_123456")
        self.assertTrue(result["ok"])
        self.assertEqual(result["validation_endpoint"], "GENERAL_NEWS")
        self.assertNotIn("rejected", result["message"].lower())

    def test_news_restricted_symbol_endpoint_can_validate_auth(self):
        client = FakeClient([
            FakeResponse(403, {"error": "Premium access required"}),
            FakeResponse(403, {"error": "Premium access required"}),
            FakeResponse(200, [{"symbol": "AAPL"}]),
        ])
        with patch.object(fh, "_shared_http_client", return_value=client):
            result = fh.validate_connection("valid_token_123456")
        self.assertTrue(result["ok"])
        self.assertEqual(result["availability"], "AUTHENTICATED")
        self.assertEqual(result["validation_endpoint"], "US_SYMBOLS")

    def test_invalid_key_message_stops_fallback(self):
        client = FakeClient([FakeResponse(401, {"error": "Invalid API key"})])
        with patch.object(fh, "_shared_http_client", return_value=client):
            result = fh.validate_connection("wrong_token_123456")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "AUTH_INVALID")
        self.assertEqual(len(client.calls), 1)

    def test_rate_limit_not_reported_as_invalid_key(self):
        client = FakeClient([
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
            FakeResponse(429, {"error": "API limit reached"}),
        ])
        with patch.object(fh, "_shared_http_client", return_value=client), patch.object(fh.time, "sleep", return_value=None):
            result = fh.validate_connection("valid_token_123456")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "RATE_LIMITED")
        self.assertNotIn("invalid", result["message"].lower())

    def test_fetch_forex_news_falls_back_to_general(self):
        client = FakeClient([
            FakeResponse(403, {"error": "Premium access required"}),
            FakeResponse(200, [{"id": 1, "headline": "EUR and USD update", "source": "Test"}]),
        ])
        state = {
            fh.KEY_STATE: "valid_token_123456",
            fh.CONNECTED_STATE: True,
            fh.NEWS_MODE_STATE: "forex",
            fh.NEWS_STATE: [],
            fh.NEWS_TIME_STATE: 0.0,
        }
        with patch.object(fh, "_shared_http_client", return_value=client), patch.object(fh.st, "session_state", state):
            rows = fh.fetch_market_news("forex", force=True)
        self.assertEqual(len(rows), 1)
        self.assertEqual(state[fh.NEWS_MODE_STATE], "general")
        self.assertTrue(state[fh.CONNECTED_STATE])


if __name__ == "__main__":
    unittest.main(verbosity=2)
