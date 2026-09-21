# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
import json
import xml.etree.ElementTree as ET

class ForexSentimentOracle(gl.Contract):
    """
    ForexSentimentOracle is an enterprise-grade GenLayer Intelligent Contract
    implementing a structured multi-round oracle lifecycle for Foreign Exchange
    and Commodity pairs (EURUSD, GBPUSD, USDJPY, XAUUSD).

    Dual-Stream Nondeterministic Acquisition (Zero Hard-Coded Macro Data):
    1. Quantitative Spot Stream: Fetches live exchange rate payload via gl.nondet.web.get,
       parses exact quote rates, and computes basis point delta against on-chain stored baselines.
    2. Live Macro News Stream: Fetches real-time financial market headlines and central bank
       developments directly via gl.nondet.web.get (Yahoo Finance Macro Feeds).

    Validators independently verify that both the quantitative delta and cited macro headlines
    exist verbatim in the acquired evidence before finalizing state on-chain.
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

            # -----------------------------------------------------------------
            # STREAM 1: Nondeterministic Spot Rate & Baseline Acquisition
            # -----------------------------------------------------------------
            rate_url = f"https://open.er-api.com/v6/latest/{base_curr}"
            try:
                resp = gl.nondet.web.get(rate_url)
                rate_body = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
            except Exception as e:
                raise RuntimeError(f"Live market evidence fetch failed for {clean_pair}: {str(e)}")

            if not rate_body or len(rate_body.strip()) == 0:
                raise RuntimeError(f"Acquired spot rate payload for {clean_pair} is empty")

            try:
                rate_json = json.loads(rate_body)
            except Exception as e:
                raise RuntimeError(f"Failed to parse spot rate JSON for {clean_pair}: {str(e)}")

            rates = rate_json.get("rates", {})
            if quote_curr not in rates:
                raise RuntimeError(f"Target quote currency '{quote_curr}' not found in acquired exchange rates")

            current_rate = float(rates[quote_curr])
            rate_time_utc = str(rate_json.get("time_last_update_utc", "N/A"))
            rate_time_unix = int(rate_json.get("time_last_update_unix", 0))

            # Pillar 1 Quantitative Technical Momentum calculation
            if prev_rate_float > 0.0:
                baseline_rate = prev_rate_float
                baseline_source = "On-Chain Stored Historical Baseline (Previous Round)"
            else:
                baseline_rate = current_rate
                baseline_source = "Genesis Calibration Baseline"

            delta = current_rate - baseline_rate
            delta_bps = int(round((delta / baseline_rate) * 10000.0)) if baseline_rate > 0.0 else 0

            if delta_bps >= 25:
                direction = "UPWARD_MOMENTUM (+1)"
                tech_score = 1.0
            elif delta_bps <= -25:
                direction = "DOWNWARD_MOMENTUM (-1)"
                tech_score = -1.0
            else:
                direction = "RANGE_BOUND_CONSOLIDATION (0)"
                tech_score = 0.0

            # -----------------------------------------------------------------
            # STREAM 2: Nondeterministic Macroeconomic News & Central Bank Feed
            # -----------------------------------------------------------------
            symbol_map = {
                "EURUSD": "EURUSD=X",
                "GBPUSD": "GBPUSD=X",
                "USDJPY": "JPY=X",
                "XAUUSD": "GC=F"
            }
            macro_sym = symbol_map.get(clean_pair, f"{clean_pair}=X")
            news_url = f"https://finance.yahoo.com/rss/headline?s={macro_sym}"

            acquired_headlines = []
            try:
                news_resp = gl.nondet.web.get(news_url)
                news_xml = news_resp.body.decode("utf-8") if hasattr(news_resp, "body") else str(news_resp)
                if news_xml and "<item>" in news_xml:
                    root = ET.fromstring(news_xml)
                    for item in root.findall(".//item")[:3]:
                        t_node = item.find("title")
                        d_node = item.find("pubDate")
                        title_text = t_node.text.strip() if t_node is not None and t_node.text else ""
                        date_text = d_node.text.strip() if d_node is not None and d_node.text else ""
                        if title_text:
                            acquired_headlines.append(f"{date_text} | {title_text}")
            except Exception as e:
                acquired_headlines.append(f"Notice: Live macro news stream unavailable ({str(e)}). Proceeding with technical grounding.")

            macro_evidence_block = "\n".join([f"- {h}" for h in acquired_headlines]) if acquired_headlines else "- No current headlines reported."

            return (
                f"=== PAIR IDENTIFIER ===\n"
                f"Asset: {clean_pair} (Base: {base_curr}, Quote: {quote_curr})\n\n"
                f"=== STREAM 1: QUANTITATIVE RATE & MOMENTUM (60% Weight) ===\n"
                f"Verified Spot Rate: 1 {base_curr} = {current_rate:.6f} {quote_curr}\n"
                f"Rate Timestamp: {rate_time_utc} (Unix: {rate_time_unix})\n"
                f"Historical Baseline: {baseline_rate:.6f} {quote_curr} [{baseline_source}]\n"
                f"Calculated Delta: {delta:+.6f} ({delta_bps:+d} bps) -> Momentum: {direction}\n\n"
                f"=== STREAM 2: LIVE ACQUIRED MACROECONOMIC EVIDENCE (40% Weight) ===\n"
                f"Source URL: {news_url}\n"
                f"Acquired Live Macro Headlines:\n{macro_evidence_block}\n\n"
                f"=== VALIDATOR CRITERIA & SYNTHESIS RULES ===\n"
                f"1. Synthesize quantitative momentum delta_bps (60% weight) with live acquired macro headlines (40% weight).\n"
                f"2. Output valid JSON containing exact rate, delta_bps, direction, signal, confidence, verbatim rate quote, verbatim macro headline quote, and rationale.\n"
                f"3. Strict Grounding: If delta_bps <= -25 (DOWNWARD), signal MUST NOT be BULLISH. If delta_bps >= +25 (UPWARD), signal MUST NOT be BEARISH.\n"
                f"4. The macro_quote MUST be an exact excerpt from the Acquired Live Macro Headlines listed above."
            )

        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=(
                f"Act as an algorithmic quantitative oracle validator for {clean_pair}. "
                f"Synthesize the Dual-Stream Acquired Evidence (Stream 1 Technical Delta + Stream 2 Live Macro Headlines). "
                f"Output a valid JSON object with the following exact keys: "
                f"'round_id' (integer), 'pair' (string), 'rate' (string float), 'baseline_rate' (string float), "
                f"'delta_bps' (integer), 'direction' (UPWARD, DOWNWARD, or CONSOLIDATION), "
                f"'signal' ('BULLISH', 'BEARISH', or 'NEUTRAL'), 'confidence' (integer 50-100), "
                f"'rate_quote' (verbatim quote of rate and timestamp), "
                f"'macro_quote' (verbatim quote from acquired macro headlines), "
                f"'rationale' (concise 1-2 sentence explanation synthesizing rate momentum and acquired macro evidence), "
                f"'status' ('RESOLVED')."
            ),
            criteria="""
                1. Output must be valid JSON with keys: 'round_id', 'pair', 'rate', 'baseline_rate', 'delta_bps', 'direction', 'signal', 'confidence', 'rate_quote', 'macro_quote', 'rationale', 'status'.
                2. The 'signal' must be exactly one of: BULLISH, BEARISH, or NEUTRAL.
                3. Grounding Rule: If delta_bps <= -25 (DOWNWARD), signal MUST NOT be BULLISH. If delta_bps >= +25 (UPWARD), signal MUST NOT be BEARISH. If -25 < delta_bps < +25, signal must reflect live macro consensus or be NEUTRAL.
                4. The 'rate_quote' must quote the exact rate number from Stream 1.
                5. The 'macro_quote' must be a direct verbatim excerpt from the acquired Stream 2 headlines.
                6. The 'confidence' must be an integer between 50 and 100.
                7. Contradictory, ungrounded, or fabricated claims MUST be rejected.
            """,
        )

        result_str = str(raw_result)

        try:
            parsed = json.loads(result_str)
            rate_val = float(parsed.get("rate", 0.0))
        except Exception:
            rate_val = 0.0

        new_round_id = u256(int(self.round_counter) + 1)
        self.round_counter = new_round_id

        curr_pair_count = int(self.pair_round_count[clean_pair]) if clean_pair in self.pair_round_count else 0
        self.pair_round_count[clean_pair] = u256(curr_pair_count + 1)

        self.pair_latest_round_id[clean_pair] = new_round_id
        if rate_val > 0.0:
            self.pair_latest_rate_e6[clean_pair] = u256(int(round(rate_val * 1000000)))

        round_key = clean_pair + ":" + str(int(new_round_id))
        self.oracle_rounds[round_key] = result_str

        return result_str

    @gl.public.write
    def request_oracle_update(self, pair: str) -> str:
        return self.request_round(pair)
