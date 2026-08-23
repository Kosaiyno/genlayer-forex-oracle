# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing

class ForexSentimentOracle(gl.Contract):
    """
    ForexSentimentOracle is a GenLayer Intelligent Contract that leverages on-chain AI
    and the GenLayer Equivalence Principle to evaluate financial market sentiment.
    """

    def __init__(self):
        self.owner = "0x0000000000000000000000000000000000000000"
        self.tracked_pairs = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"]
        self.latest_signals = {}
        self.total_updates = 0

    @gl.public.view
    def get_tracked_pairs(self) -> list[str]:
        """Returns the list of currency/commodity pairs currently tracked by the oracle."""
        return self.tracked_pairs

    @gl.public.view
    def get_signal(self, pair: str) -> str:
        pair_key = str(pair).upper().strip()
        if pair_key in self.latest_signals:
            return str(self.latest_signals[pair_key])
        return "No signal recorded for " + pair_key

    @gl.public.view
    def get_all_signals(self) -> str:
        """Returns all recorded sentiment signals for all tracked pairs."""
        if not self.latest_signals:
            return "No signals recorded yet"
        return str(self.latest_signals)

    @gl.public.view
    def get_stats(self) -> str:
        """Returns contract health and operational metrics."""
        return "Owner: " + str(self.owner) + " | Pairs Count: " + str(len(self.tracked_pairs)) + " | Total Updates: " + str(self.total_updates)

    @gl.public.write
    def add_currency_pair(self, pair: str) -> bool:
        """
        Adds a new currency or commodity pair to the oracle tracking list.
        """
        clean_pair = str(pair).upper().strip()
        if clean_pair not in self.tracked_pairs:
            self.tracked_pairs.append(clean_pair)
            return True
        return False

    @gl.public.write
    def update_sentiment(self, pair: str) -> str:
        """
        Uses GenLayer's Equivalence Principle (prompt_non_comparative) to have validators
        run AI analysis on market sentiment for the requested currency pair, evaluate candidate
        outputs against consensus criteria, and store the validated signal on-chain.
        """
        clean_pair = str(pair).upper().strip()
        if clean_pair not in self.tracked_pairs:
            raise ValueError(f"Pair '{clean_pair}' is not tracked")

        def get_input() -> str:
            # Fetch live web data using GenLayer's non-deterministic web module
            try:
                base_curr = clean_pair[:3]
                url = f"https://open.er-api.com/v6/latest/{base_curr}"
                resp = gl.nondet.web.get(url)
                body_text = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
                web_data = f"Live FX Payload: {body_text[:300]}"
            except Exception:
                web_data = f"Live Market News Context for {clean_pair}"

            return (
                f"Perform a live market sentiment evaluation for the Forex/Commodity pair: {clean_pair}.\n"
                f"Fetched Web Context: {web_data}\n"
                f"Analyze fundamental drivers, central bank interest rate expectations, macro trends, "
                f"and technical momentum for {clean_pair} based on this live market data."
            )

        # Leader node generates the evaluation using AI, and validators check output against criteria
        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=(
                f"Act as a professional macro financial analyst. Evaluate current market sentiment for {clean_pair}. "
                f"Output a JSON string with key 'signal' (must be BULLISH, BEARISH, or NEUTRAL), "
                f"'confidence' (integer from 0 to 100), and 'rationale' (concise 1-2 sentence explanation)."
            ),
            criteria="""
                The response must be structured as valid JSON or clear key-value format.
                The signal field must be exactly one of: BULLISH, BEARISH, or NEUTRAL.
                The confidence field must be an integer between 0 and 100.
                The rationale field must be a clear financial explanation of at most 2 sentences.
            """,
        )

        # Record validated signal into persistent state
        analysis_str = str(raw_result)
        self.latest_signals[clean_pair] = analysis_str
        self.total_updates += 1

        return analysis_str
