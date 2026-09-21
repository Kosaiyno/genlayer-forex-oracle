# Forex & Commodity AI Macro Oracle Intelligent Contract 📈🤖

A production-grade, multi-round **GenLayer Intelligent Contract** deployed on GenVM. It implements a structured oracle lifecycle for Foreign Exchange (EUR/USD, GBP/USD, USD/JPY) and Commodity (XAU/USD) markets, combining live dual-stream data acquisition (quantitative spot rates + live Yahoo Finance macro news feeds), on-chain historical baseline tracking, directional momentum evaluation, and 20-validator AI consensus.

---

## 🏛️ Dual-Stream Nondeterministic Ingestion (Zero Hard-Coded Data)

In direct response to GenLayer technical steward requirements, **ForexSentimentOracle** eliminates all static strings and performs live dual-stream evidence acquisition contract-side:

```
┌────────────────────────────────────────────────────────────────────────┐
│ STREAM 1: QUANTITATIVE SPOT RATE & MOMENTUM (60% Weight)               │
│ • Live Endpoint: gl.nondet.web.get("https://open.er-api.com/v6/latest") │
│ • Explicitly parses exact quote rate (e.g. USD = 1.147723)            │
│ • Retrieves previous round baseline from on-chain storage              │
│ • Computes delta_bps: ((current - baseline) / baseline) * 10,000       │
│ • Determines Momentum: UPWARD (>= +25 bps), DOWNWARD (<= -25 bps),     │
│   or CONSOLIDATION (-25 < delta < +25 bps)                             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ STREAM 2: LIVE ACQUIRED MACROECONOMIC EVIDENCE (40% Weight)            │
│ • Live Endpoint: gl.nondet.web.get("https://finance.yahoo.com/rss/...")│
│ • Dynamically fetches live, timestamped financial news headlines       │
│   discussing central bank monetary policy (Fed, ECB, BoE, BoJ)         │
│ • Zero Hard-Coding: All macro context is live and verified on-chain    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 20-VALIDATOR INDEPENDENT CONSENSUS (gl.eq_principle)                   │
│ • Validators independently verify both Stream 1 and Stream 2 payloads  │
│ • Grounding Rule: Signal cannot contradict quantitative momentum       │
│ • Verbatim Quotes Required: Outputs exact rate_quote and macro_quote   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ ON-CHAIN ROUND FINALIZATION & DEFI QUERY API                           │
│ • round_counter increments (Round 1, Round 2, Round 3...)              │
│ • Stores complete round record in oracle_rounds[pair:round_id]         │
│ • Pointers updated: pair_latest_round_id, pair_latest_rate_e6          │
│ • Public Getters: get_latest_round(), get_round_by_id(),               │
│   get_price_e6(), is_round_stale(), get_round_count()                  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 🧪 Testing & Verification

Run the automated test suite locally:

```bash
python3.14 tests/test_forex_oracle.py
```

Expected output:
```text
Ran 7 tests in 0.001s
OK
```

---

## 🚀 Deployed Contract & Studio Instructions

1. Open **GenLayer Studio**.
2. Paste `contracts/forex_sentiment_oracle.py` into `storage.py`.
3. Click **Deploy new instance**.
4. Under **Write Methods**, call `request_round("EURUSD")`.
5. Under **Read Methods**, call `get_latest_round("EURUSD")` and verify it contains both the live spot rate quote and the live acquired macro headline quote!
