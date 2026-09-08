import re
import time
import xml.etree.ElementTree as ET

from radar.util import http_get
from radar.model import Signal, tokens_of, STOP

FEEDS = [
    ("cointelegraph", "https://cointelegraph.com/rss/tag/solana"),
    ("coindesk", "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml"),
]


def collect(window_days: int) -> list[Signal]:
    signals: list[Signal] = []
    for name, url in FEEDS:
        try:
            raw = http_get(url)
            root = ET.fromstring(raw)
            items = root.findall(".//item")
            if not items:
                items = root.findall(".//{*}item")
            for it in items[:20]:
                title = (it.findtext("title") or "").strip()
                desc = (it.findtext("description") or "").strip()
                link = (it.findtext("link") or "").strip()
                pub = (it.findtext("pubDate") or "").strip()
                if not title:
                    continue
                ts = time.time()
                for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
                    try:
                        from email.utils import parsedate_to_datetime
                        ts = parsedate_to_datetime(pub).timestamp()
                        break
                    except Exception:
                        pass
                if time.time() - ts > window_days * 86400 * 2:
                    continue
                clean = re.sub(r"<[^>]+>", " ", desc)
                blob = (title + " " + clean).lower()
                if name != "cointelegraph" and "solana" not in blob:
                    continue
                signals.append(Signal(
                    source=f"news:{name}",
                    title=f"nw:{title[:90]}",
                    summary=f"{name}: {title} :: {clean[:180]}",
                    url=link,
                    ts=ts,
                    weight=round(0.7 + (1.0 if "solana" in title.lower() else 0.0), 2),
                    tokens=tokens_of(title + " " + clean[:300], STOP),
                ))
        except Exception:
            continue
    return signals
