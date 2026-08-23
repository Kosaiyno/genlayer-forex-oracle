# GenLayer Forex & Commodity Sentiment Oracle 📈🤖

An **Intelligent Smart Contract** built on [GenLayer](https://genlayer.com) that leverages on-chain AI and GenLayer's **Equivalence Principle** to perform consensus-validated financial market sentiment analysis for major Forex currency pairs and commodities (`EURUSD`, `GBPUSD`, `USDJPY`, `XAUUSD`).

---

## 🌟 Key Features

- **Live Web Data Fetching:** Natively calls live external market APIs/feeds using `gl.nondet.web.get(...)` inside non-deterministic blocks prior to LLM evaluation.
- **On-Chain AI Execution:** Evaluates macro sentiment, central bank monetary policy shifts, and technical momentum directly within smart contract state.
- **GenLayer Equivalence Principle:** Uses `gl.eq_principle.prompt_non_comparative` where validator nodes independently verify candidate AI sentiment evaluations against strict quality criteria before storing on-chain.
- **Deterministic Consensus:** Converts non-deterministic LLM reasoning into verifiable, deterministic on-chain data records (`BULLISH`, `BEARISH`, `NEUTRAL`, `confidence`, `rationale`).
- **Dynamic Asset Registry:** Owner can dynamically add new currency/commodity trading pairs (`add_currency_pair`).

---

## 🏗️ Architecture & Equivalence Principle

Unlike traditional EVM smart contracts that rely on external off-chain web2 oracles, GenLayer Intelligent Contracts run natively inside **GenVM** (Python 3.12+ execution environment). 

```
+------------------+         +-------------------------------+         +----------------------------+
| Contract Call    | ------> | Leader Node LLM Evaluation    | ------> | Validator Consensus Check  |
| update_sentiment |         | Generates raw market summary  |         | (prompt_non_comparative)   |
+------------------+         +-------------------------------+         +----------------------------+
                                                                                     |
                                                                                     v
                                                                       +----------------------------+
                                                                       | Verified Signal Stored     |
                                                                       | self.latest_signals[pair]  |
                                                                       +----------------------------+
```

### Equivalence Principle Method Used: `prompt_non_comparative`

```python
raw_result = gl.eq_principle.prompt_non_comparative(
    get_input,
    task="Act as a financial analyst... Output JSON with signal, confidence, rationale.",
    criteria="""
        Output must be valid JSON or clear key-value format.
        Signal must be BULLISH, BEARISH, or NEUTRAL.
        Confidence must be an integer between 0 and 100.
        Rationale must be a concise explanation (max 2 sentences).
    """
)
```

---

## 🚀 Quickstart & Testing

### 1. Prerequisites
- Python 3.12+
- `pytest` or Python `unittest`

### 2. Run Local Unit Tests
```bash
python tests/test_forex_oracle.py
```
*Output:*
```text
Ran 5 tests in 0.002s
OK
```

---

## 📜 Contract API Reference

### View Methods (`@gl.public.view`)
- `get_tracked_pairs() -> list[str]`: Returns list of monitored pairs.
- `get_signal(pair: str) -> dict`: Returns the latest validated sentiment record for a given pair.
- `get_all_signals() -> dict`: Returns all recorded signals.
- `get_stats() -> dict`: Returns oracle metadata (owner, pair count, total update count).

### Write Methods (`@gl.public.write`)
- `update_sentiment(pair: str) -> dict`: Triggers AI sentiment evaluation & validator consensus for `pair`.
- `add_currency_pair(pair: str) -> bool`: Registers a new currency/commodity pair.

---

## 🌐 Deploying to GenLayer

### Option A: GenLayer Studio (Browser)
1. Open [GenLayer Studio](https://studio.genlayer.com).
2. Copy contents of `contracts/forex_sentiment_oracle.py` into a new contract file.
3. Click **Deploy**.
4. Test calling `update_sentiment("EURUSD")`.

### Option B: GenLayer CLI
```bash
# Install CLI
npm install -g genlayer

# Lint contract syntax
genvm-lint check contracts/forex_sentiment_oracle.py

# Deploy to testnet
genlayer deploy contracts/forex_sentiment_oracle.py
```

---

## 🎖️ GenLayer Builder Program Submission

This repository was created as an **Intelligent Contract** contribution for the GenLayer Builders Program.

- **Builder Portal:** [points.genlayer.foundation](https://points.genlayer.foundation)
- **Category:** Intelligent Contract Deployment & Code Base
- **Contract Name:** `ForexSentimentOracle`
- **GenVM Spec:** `py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6`

---

## 📄 License
MIT License.
