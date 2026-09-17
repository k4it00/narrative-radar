#!/usr/bin/env python3
"""H14/H15 meme-signal EV study — canonical runner.

Spec: narrative-radar/PRE_REGISTRATION.md APPENDIX 11 (locked 2026-09-17,
commit fd94bb8). This script implements that spec exactly. No parameter
tuning after results; implementation repairs to restore spec compliance must
be appended to REPAIRS and disclosed in the run log header.

Run:  /home/k4it0/Aegis_System/venv/bin/python studies/boost_ev_study.py
Smoke (plumbing only, no EV computed):  ... --smoke N_MINTS
"""

from __future__ import annotations

import argparse
import bisect
import datetime as dt
import hashlib
import json
import statistics
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / "data" / "signals.jsonl"
CACHE = ROOT / "studies" / "cache"
RESULTS = ROOT / "studies" / "results"
REPORT = ROOT / "reports" / "2026-09-17_boost_ev_study.md"

GT = "https://api.geckoterminal.com/api/v2"
UA = {"User-Agent": "kai-research/0.1 (narrative-radar H14/H15 study)"}

MIN_AGE_DAYS = 7
SLACK_S = 3600
HORIZONS = {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800}
COST_STD = 0.02
COST_GRID = (0.015, 0.02, 0.03)
POOL_AGE_SLACK_S = 7200
VOL_BUCKETS = [("lt10k", 0.0, 10_000.0), ("10k_100k", 10_000.0, 100_000.0), ("ge100k", 100_000.0, float("inf"))]
DEX_SOURCES = ("dexscreener:boosted", "dexscreener:topboost", "dexscreener:newprofile")
RATE_MIN_INTERVAL_S = 2.5
HTTP_TIMEOUT_S = 20
HTTP_ATTEMPTS = 4
FETCH_WORKERS = 6
REPAIRS: list[str] = [
    "pre-run (before canonical execution): collapse/DD windows exclude the exit candle (hourly lows after the exit open are future info; spec-intent fix, no parameter change)",
    "pre-run (before canonical execution, transport only): parallel fetch pool + dispatch limiter 24 req/min + per-mint FetchError isolation (fetch failures are excluded and reported, never counted as dead); measurement spec unchanged",
]


class FetchError(RuntimeError):
    pass


class _Limiter:
    def __init__(self, min_interval: float):
        self._lock = threading.Lock()
        self._interval = min_interval
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._next - now
            self._next = max(now, self._next) + self._interval
        if delay > 0:
            time.sleep(delay)


LIMITER = _Limiter(RATE_MIN_INTERVAL_S)

NETWORK_CALLS = 0
HTTP_ERRORS: list[str] = []


def mint_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def signal_class(source: str) -> str:
    return "newprofile" if source == "dexscreener:newprofile" else "boost"


def load_signals(path: Path, now_ts: float, min_age_days: int = MIN_AGE_DAYS) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {"boost": [], "newprofile": []}
    cutoff = now_ts - min_age_days * 86400
    seen: dict[tuple[str, str], float] = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            src = rec.get("source", "")
            if src not in DEX_SOURCES:
                continue
            ts = float(rec["ts"])
            if ts > cutoff:
                continue
            mint = mint_from_url(rec["url"])
            cls = signal_class(src)
            key = (mint, cls)
            if key not in seen or ts < seen[key]:
                seen[key] = ts
    for (mint, cls), ts in sorted(seen.items(), key=lambda kv: (kv[0][1], kv[1], kv[0][0])):
        out[cls].append({"mint": mint, "ts": ts, "source": "dexscreener:topboost" if cls == "boost" else "dexscreener:newprofile"})
    return out


def all_mints(sample: dict[str, list[dict]]) -> list[str]:
    return sorted({m["mint"] for cls in sample.values() for m in cls})


