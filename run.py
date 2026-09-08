import argparse
import json
import os
import subprocess
import time

from radar.sources import github_src, hackernews, reddit_src, dexscreener, news_rss
from radar.sources import superteam_earn
from radar.cluster import cluster_signals
from radar.ideas import generate_ideas
from radar.report import write_markdown, write_dashboard

ROOT = os.path.dirname(os.path.abspath(__file__))


def try_gh_token() -> str | None:
    try:
        tok = subprocess.run(["gh", "auth", "token"], capture_output=True,
                             text=True, timeout=10).stdout.strip()
        return tok or None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window-days", type=int, default=14)
    args = ap.parse_args()

    t0 = time.time()
    gh = try_gh_token()
    collectors = [
        ("github", lambda: github_src.collect(args.window_days, gh)),
        ("hackernews", lambda: hackernews.collect(args.window_days)),
        ("reddit", lambda: reddit_src.collect(args.window_days)),
        ("dexscreener", lambda: dexscreener.collect(args.window_days)),
        ("news", lambda: news_rss.collect(args.window_days)),
        ("superteam-earn", lambda: superteam_earn.collect(args.window_days)),
    ]
    all_signals = []
    sources_used = []
    for name, fn in collectors:
        try:
            sigs = fn()
            live = [s for s in sigs if s.weight > 0]
            all_signals.extend(sigs)
            if live:
                sources_used.append(name)
            print(f"[{name}] {len(live)} signals")
        except Exception as e:
            print(f"[{name}] FAILED: {e}")

    seen = set()
    deduped = []
    for s in all_signals:
        key = (s.source, s.url or s.title)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    all_signals = deduped

    narratives = cluster_signals(all_signals)
    ideas_by_rank = {nv["rank"]: generate_ideas(nv) for nv in narratives}

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
    with open(os.path.join(ROOT, "data", "signals.json"), "w") as f:
        json.dump([s.to_dict() for s in all_signals], f, indent=1)

    stamp = time.strftime("%Y-%m-%d")
    md_path = os.path.join(ROOT, "reports", f"{stamp}_fortnight.md")
    write_markdown(narratives, ideas_by_rank, md_path, sources_used)
    write_dashboard(narratives, ideas_by_rank, sources_used,
                    os.path.join(ROOT, "site"))

    print(f"narratives: {len(narratives)} | ideas tied: {sum(len(v) for v in ideas_by_rank.values())}")
    print(f"report: {md_path}")
    print(f"elapsed: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
