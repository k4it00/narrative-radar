import time
import xml.etree.ElementTree as ET

from radar.util import http_get
from radar.model import Signal, tokens_of, STOP

SUBS = ["solana", "CryptoCurrency"]


def collect(window_days: int) -> list[Signal]:
    signals: list[Signal] = []
    for sub in SUBS:
        try:
            raw = http_get(f"https://www.reddit.com/r/{sub}/.rss", retries=5)
            root = ET.fromstring(raw)
            entries = root.findall(".//{*}entry")
            for e in entries[:25]:
                title = (e.findtext("{*}title") or "").strip()
                link = (e.find(".//{*}link") or "")
                link = link.get("href", "") if link is not None else ""
                upd = (e.findtext("{*}updated") or "").strip()
                content = (e.findtext("{*}content") or "")
                ts = time.time()
                if upd:
                    try:
                        from datetime import datetime
                        ts = datetime.fromisoformat(
                            upd.replace("Z", "+00:00")).timestamp()
                    except Exception:
                        pass
                if not title or time.time() - ts > window_days * 86400 * 2:
                    continue
                signals.append(Signal(
                    source=f"reddit:r/{sub}",
                    title=f"rd:{title[:90]}",
                    summary=f"r/{sub}: {title} :: {(content or '')[:200]}",
                    url=link or f"https://reddit.com/r/{sub}",
                    ts=ts,
                    weight=0.9,
                    tokens=tokens_of(title + " " + content[:400], STOP),
                ))
        except Exception:
            continue
    return signals