def _http_json(url: str) -> dict:
    global NETWORK_CALLS
    last_exc: Exception | None = None
    for attempt in range(HTTP_ATTEMPTS):
        if attempt:
            time.sleep(2.0 * attempt)
        LIMITER.wait()
        try:
            NETWORK_CALLS += 1
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last_exc = e
            if e.code == 404:
                return {"data": []}
            if e.code == 429:
                time.sleep(30)
                continue
        except Exception as e:
            last_exc = e
    HTTP_ERRORS.append(f"{url} :: {last_exc}")
    raise FetchError(f"{url} :: {last_exc}")


def fetch_cached(url: str, cache_file: Path) -> dict:
    if cache_file.exists():
        return json.loads(cache_file.read_text())
    data = _http_json(url)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(json.dumps(data))
    return data


def fetch_pools(mint: str) -> list[dict]:
    return fetch_cached(f"{GT}/networks/solana/tokens/{mint}/pools", CACHE / f"pools_{mint}.json").get("data", []) or []


def fetch_ohlcv(pool: str, before_ts: int) -> list[list]:
    url = f"{GT}/networks/solana/pools/{pool}/ohlcv/hour?before_timestamp={before_ts}&limit=220"
    data = fetch_cached(url, CACHE / f"ohlcv_{pool}_{before_ts}.json")
    return (data.get("data") or {}).get("attributes", {}).get("ohlcv_list", []) or []


def parse_iso(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def pick_pool(pools: list[dict], signal_ts: float) -> tuple[dict | None, bool]:
    parsed = []
    for p in pools:
        attrs = p.get("attributes", {})
        addr = p.get("id", "").split("_")[-1]
        if not addr:
            continue
        parsed.append(
            {
                "address": addr,
                "created_ts": parse_iso(attrs.get("pool_created_at")),
                "reserve_usd": float(attrs.get("reserve_in_usd") or 0.0),
            }
        )
    if not parsed:
        return None, False
    eligible = [p for p in parsed if p["created_ts"] is not None and p["created_ts"] <= signal_ts + POOL_AGE_SLACK_S]
    if eligible:
        return max(eligible, key=lambda p: p["reserve_usd"]), False
    return max(parsed, key=lambda p: p["reserve_usd"]), True


def compute_position(candles: list[list], signal_ts: float, horizons: dict[str, int]) -> dict:
    rows = sorted(([int(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])] for c in candles), key=lambda r: r[0])
    ts_list = [r[0] for r in rows]
    pos: dict = {"entry_open": None, "entry_vol_usd": None, "max_dd": None, "horizons": {}}
    if not rows:
        for h in horizons:
            pos["horizons"][h] = {"dead": True, "reason": "no_data", "gross": None}
        return pos
    i0 = bisect.bisect_left(ts_list, signal_ts)
    if i0 >= len(rows):
        for h in horizons:
            pos["horizons"][h] = {"dead": True, "reason": "no_entry_candle", "gross": None}
        return pos
    entry = rows[i0][1]
    pos["entry_open"] = entry
    pos["entry_vol_usd"] = rows[i0][5]
    i7 = bisect.bisect_left(ts_list, signal_ts + horizons["7d"])
    if not (i7 < len(rows) and ts_list[i7] <= signal_ts + horizons["7d"] + SLACK_S):
        i7 = len(rows)
    lows7 = [r[3] for r in rows[i0:i7]]
    pos["max_dd"] = (min(lows7) / entry - 1.0) if lows7 and entry > 0 else None
    for h, secs in horizons.items():
        target = signal_ts + secs
        i1 = bisect.bisect_left(ts_list, target)
        if i1 >= len(rows) or ts_list[i1] > target + SLACK_S:
            pos["horizons"][h] = {"dead": True, "reason": "no_exit_candle", "gross": None}
            continue
        window_lows = [r[3] for r in rows[i0:i1]]
        if entry > 0 and window_lows and min(window_lows) <= 0.01 * entry:
            pos["horizons"][h] = {"dead": True, "reason": "collapse_99", "gross": None}
            continue
        gross = rows[i1][1] / entry - 1.0
        pos["horizons"][h] = {"dead": False, "reason": None, "gross": gross}
    return pos


