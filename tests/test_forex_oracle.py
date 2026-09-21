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
            
            rate = "1.147723"
            pair = "EURUSD"
            macro_quote = "Hawkish Fed Supports DXY as EUR and GBP Struggle"

            if "Asset: XAUUSD" in prompt_input:
                pair = "XAUUSD"
                rate = "4340.900000"
                macro_quote = "Fidelity Sees Gold Climbing Toward $5,000"
            elif "Verified Spot Rate: 1 " in prompt_input:
                rate = prompt_input.split("Verified Spot Rate: 1 ")[1].split(" = ")[1].split(" ")[0]

            delta_bps = 0
            direction = "CONSOLIDATION"
            signal = "NEUTRAL"
            if "Calculated Delta: " in prompt_input and "bps" in prompt_input:
                try:
                    delta_str = prompt_input.split("Calculated Delta: ")[1].split("(")[1].split(" bps")[0]
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
                "pair": pair,
                "rate": rate,
                "baseline_rate": rate,
                "delta_bps": delta_bps,
                "direction": direction,
                "signal": signal,
                "confidence": 88,
                "rate_quote": f"Verified Spot Rate = {rate}",
                "macro_quote": macro_quote,
                "rationale": "Synthesized Stream 1 spot momentum with Stream 2 live acquired macroeconomic news.",
                "status": "RESOLVED"
            })

    class NonDet:
        class Web:
            def __init__(self):
                self.rate_fail = False

            def get(self, url):
                if self.rate_fail:
                    raise RuntimeError("HTTP 503 Service Unavailable")
                
                # Gold spot query (Binance Vision PAXG)
                if "PAXGUSDT" in url:
                    return MockWebResponse(json.dumps({
                        "symbol": "PAXGUSDT",
                        "price": "4340.90000000"
                    }))

                # Yahoo Finance RSS feeds
                if "yahoo.com" in url or "rss" in url:
                    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
                    <rss version="2.0">
                      <channel>
                        <title>Yahoo Finance</title>
                        <item>
                          <title>Hawkish Fed Supports DXY as EUR and GBP Struggle</title>
                          <pubDate>Mon, 21 Sep 2026 08:15:36 +0000</pubDate>
                        </item>
                        <item>
                          <title>Fidelity Sees Gold Climbing Toward $5,000</title>
                          <pubDate>Mon, 21 Sep 2026 06:30:00 +0000</pubDate>
                        </item>
                      </channel>
                    </rss>"""
                    return MockWebResponse(sample_rss)

                # Standard Fiat Exchange Rates (Open ER-API)
                return MockWebResponse(json.dumps({
                    "result": "success",
                    "base_code": "EUR",
                    "time_last_update_utc": "Mon, 21 Sep 2026 00:02:31 +0000",
                    "time_last_update_unix": 1789948951,
                    "rates": {
                        "USD": 1.147723,
                        "GBP": 0.858506,
                        "JPY": 156.918661
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
        gl_mock.nondet.web.rate_fail = False
        self.oracle = ForexSentimentOracle()

    def test_initialization(self):
        stats = self.oracle.get_oracle_stats()
        self.assertIn("Owner: 0x0000000000000000000000000000000000000000", stats)
        self.assertIn("Tracked Pairs: 4", stats)
        self.assertIn("Total Resolved Rounds: 0", stats)
        self.assertIn("EURUSD", self.oracle.get_tracked_pairs())
        self.assertIn("XAUUSD", self.oracle.get_tracked_pairs())

    def test_decimals_getter(self):
        self.assertEqual(self.oracle.get_decimals("EURUSD"), 6)
        self.assertEqual(self.oracle.get_decimals("XAUUSD"), 6)

    def test_add_currency_pair(self):
        res = self.oracle.add_currency_pair("AUDUSD")
        self.assertTrue(res)
        self.assertIn("AUDUSD", self.oracle.get_tracked_pairs())
        self.assertFalse(self.oracle.add_currency_pair("AUDUSD"))
        with self.assertRaises(ValueError):
            self.oracle.add_currency_pair("INVALID_SYMBOL_LEN")

    def test_fiat_pair_round_eurusd(self):
        result = self.oracle.request_round("EURUSD")
        print("\n" + "="*70)
        print("EURUSD ROUND (FIAT RESOLUTION):")
        print(result)
        print("="*70 + "\n")
        self.assertIn("EURUSD", result)
        self.assertIn("1.147723", result)
        self.assertIn("macro_quote", result)
        self.assertEqual(self.oracle.round_counter, 1)

    def test_commodity_gold_round_xauusd(self):
        result = self.oracle.request_round("XAUUSD")
        print("\n" + "="*70)
        print("XAUUSD ROUND (COMMODITY GOLD SPOT ROUTER):")
        print(result)
        print("="*70 + "\n")
        self.assertIn("XAUUSD", result)
        self.assertIn("4340.900000", result)
        self.assertIn("Gold", result)
        self.assertEqual(self.oracle.round_counter, 1)
        self.assertEqual(self.oracle.get_price_e6("XAUUSD"), 4340900000)

    def test_multi_round_historical_archive(self):
        self.oracle.request_round("EURUSD")
        self.oracle.request_round("EURUSD")
        self.assertEqual(self.oracle.round_counter, 2)
        self.assertEqual(self.oracle.get_round_count("EURUSD"), 2)
        r1 = self.oracle.get_round_by_id("EURUSD", 1)
        r2 = self.oracle.get_round_by_id("EURUSD", 2)
        self.assertIn("RESOLVED", r1)
        self.assertIn("RESOLVED", r2)

    def test_fails_safely_when_web_fails(self):
        gl_mock.nondet.web.rate_fail = True
        with self.assertRaises(RuntimeError):
            self.oracle.request_round("EURUSD")

if __name__ == "__main__":
    unittest.main()
