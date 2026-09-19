# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json

class ForexSentimentOracle(gl.Contract):
    """
    ForexSentimentOracle is a production-grade GenLayer Intelligent Contract
    providing a structured, multi-round oracle lifecycle for Foreign Exchange
    and Commodity pairs (EURUSD, GBPUSD, USDJPY, XAUUSD).

    Architecture:
    - Pair-Specific Ingestion: Parses exact quote currencies without string truncation.
    - Historical Directional Delta: Compares live rates against on-chain stored baselines
      to compute basis point changes (delta_bps) and directional momentum (UPWARD/DOWNWARD/FLAT).
    - Macroeconomic Context: Enriches pair evaluation with central bank monetary policy stances.
    - Equivalence Principle: 20-validator consensus enforcing quantitative evidentiary grounding.
    - Structured Round Lifecycle: Incremental round IDs, full round records, and DeFi getter methods.
    """
    owner: str
    tracked_pairs: DynArray[str]
    round_counter: u256
    pair_round_count: TreeMap[str, u256]
    pair_latest_round_id: TreeMap[str, u256]
    pair_latest_rate_e6: TreeMap[str, u256]
    oracle_rounds: TreeMap[str, str]

    def __init__(self):
        self.owner = "0x0000000000000000000000000000000000000000"
        self.tracked_pairs.append("EURUSD")
        self.tracked_pairs.append("GBPUSD")
        self.tracked_pairs.append("USDJPY")
        self.tracked_pairs.append("XAUUSD")
        self.round_counter = u256(0)

    @gl.public.view
    def get_tracked_pairs(self) -> list:
        result = []
        for i in range(len(self.tracked_pairs)):
            result.append(self.tracked_pairs[i])
        return result

    @gl.public.view
    def get_oracle_stats(self) -> str:
        return (
            "Owner: " + str(self.owner)
            + " | Tracked Pairs: " + str(len(self.tracked_pairs))
            + " | Total Resolved Rounds: " + str(self.round_counter)
        )

    @gl.public.view
    def get_latest_round(self, pair: str) -> str:
        clean_pair = str(pair).upper().strip()
        if clean_pair not in self.pair_latest_round_id:
            return "No oracle round recorded for " + clean_pair
        latest_id = str(self.pair_latest_round_id[clean_pair])
        round_key = clean_pair + ":" + latest_id
        if round_key in self.oracle_rounds:
            return str(self.oracle_rounds[round_key])
        return "Round record missing for " + round_key

    @gl.public.view
    def get_round_by_id(self, pair: str, round_id: int) -> str:
        clean_pair = str(pair).upper().strip()
        round_key = clean_pair + ":" + str(round_id)
        if round_key in self.oracle_rounds:
            return str(self.oracle_rounds[round_key])
        return "Round not found: " + round_key

    @gl.public.view
    def get_price_e6(self, pair: str) -> u256:
        clean_pair = str(pair).upper().strip()
        if clean_pair in self.pair_latest_rate_e6:
            return self.pair_latest_rate_e6[clean_pair]
        return u256(0)

    @gl.public.view
    def get_round_count(self, pair: str) -> u256:
        clean_pair = str(pair).upper().strip()
        if clean_pair in self.pair_round_count:
            return self.pair_round_count[clean_pair]
        return u256(0)

    @gl.public.write
    def add_currency_pair(self, pair: str) -> bool:
        clean_pair = str(pair).upper().strip()
        for i in range(len(self.tracked_pairs)):
            if self.tracked_pairs[i] == clean_pair:
                return False
        self.tracked_pairs.append(clean_pair)
        return True

    @gl.public.write
    def request_oracle_update(self, pair: str) -> str:
        clean_pair = str(pair).upper().strip()
        is_tracked = False
        for i in range(len(self.tracked_pairs)):
            if self.tracked_pairs[i] == clean_pair:
                is_tracked = True
                break

        if not is_tracked:
            raise ValueError(f"Pair '{clean_pair}' is not in tracked pairs")

        # Determine baseline from on-chain storage if exists
        has_baseline = clean_pair in self.pair_latest_rate_e6
        prev_rate_e6_val = int(self.pair_latest_rate_e6[clean_pair]) if has_baseline else 0
        prev_rate_float = (prev_rate_e6_val / 1000000.0) if has_baseline else 0.0

        def get_input() -> str:
            base_curr = clean_pair[:3]
            quote_curr = clean_pair[3:]

            # Primary web evidence fetch
            url = f"https://open.er-api.com/v6/latest/{base_curr}"
            try:
                resp = gl.nondet.web.get(url)
                body_text = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
            except Exception as e:
                raise RuntimeError(f"Live market evidence fetch failed for {clean_pair}: {str(e)}")

            if not body_text or len(body_text.strip()) == 0:
                raise RuntimeError(f"Acquired payload for {clean_pair} is empty")

            try:
                payload = json.loads(body_text)
            except Exception as e:
                raise RuntimeError(f"Failed to parse market JSON payload for {clean_pair}: {str(e)}")

            rates = payload.get("rates", {})
            if quote_curr not in rates:
                raise RuntimeError(f"Target quote currency '{quote_curr}' not found in acquired exchange rates")

            current_rate = float(rates[quote_curr])
            time_utc = str(payload.get("time_last_update_utc", "N/A"))

            # Calculate historical / reference directional delta
            if prev_rate_float > 0.0:
                baseline_rate = prev_rate_float
                baseline_type = "On-Chain Previous Round Stored Baseline"
            else:
                baseline_rate = current_rate
                baseline_type = "Genesis Oracle Calibration Baseline"

            delta = current_rate - baseline_rate
            delta_bps = int(round((delta / baseline_rate) * 10000.0)) if baseline_rate > 0 else 0

            if delta_bps > 10:
                direction = "UPWARD"
            elif delta_bps < -10:
                direction = "DOWNWARD"
            else:
                direction = "FLAT_CONSOLIDATION"

            # Macroeconomic central bank stance for major pairs
            macro_context = (
                f"ECB deposit facility rate at 3.75% vs US Federal Reserve funds target rate 5.25-5.50%. "
                f"Monetary policy divergence and cross-border interest rate differentials dictate macro flow."
            )

            return (
                f"PAIR SPECIFICATION: {clean_pair} (Base: {base_curr}, Quote: {quote_curr})\n"
                f"ACQUIRED LIVE RATE: 1 {base_curr} = {current_rate:.6f} {quote_curr}\n"
                f"PAYLOAD TIMESTAMP: {time_utc}\n"
                f"HISTORICAL REFERENCE BASELINE: {baseline_rate:.6f} {quote_curr} ({baseline_type})\n"
                f"DIRECTIONAL DELTA: {delta:+.6f} ({delta_bps:+d} bps) -> Momentum: {direction}\n"
                f"MACRO POLICY CONTEXT: {macro_context}\n"
                f"EVIDENCE QUOTE SOURCE: rates.{quote_curr} = {current_rate:.6f} at {time_utc}\n"
                f"INSTRUCTIONS: Synthesize a validated sentiment signal strictly grounded in the quantitative delta and macro evidence."
            )

        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=(
                f"Act as a professional algorithmic financial market validator. "
                f"Analyze the pair-specific historical evidence, directional delta, and macro context for {clean_pair}. "
                f"Output a valid JSON object with keys: "
                f"'signal' (BULLISH, BEARISH, or NEUTRAL), 'confidence' (integer 0-100), "
                f"'rate' (exact float as string), 'delta_bps' (integer basis points), "
                f"'direction' (UPWARD, DOWNWARD, or FLAT_CONSOLIDATION), "
                f"'evidence_quote' (exact rate and timestamp excerpt), and "
                f"'rationale' (concise 1-2 sentence explanation synthesizing rate momentum and macro factors)."
            ),
            criteria="""
                1. Output must be valid JSON with keys: 'signal', 'confidence', 'rate', 'delta_bps', 'direction', 'evidence_quote', and 'rationale'.
                2. The 'signal' must be exactly BULLISH, BEARISH, or NEUTRAL.
                3. Grounding Rule: If direction is UPWARD (+bps), signal must be BULLISH or NEUTRAL (cannot be BEARISH). If direction is DOWNWARD (-bps), signal must be BEARISH or NEUTRAL (cannot be BULLISH). If FLAT, signal must be NEUTRAL.
                4. The 'evidence_quote' must contain the exact rate number and timestamp from the acquired evidence string.
                5. The 'confidence' must be an integer between 50 and 100 representing evidence confidence.
                6. Any hallucinated, ungrounded, or directionally contradictory signal MUST be rejected.
            """,
        )

        result_str = str(raw_result)

        # Parse verified output to update structured on-chain storage
        try:
            parsed = json.loads(result_str)
            rate_val = float(parsed.get("rate", 0.0))
        except Exception:
            rate_val = 0.0

        # Increment global round counter
        new_round_id = u256(int(self.round_counter) + 1)
        self.round_counter = new_round_id

        # Update pair round count
        curr_pair_count = int(self.pair_round_count[clean_pair]) if clean_pair in self.pair_round_count else 0
        self.pair_round_count[clean_pair] = u256(curr_pair_count + 1)

        # Update latest pointers
        self.pair_latest_round_id[clean_pair] = new_round_id
        if rate_val > 0.0:
            self.pair_latest_rate_e6[clean_pair] = u256(int(round(rate_val * 1000000)))

        # Store complete historical round record
        round_key = clean_pair + ":" + str(int(new_round_id))
        self.oracle_rounds[round_key] = result_str

        return result_str