def bucket_of(vol_usd: float | None) -> str:
    if vol_usd is None:
        return "unknown"
    for name, lo, hi in VOL_BUCKETS:
        if lo <= vol_usd < hi:
            return name
    return "unknown"


def analyze(sample: dict[str, list[dict]], fetch_mints: list[str], smoke: bool = False) -> dict:
    pools_map: dict[str, list[dict]] = {}
    mint_errors: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        futs = {ex.submit(fetch_pools, m): m for m in fetch_mints}
        for done, fut in enumerate(as_completed(futs), 1):
            mint = futs[fut]
            try:
                pools_map[mint] = fut.result()
            except FetchError as e:
                mint_errors[mint] = str(e)
            if done % 25 == 0:
                print(f"[fetch1] {done}/{len(futs)} pool lists (errors={len(mint_errors)})", flush=True)
    picks: dict[tuple[str, str], tuple[dict | None, bool]] = {}
    ohlcv_jobs: set[tuple[str, int]] = set()
    for cls, sigs in sample.items():
        for s in sigs:
            mint, ts = s["mint"], s["ts"]
            if mint in mint_errors:
                continue
            pool, migration = pick_pool(pools_map.get(mint, []), ts)
            picks[(cls, mint)] = (pool, migration)
            if pool is not None:
                ohlcv_jobs.add((pool["address"], int(ts + HORIZONS["7d"] + SLACK_S)))
    jobs = sorted(ohlcv_jobs)
    ohlcv_map: dict[tuple[str, int], list] = {}
    ohlcv_failed: set[tuple[str, int]] = set()
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as ex:
        futs2 = {ex.submit(fetch_ohlcv, p, b): (p, b) for p, b in jobs}
        for done, fut in enumerate(as_completed(futs2), 1):
            key = futs2[fut]
            try:
                ohlcv_map[key] = fut.result()
            except FetchError:
                ohlcv_failed.add(key)
            if done % 25 == 0:
                print(f"[fetch2] {done}/{len(futs2)} ohlcv (errors={len(ohlcv_failed)})", flush=True)
    positions: list[dict] = []
    for cls, sigs in sample.items():
        for s in sigs:
            mint, ts = s["mint"], s["ts"]
            rec = {
                "class": cls,
                "source": s["source"],
                "mint": mint,
                "signal_ts": ts,
                "pool": None,
                "migration_risk": False,
                "dead_no_pool": False,
            }
            if mint in mint_errors:
                rec["fetch_error"] = mint_errors[mint]
            else:
                pool, migration = picks[(cls, mint)]
                rec["migration_risk"] = migration
                rec["dead_no_pool"] = pool is None
                if pool is None:
                    rec["horizons"] = {h: {"dead": True, "reason": "no_pool", "gross": None} for h in HORIZONS}
                    rec["max_dd"] = None
                    rec["entry_vol_usd"] = None
                else:
                    rec["pool"] = pool["address"]
                    rec["pool_reserve_usd"] = pool["reserve_usd"]
                    key = (pool["address"], int(ts + HORIZONS["7d"] + SLACK_S))
                    if key in ohlcv_failed:
                        rec["fetch_error"] = f"ohlcv {key[0]} @ {key[1]}"
                    else:
                        candles = ohlcv_map[key]
                        rec.update(compute_position(candles, ts, HORIZONS))
                        rec["candles"] = len(candles)
            if "horizons" not in rec:
                rec["horizons"] = {h: {"dead": True, "reason": "fetch_error", "gross": None} for h in HORIZONS}
                rec["max_dd"] = None
                rec["entry_vol_usd"] = None
            rec["bucket"] = bucket_of(rec.get("entry_vol_usd"))
            positions.append(rec)
    if smoke:
        return {
            "smoke": True,
            "mints": len(fetch_mints),
            "positions": len(positions),
            "fetch_errors": len({p["mint"] for p in positions if p.get("fetch_error")}),
            "network_calls": NETWORK_CALLS,
            "http_errors": HTTP_ERRORS,
        }
    return summarize(positions)


