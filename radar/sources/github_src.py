import json
import time

from radar.util import http_get
from radar.model import Signal, tokens_of, STOP

API = "https://api.github.com"


def collect(window_days: int, github_token: str | None = None) -> list[Signal]:
    since = time.strftime("%Y-%m-%d", time.gmtime(time.time() - window_days * 86400))
    headers = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
    signals: list[Signal] = []
    queries = [
        ("created", f"q=solana+created%3A%3E{since}&sort=stars&order=desc&per_page=15",
         "new repo"),
        ("pushed", f"q=solana+pushed%3A%3E{since}&sort=stars&order=desc&per_page=20",
         "active repo"),
        ("topics", "q=topic%3Asolana-agent&sort=updated&order=desc&per_page=10",
         "agent repo"),
        ("topics", "q=topic%3Asolana+topic%3Adefi&sort=updated&order=desc&per_page=10",
         "defi repo"),
        ("topics", "q=topic%3Asolana+topic%3Adepin&sort=updated&order=desc&per_page=10",
         "depin repo"),
        ("topics", "q=topic%3Aanchor-framework&sort=updated&order=desc&per_page=8",
         "anchor repo"),
        ("pushed", "q=solana+paymaster+pushed%3A%3E2026-06-01&sort=updated&per_page=8",
         "paymaster repo"),
    ]
    for kind, qs, note in queries:
        try:
            data = json.loads(http_get(f"{API}/search/repositories?{qs}", headers))
            for item in data.get("items", [])[:20]:
                repo = item.get("full_name", "")
                desc = item.get("description") or ""
                stars = item.get("stargazers_count", 0)
                pushed = item.get("pushed_at", "")
                created = item.get("created_at", "")
                summary = (
                    f"[{note}] {repo} stars={stars} pushed={pushed[:10]} "
                    f"created={created[:10]} :: {desc[:220]}"
                )
                w = 1.0 + min(stars, 2000) / 1000.0
                if kind == "created":
                    w += 1.5
                if pushed[:10] >= since:
                    w += 0.8
                signals.append(Signal(
                    source="github",
                    title=f"gh:{repo}",
                    summary=summary,
                    url=item.get("html_url", ""),
                    ts=time.time(),
                    weight=round(w, 2),
                    tokens=tokens_of(repo + " " + desc, STOP),
                ))
        except Exception as e:
            signals.append(Signal(
                source="github", title="gh:error", url="",
                summary=f"github query failed: {kind} {e}",
                ts=time.time(), weight=0.0, tokens=set(),
            ))
    return signals
