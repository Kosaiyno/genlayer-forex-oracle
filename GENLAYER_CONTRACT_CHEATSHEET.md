# GenLayer Intelligent Contract Development Cheatsheet 📖⚡

Proven, 100% compliant rules and patterns for building production-ready GenLayer Intelligent Contracts.

---

## 1. Environment Header
Every contract MUST start with a pinned runner dependency header:
```python
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import typing
```

---

## 2. On-Chain Storage Declaration Rules

> [!IMPORTANT]
> - Standard Python `list` and `dict` are **ephemeral** and discarded after execution.
> - Use GenLayer storage collection types: **`DynArray[T]`**, **`TreeMap[K, V]`**, **`u256`**, **`str`**.
> - Storage fields MUST be declared as **class-level type annotations**.
> - Do NOT call `DynArray()` or `TreeMap()` in `__init__` (GenVM auto-instantiates them). Populate with `.append()` in `__init__`.

```python
class MyContract(gl.Contract):
    # Class-level storage field declarations
    owner: str
    items: DynArray[str]
    records: TreeMap[str, str]
    count: u256

    def __init__(self):
        self.owner = "0x0000000000000000000000000000000000000000"
        self.items.append("FirstItem")  # Populate via .append()
        self.count = u256(0)
```

---

## 3. Web Fetching & Safe Error Handling (`gl.nondet.web.get`)

Always fetch data inside non-deterministic blocks and **fail safely** if evidence is unavailable:

```python
def get_input() -> str:
    url = f"https://api.example.com/data/{key}"
    try:
        resp = gl.nondet.web.get(url)
        body_text = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
    except Exception as e:
        # Fail safely: raise exception when evidence is unavailable
        raise RuntimeError(f"Web evidence fetch failed for {key}: {str(e)}")

    if not body_text or "expected_key" not in body_text:
        raise RuntimeError(f"Acquired evidence for {key} is invalid")

    return f"Acquired Evidence:\n{body_text[:500]}"
```

---

## 4. Evidence-Grounded Validator Consensus (`gl.eq_principle.prompt_non_comparative`)

Validators must verify signals against acquired evidence (opposing or ungrounded signals must be rejected):

```python
raw_result = gl.eq_principle.prompt_non_comparative(
    get_input,
    task=(
        "Analyze the acquired evidence and output a JSON object with keys: "
        "'signal' (BULLISH, BEARISH, or NEUTRAL), 'confidence' (0-100), "
        "'evidence_quote' (direct quote from evidence), and 'rationale' (1-2 sentence explanation)."
    ),
    criteria="""
        1. Must be valid JSON with keys: 'signal', 'confidence', 'evidence_quote', 'rationale'.
        2. The 'signal' must be exactly BULLISH, BEARISH, or NEUTRAL.
        3. The 'signal' MUST be factually justified by acquired evidence; opposing signals MUST be rejected.
        4. The 'evidence_quote' field must contain a direct quote from the evidence.
        5. Confidence must be an integer between 0 and 100.
    """,
)
```

---

## 5. View Methods (`@gl.public.view`)
Return clean `str` or `list` representations for Studio RPC compatibility:

```python
@gl.public.view
def get_stats(self) -> str:
    return "Owner: " + str(self.owner) + " | Items: " + str(len(self.items)) + " | Count: " + str(self.count)
```
