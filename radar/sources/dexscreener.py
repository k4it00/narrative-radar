import time

from radar.util import get_json
from radar.model import Signal, tokens_of, STOP


def collect(window_days: int) -> list[Signal]:
    signals: list[Signal] = []
    for kind, url in (
        ("boosted", "https://api.dexscreener.com/token-boosts/latest/v1"),
        ("topboost", "https://api.dexscreener.com/token-boosts/top/v1"),
        ("newprofile", "https://api.dexscreener.com/token-profiles/latest/v1"),
    ):
        try:
            data = get_json(url)
            if not isinstance(data, list):
                continue
            n = 0
            for item in data:
                chain = (item.get("chainId") or "").lower()
                if chain != "solana":
                    continue
                tok = item.get("tokenAddress", "")
                desc = item.get("description") or ""
                signals.append(Signal(
                    source=f"dexscreener:{kind}",
                    title=f"dx:{kind}:sol:{tok[:10]}",
                    summary=f"DexScreener {kind} Solana token {tok} "
                            f"amount={item.get('amount', '?')} :: {desc[:200]}",
                    url=f"https://dexscreener.com/solana/{tok}",
                    ts=time.time(),
                    weight=round(1.2 if kind == "topboost" else 0.9, 2),
                    tokens=tokens_of(desc, STOP) | {tok[:8]} if tok else tokens_of(desc, STOP),
                ))
                n += 1
                if n >= 25:
                    break
        except Exception:
            continue
    return signals