def net(gross: float | None, dead: bool, cost: float, all_in: bool) -> float | None:
    if gross is None:
        if dead and all_in:
            return max(-1.0, -1.0 - cost)
        return None
    return gross - cost


def _stats(vals: list[float]) -> dict:
    if not vals:
        return {"n": 0}
    vals_sorted = sorted(vals)
    return {
        "n": len(vals),
        "mean": statistics.mean(vals),
        "median": statistics.median(vals),
        "win_rate": sum(1 for v in vals if v > 0) / len(vals),
        "p10": vals_sorted[max(0, int(0.10 * (len(vals_sorted) - 1)))],
        "p90": vals_sorted[min(len(vals_sorted) - 1, int(0.90 * (len(vals_sorted) - 1)))],
    }


def summarize(positions: list[dict]) -> dict:
    out: dict = {"classes": {}, "positions": positions}
    for cls in ("boost", "newprofile"):
        allpos = [p for p in positions if p["class"] == cls]
        cpos = [p for p in allpos if not p.get("fetch_error")]
        cls_out: dict = {
            "n_signals": len(allpos),
            "n_fetch_errors": len(allpos) - len(cpos),
            "n_mints": len({p["mint"] for p in cpos}),
            "horizons": {},
        }
        dds = [p["max_dd"] for p in cpos if p.get("max_dd") is not None]
        for h in HORIZONS:
            tradeable = [p for p in cpos if not p["horizons"][h]["dead"]]
            allin = cpos
            t_net: dict[str, list[float]] = {str(c): [] for c in COST_GRID}
            a_net: dict[str, list[float]] = {str(c): [] for c in COST_GRID}
            gross_vals = [p["horizons"][h]["gross"] for p in tradeable]
            for c in COST_GRID:
                t_net[str(c)] = [p["horizons"][h]["gross"] - c for p in tradeable]
                a_net[str(c)] = [max(-1.0, (p["horizons"][h]["gross"] if not p["horizons"][h]["dead"] else -1.0) - c) for p in allin]
            reasons: dict[str, int] = {}
            for p in allin:
                if p["horizons"][h]["dead"]:
                    reasons[p["horizons"][h]["reason"]] = reasons.get(p["horizons"][h]["reason"], 0) + 1
            buckets: dict[str, dict] = {}
            for bname, _, _ in VOL_BUCKETS + [("unknown", 0, 0)]:
                bpos = [p for p in allin if p["bucket"] == bname]
                bt = [p for p in bpos if not p["horizons"][h]["dead"]]
                buckets[bname] = {
                    "n": len(bpos),
                    "mean_net_tradeable": statistics.mean([p["horizons"][h]["gross"] - COST_STD for p in bt]) if bt else None,
                    "dead_rate": (len(bpos) - len(bt)) / len(bpos) if bpos else None,
                }
            cls_out["horizons"][h] = {
                "tradeable_gross": _stats(gross_vals),
                "tradeable_net_std": _stats(t_net[str(COST_STD)]),
                "allin_net_std": _stats(a_net[str(COST_STD)]),
                "dead_rate": sum(1 for p in allin if p["horizons"][h]["dead"]) / len(allin) if allin else None,
                "dead_reasons": reasons,
                "cost_sensitivity_tradeable_mean": {c: (statistics.mean(t_net[str(c)]) if t_net[str(c)] else None) for c in COST_GRID},
                "cost_sensitivity_allin_mean": {c: (statistics.mean(a_net[str(c)]) if a_net[str(c)] else None) for c in COST_GRID},
                "buckets": buckets,
            }
        cls_out["mean_max_dd_7d"] = statistics.mean(dds) if dds else None
        cls_out["migration_risk_n"] = sum(1 for p in cpos if p.get("migration_risk"))
        boost_sources: dict[str, dict] = {}
        for src in ("dexscreener:boosted", "dexscreener:topboost"):
            spos = [p for p in cpos if p["source"] == src]
            if spos:
                h24 = [p["horizons"]["24h"] for p in spos]
                st = [p for p in spos if not p["horizons"]["24h"]["dead"]]
                boost_sources[src] = {
                    "n": len(spos),
                    "dead_rate_24h": sum(1 for x in h24 if x["dead"]) / len(spos),
                    "mean_net_24h_tradeable": statistics.mean([p["horizons"]["24h"]["gross"] - COST_STD for p in st]) if st else None,
                }
        cls_out["sources"] = boost_sources
        out["classes"][cls] = cls_out
    out["verdict"] = verdict(out)
    return out


