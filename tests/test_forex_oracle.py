import sys
import os
import unittest
from unittest.mock import MagicMock

# Create a stub/mock genlayer module for local unit testing if genlayer SDK is not installed
class MockWebResponse:
    def __init__(self, body_text):
        self.body = body_text.encode("utf-8")

class MockGL:
    class Contract:
        pass

    class Public:
        def view(self, func):
            return func
        def write(self, func):
            return func

    class EqPrinciple:
        def prompt_non_comparative(self, get_input, task, criteria):
            # Execute get_input to ensure web fetching and validation inside get_input is exercised
            prompt_input = get_input()
            return '{"signal": "BULLISH", "confidence": 85, "evidence_quote": "rates: USD 1.085", "rationale": "Strong macroeconomic indicators and hawkish rate trajectory."}'

    class NonDet:
        class Web:
            def __init__(self):
                self.should_fail = False

            def get(self, url):
                if self.should_fail:
                    raise RuntimeError("HTTP 500 Connection Refused")
                return MockWebResponse('{"result": "success", "base_code": "EUR", "rates": {"USD": 1.085}}')

gl_mock = MockGL()
gl_mock.public = MockGL.Public()
gl_mock.eq_principle = MockGL.EqPrinciple()
gl_mock.nondet = MockGL.NonDet()
gl_mock.nondet.web = MockGL.NonDet.Web()
gl_mock.gl = gl_mock
gl_mock.Contract = MockGL.Contract

sys.modules['genlayer'] = gl_mock

# Add contract directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'contracts'))
from forex_sentiment_oracle import ForexSentimentOracle

class TestForexSentimentOracle(unittest.TestCase):

    def setUp(self):
        gl_mock.nondet.web.should_fail = False
        self.oracle = ForexSentimentOracle()

    def test_initialization(self):
        stats = self.oracle.get_stats()
        self.assertIn("Owner: 0x0000000000000000000000000000000000000000", stats)
        self.assertIn("Pairs Count: 4", stats)
        self.assertIn("Total Updates: 0", stats)
        self.assertIn("EURUSD", self.oracle.get_tracked_pairs())

    def test_add_currency_pair(self):
        res = self.oracle.add_currency_pair("BTCUSD")
        self.assertTrue(res)
        self.assertIn("BTCUSD", self.oracle.get_tracked_pairs())

    def test_get_signal_empty(self):
        sig = self.oracle.get_signal("EURUSD")
        self.assertIn("No signal recorded for EURUSD", sig)

    def test_update_sentiment_success(self):
        result = self.oracle.update_sentiment("EURUSD")
        self.assertIn("BULLISH", result)
        self.assertIn("evidence_quote", result)
        
        # Verify state persistent update
        stored = self.oracle.get_signal("EURUSD")
        self.assertIn("BULLISH", stored)
        self.assertIn("Total Updates: 1", self.oracle.get_stats())

    def test_update_sentiment_fails_safely_when_web_fetch_fails(self):
        # Trigger simulated network/web fetch failure
        gl_mock.nondet.web.should_fail = True
        with self.assertRaises(RuntimeError) as ctx:
            self.oracle.update_sentiment("EURUSD")
        self.assertIn("Market evidence fetch failed", str(ctx.exception))

    def test_update_untracked_pair_raises_error(self):
        with self.assertRaises(ValueError):
            self.oracle.update_sentiment("UNKNOWNPAIR")

if __name__ == "__main__":
    unittest.main()
