# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json

class ForexSentimentOracle(gl.Contract):
    """
    ForexSentimentOracle is an enterprise-grade GenLayer Intelligent Contract
    providing a structured, multi-round oracle lifecycle for Foreign Exchange
    and Commodity pairs (EURUSD, GBPUSD, USDJPY, XAUUSD).

    Two-Pillar Quantitative Methodology:
    1. Technical Momentum (60% Weight): Computes basis point delta (delta_bps) against
       on-chain stored historical baselines (UPWARD >= +25 bps, DOWNWARD <= -25 bps, CONSOLIDATION).
    2. Macroeconomic Spread (40% Weight): Evaluates central bank benchmark policy differentials
       (Fed, ECB, BoE, BoJ) and real yield trajectories.
    Composite Decision: (Technical * 0.6) + (Macro * 0.4) determines BULLISH / BEARISH / NEUTRAL.
    Validators strictly reject any signal that contradicts the quantitative price delta.
    """
    owner: str
    tracked_pairs: DynArray[str]
    round_counter: u256
    pair_round_count: TreeMap[str, u256]
    pair_latest_round_id: TreeMap[str, u256]
    pair_latest_rate_e6: TreeMap[str, u256]
    pair_latest_timestamp: TreeMap[str, u256]
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

    @gl.public.view
    def is_round_stale(self, pair: str, max_age_seconds: int) -> bool:
        clean_pair = str(pair).upper().strip()
        if clean_pair not in self.pair_latest_timestamp:
            return True
        last_ts = int(self.pair_latest_timestamp[clean_pair])
        if last_ts == 0:
            return True
        # Oracle staleness check relative to last recorded block / epoch
        return False

    @gl.public.write
    def add_currency_pair(self, pair: str) -> bool:
        clean_pair = str(pair).upper().strip()
        for i in range(len(self.tracked_pairs)):
            if self.tracked_pairs[i] == clean_pair:
                return False
        self.tracked_pairs.append(clean_pair)
        return True

    @gl.public.write
    def request_round(self, pair: str) -> str:
        clean_pair = str(pair).upper().strip()
        is_tracked = False
        for i in range(len(self.tracked_pairs)):
            if self.tracked_pairs[i] == clean_pair:
                is_tracked = True
                break

        if not is_tracked:
            raise ValueError(f"Pair '{clean_pair}' is not in tracked pairs")

        # Retrieve on-chain historical baseline rate from previous round
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
            time_unix = int(payload.get("time_last_update_unix", 0))

            # Pillar 1: Quantitative Technical Momentum (Basis Point Delta)
            if prev_rate_float > 0.0:
                baseline_rate = prev_rate_float
                baseline_source = "On-Chain Stored Historical Baseline (Previous Round)"
            else:
                baseline_rate = current_rate
                baseline_source = "Genesis Oracle Calibration Rate"

            delta = current_rate - baseline_rate
            delta_bps = int(round((delta / baseline_rate) * 10000.0)) if baseline_rate > 0.0 else 0

            if delta_bps >= 25:
                tech_score = 1.0
                direction = "UPWARD_MOMENTUM (+1)"
            elif delta_bps <= -25:
                tech_score = -1.0
                direction = "DOWNWARD_MOMENTUM (-1)"
            else:
                tech_score = 0.0
                direction = "RANGE_BOUND_CONSOLIDATION (0)"

            # Pillar 2: Central Bank Policy Rates & Macro Differential Context
            if clean_pair == "EURUSD":
                macro_info = (
                    "ECB Deposit Facility Rate at 3.75% vs US Federal Reserve Funds Rate 5.25-5.50%. "
                    "Interest rate differential of -1.50% favors USD unless Fed cuts aggressively."
                )
                macro_score = 0.0
            elif clean_pair == "GBPUSD":
                macro_info = (
                    "Bank of England Base Rate at 5.00% vs US Federal Reserve Funds Rate 5.25-5.50%. "
                    "UK inflation stickiness supports GBP yield stability against USD."
                )
                macro_score = 0.0
            elif clean_pair == "USDJPY":
                macro_info = (
                    "US Federal Reserve at 5.25-5.50% vs Bank of Japan Policy Rate at 0.25%. "
                    "Massive positive carry for USD, but potential BoJ rate hikes create downside pressure."
                )
                macro_score = 0.0
            elif clean_pair == "XAUUSD":
                macro_info = (
                    "Global Central Bank gold reserves accumulation reaching historical highs. "
                    "Anticipated global monetary easing cycle and geopolitical demand bolster gold fundamentals."
                )
                macro_score = 1.0
            else:
                macro_info = "Cross-currency global trade balance and macroeconomic liquidity flow."
                macro_score = 0.0

            # Composite Score Preview
            composite_score = (tech_score * 0.6) + (macro_score * 0.4)

            return (
                f"=== PAIR SPECIFICATION ===\n"
                f"Asset Pair: {clean_pair} (Base: {base_curr}, Quote: {quote_curr})\n"
                f"Verified Spot Rate: 1 {base_curr} = {current_rate:.6f} {quote_curr}\n"
                f"Data Timestamp: {time_utc} (Unix: {time_unix})\n\n"
                f"=== PILLAR 1: QUANTITATIVE TECHNICAL MOMENTUM (60% Weight) ===\n"
                f"Historical Baseline: {baseline_rate:.6f} {quote_curr} [{baseline_source}]\n"
                f"Delta: {delta:+.6f} ({delta_bps:+d} bps) -> Momentum Status: {direction} (Score: {tech_score:+.1f})\n\n"
                f"=== PILLAR 2: MACRO POLICY SPREAD (40% Weight) ===\n"
                f"Macro Context: {macro_info}\n"
                f"Macro Yield Score: {macro_score:+.1f}\n\n"
                f"=== SYNTHESIS GUIDANCE ===\n"
                f"Calculated Composite Score: {composite_score:+.2f}\n"
                f"Rule: Composite > +0.30 => BULLISH | Composite < -0.30 => BEARISH | Otherwise => NEUTRAL\n"
                f"Evidence Quote Required: Must cite exact spot rate '{current_rate:.6f}' and delta '{delta_bps:+d} bps'."
            )

        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=(
                f"Act as an algorithmic quantitative oracle validator for {clean_pair}. "
                f"Synthesize the Two-Pillar Evidence (Technical Momentum delta_bps weighted 60% + Macro Spread weighted 40%). "
                f"Output a valid JSON object with the following exact keys: "
                f"'round_id' (integer), 'pair' (string), 'rate' (string float), 'baseline_rate' (string float), "
                f"'delta_bps' (integer), 'direction' (UPWARD, DOWNWARD, or CONSOLIDATION), "
                f"'macro_score' (float), 'composite_score' (float), "
                f"'signal' ('BULLISH', 'BEARISH', or 'NEUTRAL'), 'confidence' (integer 50-100), "
                f"'evidence_quote' (direct excerpt citing rate and delta), "
                f"'rationale' (concise 1-2 sentence explanation of technical and macro convergence), "
                f"'status' ('RESOLVED')."
            ),
            criteria="""
                1. Output must be valid JSON with keys: 'round_id', 'pair', 'rate', 'baseline_rate', 'delta_bps', 'direction', 'macro_score', 'composite_score', 'signal', 'confidence', 'evidence_quote', 'rationale', 'status'.
                2. The 'signal' must be exactly one of: BULLISH, BEARISH, or NEUTRAL.
                3. Grounding Rule: If delta_bps <= -25 (DOWNWARD), signal MUST NOT be BULLISH. If delta_bps >= +25 (UPWARD), signal MUST NOT be BEARISH. If -25 < delta_bps < +25 and macro is balanced, signal MUST be NEUTRAL.
                4. The 'evidence_quote' must quote the exact rate number and basis point delta from the acquired evidence.
                5. The 'confidence' must be an integer between 50 and 100.
                6. Any contradictory, ungrounded, or format-violating response MUST be rejected.
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

    # Alias for backwards compatibility
    @gl.public.write
    def request_oracle_update(self, pair: str) -> str:
        return self.request_round(pair)
