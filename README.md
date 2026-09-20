# Forex & Commodity AI Macro Oracle Intelligent Contract 📈🤖

A production-grade, multi-round **GenLayer Intelligent Contract** deployed on GenVM. It implements a structured oracle lifecycle for Foreign Exchange (EUR/USD, GBP/USD, USD/JPY) and Commodity (XAU/USD) markets, combining live pair-specific data ingestion, on-chain historical baseline tracking, two-pillar quantitative synthesis, and 20-validator AI consensus.

---

## 📐 Two-Pillar Quantitative Methodology

Rather than relying on ungrounded text prompts, **ForexSentimentOracle** evaluates market signals using an explicit mathematical framework:

### Pillar 1: Quantitative Technical Momentum (60% Weight)
Measures the directional rate change against on-chain historical baseline:
$$\Delta_{\text{bps}} = \frac{\text{Current Rate} - \text{Reference Baseline}}{\text{Reference Baseline}} \times 10,000$$

- $\Delta_{\text{bps}} \ge +25\text{ bps}$ (+0.25%): Technical Score = $+1.0$ (`UPWARD_MOMENTUM`)
- $\Delta_{\text{bps}} \le -25\text{ bps}$ (-0.25%): Technical Score = $-1.0$ (`DOWNWARD_MOMENTUM`)
- $-25\text{ bps} < \Delta_{\text{bps}} < +25\text{ bps}$: Technical Score = $0.0$ (`RANGE_BOUND_CONSOLIDATION`)

### Pillar 2: Central Bank Policy & Yield Spread (40% Weight)
Evaluates benchmark interest rate differentials:
- **EUR/USD**: ECB Deposit Rate (3.75%) vs US Fed Funds Rate (5.25-5.50%)
- **USD/JPY**: US Fed Funds Rate vs Bank of Japan Policy Rate (0.25%)
- **GBP/USD**: Bank of England Base Rate (5.00%) vs US Fed
- **XAU/USD**: Global Central Bank Gold Accumulation & Real Yield Trajectory
- Spread favors Base currency: Macro Score = $+1.0$
- Spread favors Quote currency: Macro Score = $-1.0$
- Neutral/balanced: Macro Score = $0.0$

### Composite Decision Matrix
$$\text{Composite Score} = (\text{Technical Score} \times 0.6) + (\text{Macro Score} \times 0.4)$$
- $\text{Composite} > +0.30 \implies \mathbf{BULLISH}$
- $\text{Composite} < -0.30 \implies \mathbf{BEARISH}$
- $-0.30 \le \text{Composite} \le +0.30 \implies \mathbf{NEUTRAL}$

### Strict Validator Grounding Rules (Equivalence Principle)
- If $\Delta_{\text{bps}} \le -25\text{ bps}$, signal **MUST NOT** be `BULLISH`.
- If $\Delta_{\text{bps}} \ge +25\text{ bps}$, signal **MUST NOT** be `BEARISH`.
- Output must explicitly cite the verbatim spot rate and basis point delta from the acquired evidence.

---

## 🏛️ Structured Multi-Round Oracle Lifecycle

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. INGESTION & DATA RESOLUTION (gl.nondet.web.get)                     │
│    • Target Pair: Extracts exact Base & Quote rates (e.g. EUR -> USD)   │
│    • Zero Truncation: Explicitly parses full JSON payload              │
│    • Historical Baseline: Retrieves previous round rate from on-chain   │
│      storage (or genesis calibration if round #1)                      │
│    • Directional Momentum: Computes basis point delta (delta_bps)      │
│    • Macro Spread: Injects central bank monetary policy differential   │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. INDEPENDENT VALIDATOR CONSENSUS (gl.eq_principle)                   │
│    • 20 GenLayer validators independently evaluate the evidence        │
│    • Strict Evidentiary Grounding: Signals contradictory to delta FAIL │
│    • Exact Quote Verification: Requires verbatim rate and delta quote  │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. ON-CHAIN ROUND FINALIZATION & ARCHIVE                               │
│    • Increments round_counter (Round 1, Round 2, Round 3...)           │
│    • Updates pair_latest_rate_e6 (scaled integer for DeFi consumption) │
│    • Stores complete round history in oracle_rounds[pair:round_id]     │
│    • Exposes consumer methods: get_latest_round(), get_round_by_id(),   │
│      get_price_e6(), is_round_stale(), and get_round_count()           │
└────────────────────────────────────────────────────────────────────────┘
```

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
Ran 7 tests in 0.001s
OK
```

---

## 🚀 Deployed Contract & Studio Instructions

1. Open **GenLayer Studio**.
2. Paste `contracts/forex_sentiment_oracle.py` into `storage.py`.
3. Click **Deploy new instance**.
4. Under **Write Methods**, call `request_round("EURUSD")`.
5. Under **Read Methods**, inspect `get_latest_round("EURUSD")` and `get_price_e6("EURUSD")`.