def verdict(res: dict) -> dict:
    v: dict = {}
    for cls in ("boost", "newprofile"):
        c = res["classes"][cls]
        n_mints = c["n_mints"]
        all_neg = all(
            (c["horizons"][h]["tradeable_net_std"].get("mean") is not None and c["horizons"][h]["tradeable_net_std"]["mean"] < 0)
            for h in HORIZONS
        )
        cand = []
        for h in HORIZONS:
            s = c["horizons"][h]["tradeable_net_std"]
            if s.get("n", 0) >= 30 and s.get("mean") is not None and s["mean"] > 0.05 and s.get("median", -1) > 0:
                cand.append(h)
        if n_mints < 50:
            status = "INCONCLUSIVE"
        elif all_neg:
            status = "CONFIRMED_HARMFUL"
        elif cand:
            status = "CANDIDATE_EDGE"
        else:
            status = "MIXED"
        v[cls] = {"status": status, "candidate_horizons": cand, "n_mints": n_mints}
    return v


def git_hash() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def fmt_pct(x: float | None) -> str:
    return "n/a" if x is None else f"{100 * x:+.2f}%"


def report_md(res: dict, meta: dict) -> str:
    lines = [
        "# H14/H15 Meme-signal EV study — canonical run",
        "",
        f"- Run (UTC): {meta['started_utc']} -> {meta['ended_utc']}",
        f"- Spec: PRE_REGISTRATION.md APPENDIX 11 (locked fd94bb8). Script: studies/boost_ev_study.py @ {meta['git']}",
        f"- Sample: {meta['n_signals']} signals >=7d old ({meta['n_boost']} boost, {meta['n_newprofile']} newprofile), {meta['n_mints']} unique mints",
        f"- Network calls: {meta['network_calls']} | HTTP errors: {len(meta['http_errors'])}",
        f"- Repairs disclosed: {REPAIRS or 'none'}",
        "",
        "Cost standard = 2.00% round trip; sensitivity 1.50%/3.00% in JSON.",
        "",
    ]
    for cls in ("boost", "newprofile"):
        c = res["classes"][cls]
        v = res["verdict"][cls]
        lines += [
            f"## {cls.upper()} (H14)" if cls == "boost" else "## NEWPROFILE (H15)",
            "",
            f"n={c['n_signals']} signals / {c['n_mints']} mints (fetch-errors excluded: {c['n_fetch_errors']}) | mean maxDD(7d)={fmt_pct(c['mean_max_dd_7d'])} | migration-flagged: {c['migration_risk_n']}",
            "",
            "| horizon | n tradeable | dead% | gross mean | net mean (2%) | median net | win% | p10 net | p90 net | all-in mean (2%) |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        for h in HORIZONS:
            hs = c["horizons"][h]
            t = hs["tradeable_net_std"]
            g = hs["tradeable_gross"]
            a = hs["allin_net_std"]
            lines.append(
                f"| {h} | {t.get('n', 0)} | {fmt_pct(hs['dead_rate'])} | {fmt_pct(g.get('mean'))} | {fmt_pct(t.get('mean'))} | "
                f"{fmt_pct(t.get('median'))} | {fmt_pct(t.get('win_rate'))} | {fmt_pct(t.get('p10'))} | {fmt_pct(t.get('p90'))} | {fmt_pct(a.get('mean'))} |"
            )
        lines += ["", "Dead reasons (24h): " + json.dumps(c["horizons"]["24h"]["dead_reasons"]), ""]
        if c.get("sources"):
            lines += ["Source split (24h):", ""]
            for src, s in c["sources"].items():
                lines.append(f"- {src}: n={s['n']}, dead%={fmt_pct(s['dead_rate_24h'])}, mean net 24h={fmt_pct(s['mean_net_24h_tradeable'])}")
            lines.append("")
        lines += ["Volume buckets (tradeable mean net):", ""]
        hdr = "| bucket | " + " | ".join(f"{h} n/net" for h in HORIZONS) + " |"
        sep = "|---" * (len(HORIZONS) + 1) + "|"
        lines += [hdr, sep]
        for bname, _, _ in VOL_BUCKETS + [("unknown", 0, 0)]:
            cells = []
            for h in HORIZONS:
                b = c["horizons"][h]["buckets"].get(bname, {})
                cells.append(f"{b.get('n', 0)} / {fmt_pct(b.get('mean_net_tradeable'))}")
            lines.append(f"| {bname} | " + " | ".join(cells) + " |")
        lines += ["", f"**Verdict ({cls}): {v['status']}** (candidate horizons: {v['candidate_horizons'] or 'none'})", ""]
    lines += [
        "## Limitations (pre-stated in APPENDIX 11)",
        "",
        "- Hourly granularity; next-hourly-open entry models 0-60 min latency.",
        "- Flat round-trip cost understates thin-pool slippage; all results are best-case for a taker.",
        "- Pool reserve is read now, not point-in-time; entry-hour volume is the point-in-time activity proxy.",
        "- Migration-flagged tokens (chosen pool created after signal +2h) carry pool-identity risk.",
        "",
        "No trading, no wallet, no registration — research measurement only.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", type=int, default=0)
    ap.add_argument("--now", type=float, default=None)
    args = ap.parse_args()
    now = args.now if args.now is not None else time.time()
    started = dt.datetime.now(dt.timezone.utc)
    sample = load_signals(SIGNALS, now)
    mints = all_mints(sample)
    meta = {
        "started_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_hash(),
        "n_signals": sum(len(v) for v in sample.values()),
        "n_boost": len(sample["boost"]),
        "n_newprofile": len(sample["newprofile"]),
        "n_mints": len(mints),
    }
    if args.smoke:
        subset = set(mints[: args.smoke])
        sm = {cls: [s for s in sigs if s["mint"] in subset] for cls, sigs in sample.items()}
        res = analyze(sm, mints[: args.smoke], smoke=True)
        print(json.dumps(res, indent=2))
        return 0
    RESULTS.mkdir(parents=True, exist_ok=True)
    res = analyze(sample, mints)
    ended = dt.datetime.now(dt.timezone.utc)
    meta["ended_utc"] = ended.strftime("%Y-%m-%dT%H:%M:%SZ")
    meta["network_calls"] = NETWORK_CALLS
    meta["http_errors"] = HTTP_ERRORS
    res["meta"] = meta
    json_path = RESULTS / "boost_ev_2026-09-17.json"
    json_path.write_text(json.dumps(res, indent=2))
    with open(RESULTS / "positions_2026-09-17.jsonl", "w") as f:
        for p in res["positions"]:
            f.write(json.dumps(p) + "\n")
    REPORT.write_text(report_md(res, meta))
    print(json.dumps({"meta": meta, "verdict": res["verdict"]}, indent=2))
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
