import json
import time

from radar.util import get_json
from radar.model import Signal, tokens_of, STOP

BASE = "https://superteam.fun"


def collect(window_days: int, agent_key: str | None = None) -> list[Signal]:
    signals: list[Signal] = []
    headers = {"Authorization": f"Bearer {agent_key}"} if agent_key else None
    urls = [
        (f"{BASE}/api/listings?take=20", "public"),
        (f"{BASE}/api/agents/listings/live?take=20", "agent"),
    ]
    for url, tag in urls:
        try:
            req = None
            from radar.util import http_get
            raw = http_get(url, headers)
            data = json.loads(raw.decode("utf-8", "replace"))
            rows = data.get("items") if isinstance(data, dict) else data
            if not isinstance(rows, list):
                continue
            for l in rows[:20]:
                title = l.get("title") or ""
                if not title:
                    continue
                slug = l.get("slug") or ""
                typ = l.get("type") or "listing"
                reward = l.get("rewardAmount") or l.get("rewardValue") or ""
                token = l.get("token") or ""
                skills = l.get("skills") or ""
                signals.append(Signal(
                    source="superteam-earn",
                    title=f"st:{title[:80]}",
                    summary=f"Superteam Earn {typ} '{title}' reward={reward}{token} "
                            f"skills={skills} :: what sponsors pay builders to ship right now",
                    url=f"https://superteam.fun/earn/listing/{slug}" if slug else BASE + "/earn",
                    ts=time.time(),
                    weight=1.1,
                    tokens=tokens_of(title + " " + str(skills), STOP),
                ))
            break
        except Exception:
            continue
    return signals
