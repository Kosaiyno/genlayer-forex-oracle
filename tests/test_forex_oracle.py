import sys
import os
import unittest
import json

class MockWebResponse:
    def __init__(self, body_text):
        self.body = body_text.encode("utf-8")

class DynArray(list):
    pass

class TreeMap(dict):
    pass

class u256(int):
    pass

class MockGL:
    class Contract:
        def __new__(cls, *args, **kwargs):
            obj = super().__new__(cls)
            obj.tracked_pairs = DynArray()
            obj.pair_round_count = TreeMap()
            obj.pair_latest_round_id = TreeMap()
            obj.pair_latest_rate_e6 = TreeMap()
            obj.oracle_rounds = TreeMap()
            obj.round_counter = u256(0)
            return obj

    class Public:
        def view(self, func):
            return func
        def write(self, func):
            return func

    class EqPrinciple:
        def prompt_non_comparative(self, get_input, task, criteria):
            prompt_input = get_input()
            # Extract current rate from prompt input to produce grounded response
            rate = "1.147761"
            if "1 EUR = " in prompt_input:
                rate = prompt_input.split("1 EUR = ")[1].split(" ")[0]
            
            return json.dumps({
                "signal": "BULLISH",
                "confidence": 88,
                "rate": rate,
                "delta_bps": 24,
                "direction": "UPWARD",
                "evidence_quote": f"rates.USD = {rate} at Sat, 19 Sep 2026 00:02:31 +0000",
                "rationale": "Upward momentum confirmed by basis point delta with favorable macroeconomic rate differentials."
            })

    class NonDet:
        class Web:
            def __init__(self):
                self.should_fail = False

            def get(self, url):
                if self.should_fail:
                    raise RuntimeError("HTTP 503 Service Unavailable")
                return MockWebResponse(json.dumps({
                    "result": "success",
                    "base_code": "EUR",
                    "time_last_update_utc": "Sat, 19 Sep 2026 00:02:31 +0000",
                    "rates": {
                        "USD": 1.147761,
                        "GBP": 0.858506,
                        "JPY": 180.272447
                    }
                }))

gl_mock = MockGL()
gl_mock.public = MockGL.Public()
gl_mock.eq_principle = MockGL.EqPrinciple()
gl_mock.nondet = MockGL.NonDet()
gl_mock.nondet.web = MockGL.NonDet.Web()
gl_mock.gl = gl_mock
gl_mock.Contract = MockGL.Contract
gl_mock.DynArray = DynArray
gl_mock.TreeMap = TreeMap
gl_mock.u256 = u256

sys.modules['genlayer'] = gl_mock

# Add contract directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'contracts'))
from forex_sentiment_oracle import ForexSentimentOracle

class TestForexSentimentOracle(unittest.TestCase):

    def setUp(self):
        gl_mock.nondet.web.should_fail = False
        self.oracle = ForexSentimentOracle()

    def test_initialization(self):
        stats = self.oracle.get_oracle_stats()
        self.assertIn("Owner: 0x0000000000000000000000000000000000000000", stats)
        self.assertIn("Tracked Pairs: 4", stats)
        self.assertIn("Total Resolved Rounds: 0", stats)
        self.assertIn("EURUSD", self.oracle.get_tracked_pairs())

    def test_add_currency_pair(self):
        res = self.oracle.add_currency_pair("BTCUSD")
        self.assertTrue(res)
        self.assertIn("BTCUSD", self.oracle.get_tracked_pairs())
        # Duplicate should return False
        self.assertFalse(self.oracle.add_currency_pair("BTCUSD"))

    def test_get_round_empty(self):
        round_info = self.oracle.get_latest_round("EURUSD")
        self.assertIn("No oracle round recorded for EURUSD", round_info)
        self.assertEqual(self.oracle.get_price_e6("EURUSD"), 0)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 0)

    def test_request_oracle_update_round_1_genesis(self):
        result = self.oracle.request_oracle_update("EURUSD")
        print("\n" + "="*65)
        print("ROUND 1 ORACLE RESOLUTION:")
        print(result)
        print("="*65 + "\n")

        self.assertIn("BULLISH", result)
        self.assertIn("1.147761", result)
        self.assertIn("evidence_quote", result)

        # Check state updates
        self.assertEqual(self.oracle.round_counter, 1)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 1)
        price_e6 = self.oracle.get_price_e6("EURUSD")
        self.assertEqual(price_e6, 1147761)

        # Check round query
        round_1_data = self.oracle.get_round_by_id("EURUSD", 1)
        self.assertIn("1.147761", round_1_data)

    def test_request_oracle_update_multi_round_lifecycle(self):
        # Round 1
        res1 = self.oracle.request_oracle_update("EURUSD")
        self.assertEqual(self.oracle.round_counter, 1)

        # Round 2 (uses Round 1 as historical on-chain baseline)
        res2 = self.oracle.request_oracle_update("EURUSD")
        print("\n" + "="*65)
        print("ROUND 2 ORACLE RESOLUTION (WITH HISTORICAL BASELINE):")
        print(res2)
        print("="*65 + "\n")

        self.assertEqual(self.oracle.round_counter, 2)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 2)

        # Verify historical archive contains both rounds
        r1 = self.oracle.get_round_by_id("EURUSD", 1)
        r2 = self.oracle.get_round_by_id("EURUSD", 2)
        self.assertTrue(len(r1) > 0)
        self.assertTrue(len(r2) > 0)

    def test_fails_safely_when_web_fetch_fails(self):
        gl_mock.nondet.web.should_fail = True
        with self.assertRaises(RuntimeError) as ctx:
            self.oracle.request_oracle_update("EURUSD")
        self.assertIn("Live market evidence fetch failed", str(ctx.exception))

    def test_untracked_pair_raises_error(self):
        with self.assertRaises(ValueError):
            self.oracle.request_oracle_update("UNKNOWNPAIR")

if __name__ == "__main__":
    unittest.main()
