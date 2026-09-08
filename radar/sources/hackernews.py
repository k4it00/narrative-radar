import time
import urllib.parse

from radar.util import get_json
from radar.model import Signal, tokens_of, STOP

API = "https://hn.algolia.com/api/v1"


def collect(window_days: int) -> list[Signal]:
    since = int(time.time() - window_days * 86400)
    signals: list[Signal] = []
    for q in ("solana", "solana agent", "solana depin", "jupiter exchange",
              "pump.fun", "jito", "solana program"):
        url = (
            f"{API}/search_by_date?query={urllib.parse.quote(q)}"
            f"&tags=story&numericFilters=created_at_i%3E{since}&hitsPerPage=15"
        )
        try:
            data = get_json(url)
            for hit in data.get("hits", []):
                title = hit.get("title") or ""
                url = hit.get("url") or ""
                blob = title.lower() + " " + url.lower()
                if not title or not any(
                        k in blob for k in ("solana", "jupiter", "jito", "pump.fun", "anchor", "sol/")):
                    continue
                signals.append(Signal(
                    source="hackernews",
                    title=f"hn:{title[:90]}",
                    summary=f"HN story ({hit.get('points', 0)} pts, "
                            f"{hit.get('num_comments', 0)} comments): {title}",
                    url=url or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                    ts=hit.get("created_at_i", time.time()),
                    weight=round(1.0 + min(hit.get("points", 0), 400) / 100.0, 2),
                    tokens=tokens_of(title, STOP),
                ))
        except Exception:
            continue
    return signals
