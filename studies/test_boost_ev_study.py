"""Hermetic tests for the H14/H15 study (APPENDIX 11) — synthetic data only."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import boost_ev_study as m  # noqa: E402


def _mkpos(cls: str, mint: str, gross: float | None, dead: bool = False, reason: str | None = None) -> dict:
    horizons = {h: {"dead": dead, "reason": reason, "gross": None if dead else gross} for h in m.HORIZONS}
    return {
        "class": cls,
        "source": "dexscreener:boosted" if cls == "boost" else "dexscreener:newprofile",
        "mint": mint,
        "signal_ts": 0.0,
        "pool": "p",
        "migration_risk": False,
        "dead_no_pool": False,
        "entry_open": 1.0,
        "entry_vol_usd": 50_000.0,
        "bucket": "10k_100k",
        "max_dd": -0.2,
        "horizons": horizons,
    }


def test_load_signals_filters_dedupes(tmp_path: Path) -> None:
    now = 1_000_000_000.0
    old_boost = now - 8 * 86400
    old_prof = now - 9 * 86400
    recs = [
        {"source": "github", "url": "https://github.com/x/y", "ts": old_boost},
        {"source": "dexscreener:boosted", "url": "https://dexscreener.com/solana/MINTB", "ts": old_boost + 100},
        {"source": "dexscreener:boosted", "url": "https://dexscreener.com/solana/MINTB", "ts": old_boost},
        {"source": "dexscreener:newprofile", "url": "https://dexscreener.com/solana/MINTP", "ts": old_prof},
        {"source": "dexscreener:newprofile", "url": "https://dexscreener.com/solana/RECENT", "ts": now - 86400},
    ]
    p = tmp_path / "s.jsonl"
    p.write_text("\n".join(json.dumps(r) for r in recs))
    s = m.load_signals(p, now)
    assert [x["mint"] for x in s["boost"]] == ["MINTB"]
    assert s["boost"][0]["ts"] == old_boost
    assert [x["mint"] for x in s["newprofile"]] == ["MINTP"]
    assert len(s["newprofile"]) == 1


def test_pick_pool_prefers_pre_signal() -> None:
    pools = [
        {"id": "solana_AAA", "attributes": {"pool_created_at": "2026-01-01T00:00:00Z", "reserve_in_usd": "1000"}},
        {"id": "solana_BBB", "attributes": {"pool_created_at": "2026-09-17T06:00:00Z", "reserve_in_usd": "99999"}},
    ]
    import datetime as dt

    sig = dt.datetime(2026, 9, 17, 3, 0, tzinfo=dt.timezone.utc).timestamp()
    pool, mig = m.pick_pool(pools, sig)
    assert pool is not None and pool["address"] == "AAA" and mig is False
    pool2, mig2 = m.pick_pool([pools[1]], sig)
    assert pool2 is not None and pool2["address"] == "BBB" and mig2 is True
    assert m.pick_pool([], sig) == (None, False)


def test_compute_position_normal() -> None:
    candles = [
        [3600, 1.0, 1.2, 0.95, 1.1, 5000.0],
        [7200, 1.1, 1.3, 1.0, 1.25, 6000.0],
        [10800, 1.25, 1.4, 1.1, 1.3, 7000.0],
    ]
    pos = m.compute_position(candles, 3500.0, {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800})
    assert pos["entry_open"] == 1.0
    assert pos["horizons"]["1h"]["dead"] is False
    assert abs(pos["horizons"]["1h"]["gross"] - 0.1) < 1e-12
    assert pos["horizons"]["24h"]["dead"] is True and pos["horizons"]["24h"]["reason"] == "no_exit_candle"
    assert abs(pos["max_dd"] - (-0.05)) < 1e-12


def test_compute_position_no_entry_and_no_data() -> None:
    pos = m.compute_position([[1000, 1, 1, 1, 1, 1]], 5000.0, m.HORIZONS)
    assert pos["horizons"]["1h"]["reason"] == "no_entry_candle"
    pos2 = m.compute_position([], 5000.0, m.HORIZONS)
    assert pos2["horizons"]["1h"]["reason"] == "no_data"


def test_compute_position_collapse() -> None:
    candles = [
        [3600, 1.0, 1.0, 1.0, 1.0, 10.0],
        [7200, 1.0, 1.0, 0.001, 0.005, 10.0],
        [25200, 0.005, 0.006, 0.004, 0.005, 5.0],
    ]
    pos = m.compute_position(candles, 3500.0, {"1h": 3600, "6h": 21600, "24h": 86400, "7d": 604800})
    assert pos["horizons"]["6h"]["dead"] is True and pos["horizons"]["6h"]["reason"] == "collapse_99"
    assert pos["horizons"]["1h"]["dead"] is False


def test_bucket_of() -> None:
    assert m.bucket_of(9999) == "lt10k"
    assert m.bucket_of(10000) == "10k_100k"
    assert m.bucket_of(99999) == "10k_100k"
    assert m.bucket_of(100000) == "ge100k"
    assert m.bucket_of(None) == "unknown"


def test_summarize_verdict_confirmed_harmful() -> None:
    positions = [_mkpos("boost", f"M{i:03d}", -0.2) for i in range(60)]
    res = m.summarize(positions)
    assert res["verdict"]["boost"]["status"] == "CONFIRMED_HARMFUL"
    assert res["classes"]["boost"]["horizons"]["24h"]["tradeable_net_std"]["mean"] < 0


def test_summarize_verdict_candidate_edge() -> None:
    positions = [_mkpos("newprofile", f"P{i:03d}", 0.10) for i in range(60)]
    res = m.summarize(positions)
    assert res["verdict"]["newprofile"]["status"] == "CANDIDATE_EDGE"
    assert "24h" in res["verdict"]["newprofile"]["candidate_horizons"]


def test_summarize_verdict_inconclusive() -> None:
    positions = [_mkpos("boost", f"M{i:03d}", -0.2) for i in range(10)]
    res = m.summarize(positions)
    assert res["verdict"]["boost"]["status"] == "INCONCLUSIVE"


def test_summarize_dead_all_in_floor() -> None:
    positions = [_mkpos("boost", "MD", None, dead=True, reason="no_pool") for _ in range(60)]
    res = m.summarize(positions)
    a = res["classes"]["boost"]["horizons"]["24h"]["allin_net_std"]
    assert a["n"] == 60
    assert abs(a["mean"] - (-1.0)) < 1e-12
    assert res["classes"]["boost"]["horizons"]["24h"]["dead_rate"] == 1.0


def test_report_md_renders() -> None:
    positions = [_mkpos("boost", f"M{i:03d}", 0.05) for i in range(60)]
    res = m.summarize(positions)
    meta = {
        "started_utc": "x",
        "ended_utc": "y",
        "git": "abc",
        "n_signals": 60,
        "n_boost": 60,
        "n_newprofile": 0,
        "n_mints": 60,
        "network_calls": 0,
        "http_errors": [],
    }
    md = m.report_md(res, meta)
    assert "H14" in md and "Verdict" in md and "Limitations" in md
