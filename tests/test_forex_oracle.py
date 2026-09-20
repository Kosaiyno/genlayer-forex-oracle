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
            obj.pair_latest_timestamp = TreeMap()
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
            
            # Extract current spot rate from prompt input
            rate = "1.147761"
            if "Verified Spot Rate: 1 EUR = " in prompt_input:
                rate = prompt_input.split("Verified Spot Rate: 1 EUR = ")[1].split(" ")[0]

            # Check if this is Round 2 (has historical delta)
            delta_bps = 0
            direction = "CONSOLIDATION"
            signal = "NEUTRAL"
            if "Delta: " in prompt_input and "bps" in prompt_input:
                try:
                    delta_str = prompt_input.split("Delta: ")[1].split("(")[1].split(" bps")[0]
                    delta_bps = int(delta_str)
                    if delta_bps >= 25:
                        direction = "UPWARD"
                        signal = "BULLISH"
                    elif delta_bps <= -25:
                        direction = "DOWNWARD"
                        signal = "BEARISH"
                except Exception:
                    pass

            return json.dumps({
                "round_id": 1,
                "pair": "EURUSD",
                "rate": rate,
                "baseline_rate": "1.145000" if delta_bps != 0 else rate,
                "delta_bps": delta_bps,
                "direction": direction,
                "macro_score": 0.0,
                "composite_score": round((delta_bps / 100.0) * 0.6, 2),
                "signal": signal,
                "confidence": 88,
                "evidence_quote": f"Verified Spot Rate: 1 EUR = {rate} USD, Delta: {delta_bps:+d} bps",
                "rationale": "Quantitatively evaluated via two-pillar framework combining basis point momentum and central bank yield differentials.",
                "status": "RESOLVED"
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
                    "time_last_update_utc": "Sat, 20 Sep 2026 00:02:31 +0000",
                    "time_last_update_unix": 1789862551,
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
        self.assertFalse(self.oracle.add_currency_pair("BTCUSD"))

    def test_empty_oracle_state(self):
        round_info = self.oracle.get_latest_round("EURUSD")
        self.assertIn("No oracle round recorded for EURUSD", round_info)
        self.assertEqual(self.oracle.get_price_e6("EURUSD"), 0)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 0)
        self.assertTrue(self.oracle.is_round_stale("EURUSD", 3600))

    def test_request_round_1_genesis_calibration(self):
        result = self.oracle.request_round("EURUSD")
        print("\n" + "="*65)
        print("GENESIS ORACLE ROUND 1 RESOLUTION:")
        print(result)
        print("="*65 + "\n")

        self.assertIn("EURUSD", result)
        self.assertIn("1.147761", result)
        self.assertIn("RESOLVED", result)

        # Verify state updates
        self.assertEqual(self.oracle.round_counter, 1)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 1)
        price_e6 = self.oracle.get_price_e6("EURUSD")
        self.assertEqual(price_e6, 1147761)

        # Verify latest round reader
        latest = self.oracle.get_latest_round("EURUSD")
        self.assertIn("1.147761", latest)

    def test_multi_round_historical_delta_lifecycle(self):
        # Execute Round 1 (calibrates genesis rate)
        res1 = self.oracle.request_round("EURUSD")
        self.assertEqual(self.oracle.round_counter, 1)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 1)

        # Execute Round 2 (retrieves Round 1 baseline, calculates delta)
        res2 = self.oracle.request_round("EURUSD")
        print("\n" + "="*65)
        print("ROUND 2 RESOLUTION WITH ON-CHAIN HISTORICAL DELTA:")
        print(res2)
        print("="*65 + "\n")

        self.assertEqual(self.oracle.round_counter, 2)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 2)

        # Verify both rounds exist permanently in historical archive
        r1 = self.oracle.get_round_by_id("EURUSD", 1)
        r2 = self.oracle.get_round_by_id("EURUSD", 2)
        self.assertIn("RESOLVED", r1)
        self.assertIn("RESOLVED", r2)

    def test_fails_safely_when_web_fetch_fails(self):
        gl_mock.nondet.web.should_fail = True
        with self.assertRaises(RuntimeError) as ctx:
            self.oracle.request_round("EURUSD")
        self.assertIn("Live market evidence fetch failed", str(ctx.exception))

    def test_untracked_pair_raises_error(self):
        with self.assertRaises(ValueError):
            self.oracle.request_round("UNTRACKED_PAIR")

if __name__ == "__main__":
    unittest.main()
