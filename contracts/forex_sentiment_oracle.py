# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing

class ForexSentimentOracle(gl.Contract):
    """
    ForexSentimentOracle is a GenLayer Intelligent Contract that leverages on-chain AI
    and the GenLayer Equivalence Principle to evaluate financial market sentiment.

    Validators independently verify proposed sentiment signals directly against acquired
    live market evidence, failing safely if live evidence is unavailable.
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
        independently verify sentiment signals against acquired market evidence.
        Fails safely if live evidence is unavailable.
        """
        clean_pair = str(pair).upper().strip()
        if clean_pair not in self.tracked_pairs:
            raise ValueError(f"Pair '{clean_pair}' is not tracked")

        def get_input() -> str:
            # Fetch live web data using GenLayer's non-deterministic web module
            base_curr = clean_pair[:3]
            url = f"https://open.er-api.com/v6/latest/{base_curr}"

            try:
                resp = gl.nondet.web.get(url)
                body_text = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
            except Exception as e:
                # Fail safely: raise exception when live market evidence is unavailable
                raise RuntimeError(f"Market evidence fetch failed for {clean_pair}: {str(e)}")

            if not body_text or len(body_text.strip()) == 0 or "rates" not in body_text:
                raise RuntimeError(f"Acquired market evidence for {clean_pair} is invalid or empty")

            return (
                f"Target Currency Pair: {clean_pair}\n"
                f"Acquired Live Market Evidence (Exchange Rate Data Payload):\n{body_text[:500]}\n\n"
                f"Instructions: Evaluate the sentiment signal for {clean_pair} derived strictly from this acquired market evidence."
            )

        # Leader node generates the evaluation using AI, and validators independently check signal against evidence
        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=(
                f"Act as a professional financial market validator. Analyze the acquired market evidence for {clean_pair}. "
                f"Evaluate whether the exchange rate data and macro factors support a BULLISH, BEARISH, or NEUTRAL signal. "
                f"Output a JSON object with keys: 'signal' (BULLISH, BEARISH, or NEUTRAL), 'confidence' (0-100), "
                f"'evidence_quote' (direct excerpt from acquired data), and 'rationale' (concise 1-2 sentence explanation)."
            ),
            criteria="""
                1. The response must be valid JSON with keys: 'signal', 'confidence', 'evidence_quote', and 'rationale'.
                2. The 'signal' must be exactly one of: BULLISH, BEARISH, or NEUTRAL.
                3. The 'signal' MUST be factually justified by and consistent with the acquired market evidence provided in the input; opposing or ungrounded signals MUST be rejected.
                4. The 'evidence_quote' field must contain a direct data point or quote from the acquired market evidence string.
                5. The 'confidence' must be an integer between 0 and 100 representing evidentiary alignment.
                6. The 'rationale' must concisely explain how the acquired market evidence justifies the signal.
            """,
        )

        # Record validated signal into persistent state
        analysis_str = str(raw_result)
        self.latest_signals[clean_pair] = analysis_str
        self.total_updates += 1

        return analysis_str
