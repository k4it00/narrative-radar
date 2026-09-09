#!/usr/bin/env python3
"""Hourly append-only collector for the Solana Narrative Radar.

Creates/appends (data/):
  signals.jsonl    every raw signal: {collected_at, source, title, summary, url, ts, weight, tokens}
  narratives.jsonl hourly cluster snapshot: {collected_at, n_live, clusters:[{score,n,srcs,top_tokens}]}
  market_1h.jsonl  SOL-basket last-closed 1h candle: {collected_at, px:{SYM:close}, vol:{SYM:qvol}}
Dedupe per (source,title) within the collection window via bounded state file.
Pre-registered hypotheses live in PRE_REGISTRATION.md (locked before any data existed).
Stdlib only (repo constraint). Read-only w.r.t. the rest of the repo.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from radar.cluster import cluster_signals  # noqa: E402
from radar.sources import (  # noqa: E402
    dexscreener, github_src, hackernews, news_rss, reddit_src, superteam_earn,
)

DATA = os.path.join(ROOT, "data")
STATE = os.path.join(DATA, "collector_state.json")
BASKET = ["SOLUSDT", "JUPUSDT", "JTOUSDT", "WIFUSDT", "1000BONKUSDT", "PYTHUSDT", "RAYUSDT", "TNSRUSDT"]
WINDOW_DAYS = 2


def try_gh_token():
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True,
                              timeout=10).stdout.strip() or None
    except Exception:
        return None


def load_state() -> dict:
    try:
        return json.load(open(STATE))
    except Exception:
        return {"seen_keys": [], "last_run": None}


def save_state(st: dict) -> None:
    st["seen_keys"] = st["seen_keys"][-80000:]
    json.dump(st, open(STATE, "w"))


def append_jsonl(path: str, rows: list[dict]) -> int:
    if not rows:
        return 0
    with open(path, "a") as f:
        for r in rows:
            f.write(json.dumps(r, default=str) + "\n")
    return len(rows)


def collect_signals() -> list[dict]:
    gh = try_gh_token()
    collectors = [
        ("github", lambda: github_src.collect(WINDOW_DAYS, gh)),
        ("hackernews", lambda: hackernews.collect(WINDOW_DAYS)),
        ("reddit", lambda: reddit_src.collect(WINDOW_DAYS)),
        ("dexscreener", lambda: dexscreener.collect(WINDOW_DAYS)),
        ("news", lambda: news_rss.collect(WINDOW_DAYS)),
        ("superteam-earn", lambda: superteam_earn.collect(WINDOW_DAYS)),
    ]
    out, st = [], load_state()
    seen = set(st["seen_keys"])
    now = datetime.now(timezone.utc).isoformat()
    for name, fn in collectors:
        try:
            for s in fn():
                key = f"{s.source}|{s.title}"
                if key in seen:
                    continue
                seen.add(key)
                d = s.to_dict()
                d["collected_at"] = now
                out.append(d)
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] FAILED: {e}")
    st["seen_keys"] = list(seen)[-80000:]
    st["last_run"] = now
    save_state(st)
    return out


def snapshot_narratives(signals: list[dict]) -> dict:
    from radar.model import Signal
    objs = [Signal(source=s["source"], title=s["title"], summary=s.get("summary", ""),
                   url=s.get("url", ""), ts=float(s["ts"]), weight=float(s["weight"]),
                   tokens=set(s.get("tokens") or [])) for s in signals]
    clusters = cluster_signals(objs)
    compact = []
    for nv in clusters:
        members = nv.get("signals") or []
        toks = nv.get("tokens")
        top = sorted(toks.keys())[:12] if isinstance(toks, dict) else sorted(toks or [])[:12]
        compact.append({
            "score": round(float(nv.get("score", 0.0)), 3),
            "n": int(nv.get("n_signals", len(members))),
            "srcs": sorted({getattr(sig, "source", "") for sig in members})[:8],
            "top_tokens": top,
        })
    return {"collected_at": datetime.now(timezone.utc).isoformat(),
            "n_live": len(objs), "clusters": compact[:40]}


def market_snapshot() -> dict:
    px, vol = {}, {}
    now = datetime.now(timezone.utc).isoformat()
    for sym in BASKET:
        try:
            url = f"https://fapi.binance.com/fapi/v1/klines?symbol={sym}&interval=1h&limit=2"
            k = json.loads(urllib.request.urlopen(url, timeout=10).read())
            if k:
                px[sym] = float(k[-2][4])   # last CLOSED candle
                vol[sym] = float(k[-2][7])  # quote volume
        except Exception as e:  # noqa: BLE001
            print(f"[mkt:{sym}] {e}")
    return {"collected_at": now, "px": px, "vol": vol}


def main() -> None:
    os.makedirs(DATA, exist_ok=True)
    t0 = time.time()
    sigs = collect_signals()
    n_sig = append_jsonl(os.path.join(DATA, "signals.jsonl"), sigs)
    nv = snapshot_narratives(sigs)
    append_jsonl(os.path.join(DATA, "narratives.jsonl"), [nv])
    mk = market_snapshot()
    append_jsonl(os.path.join(DATA, "market_1h.jsonl"), [mk])
    print(f"collected {n_sig} new signals | {len(nv['clusters'])} clusters | "
          f"{len(mk['px'])} basket prices | {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
