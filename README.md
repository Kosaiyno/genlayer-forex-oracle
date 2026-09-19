# Forex & Commodity AI Sentiment Oracle Intelligent Contract 📈🤖

A production-grade, multi-round **GenLayer Intelligent Contract** deployed on GenVM. It implements a structured oracle lifecycle for Foreign Exchange (EUR/USD, GBP/USD, USD/JPY) and Commodity (XAU/USD) markets, combining live pair-specific data ingestion, on-chain historical baseline tracking, directional momentum evaluation, and 20-validator AI consensus.

---

## 🏛️ Structured Oracle Lifecycle Architecture

Unlike naive single-prompt contracts, **ForexSentimentOracle** implements a formal multi-round state machine:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & DATA RESOLUTION (gl.nondet.web.get)                     │
│    • Target Pair: Extracts exact Base & Quote rates (e.g. EUR -> USD)   │
│    • Zero Truncation: Explicitly parses full JSON payload              │
│    • Historical Baseline: Retrieves previous round rate from on-chain   │
│      storage (or genesis calibration if round #1)                      │
│    • Directional Momentum: Computes basis point delta (delta_bps) &   │
│      momentum direction (UPWARD / DOWNWARD / FLAT_CONSOLIDATION)       │
│    • Macro Context: Injects central bank monetary policy stance        │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. INDEPENDENT VALIDATOR CONSENSUS (gl.eq_principle)                   │
│    • 20 GenLayer validators independently evaluate the evidence        │
│    • Evidentiary Grounding Rule: Signals MUST strictly align with the  │
│      mathematical directional delta (e.g. negative bps cannot be BULLISH)│
│    • Exact Quote Extraction: Requires explicit timestamped rate quote  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ON-CHAIN ROUND FINALIZATION & ARCHIVE                               │
│    • Increments round_counter (Round 1, Round 2, Round 3...)           │
│    • Updates pair_latest_rate_e6 (scaled integer for DeFi consumption) │
│    • Stores complete round history in oracle_rounds[pair:round_id]     │
│    • Exposes consumer methods: get_latest_round(), get_round_by_id(),   │
│      get_price_e6(), and get_round_count()                             │
└────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Key Technical Features

1. **Pair-Specific Ingestion (Zero Truncation Omission)**:
   Explicitly parses target quote currencies directly from JSON objects. Avoids raw character slicing that drops alphabetic currency keys.
2. **On-Chain Historical Tracking & Directional Delta**:
   Maintains previous round rates in `pair_latest_rate_e6`. Every new round compares the live rate against this stored baseline, computing `delta_bps` (basis points) and momentum direction to quantitatively justify sentiment calls.
3. **Macroeconomic Monetary Context**:
   Synthesizes live rate deltas with central bank policy stances (ECB, Fed, BoE, BoJ) for robust macro analysis.
4. **Structured Multi-Round Storage**:
   Uses official GenLayer persistent types (`DynArray[str]`, `TreeMap[str, str]`, `u256`). Archives every historical round permanently on-chain.
5. **DeFi Consumer Ready**:
   Provides standard price getters (`get_price_e6`) returning integer-scaled prices ($10^6$) for direct consumption by lending protocols, perp DEXs, or automated vaults.

---

## 📂 Repository Layout

```text
genlayer-forex-oracle/
├── contracts/
│   └── forex_sentiment_oracle.py     # Pinned GenVM Intelligent Contract
├── tests/
│   └── test_forex_oracle.py          # Automated Unit Test Suite (7/7 Passing)
├── GENLAYER_CONTRACT_CHEATSHEET.md   # GenVM Development Reference
└── README.md                         # Protocol Documentation
```

---

## 🧪 Testing & Verification

Run the test suite locally with Python 3.14+:

```bash
python3.14 tests/test_forex_oracle.py
```

Expected output:
```text
Ran 7 tests in 0.000s
OK
```

---

## 🚀 Deployed Contract & Studio Instructions

1. Open **GenLayer Studio**.
2. Paste `contracts/forex_sentiment_oracle.py` into `storage.py`.
3. Click **Deploy new instance**.
4. Under **Write Methods**, call `request_oracle_update("EURUSD")`.
5. Under **Read Methods**, inspect `get_latest_round("EURUSD")` and `get_price_e6("EURUSD")`.
