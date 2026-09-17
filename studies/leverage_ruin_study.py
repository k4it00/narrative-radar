#!/usr/bin/env python3
"""R1/R2 leverage ruin + Kelly study — canonical runner.

Spec: narrative-radar/PRE_REGISTRATION.md APPENDIX 12 (locked 2026-09-17,
commit 8988718). Math only; no trading, no wallet.

Run: /home/k4it0/Aegis_System/venv/bin/python studies/leverage_ruin_study.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = Path("/home/k4it0/Aegis_System/data/SOLUSDT_1h_2020_2026.csv")
RESULTS = ROOT / "studies" / "results"
REPORT = ROOT / "reports" / "2026-09-17_leverage_ruin_study.md"

SEED = 20260917
N_PATHS = 10_000
BLOCK_H = 24
HOURS_YEAR = 8760
HORIZONS = {"30d": 720, "90d": 2160, "365d": 8760}
LEVERAGES = (1, 2, 3, 5, 10)
MUS = (-0.20, 0.0, 0.20, 0.50)
MODES = ("fixed", "rebalanced")
E0 = 500.0
FEE_RT_SIDE = 0.0005 + 0.0002
MM = 0.005
CHUNK = 1000
LOW_EQUITY = 50.0
REPAIRS: list[str] = []


def load_series(path: Path) -> tuple[np.ndarray, np.ndarray]:
    import csv

    rets: list[float] = []
    fund: list[float] = []
    prev_close: float | None = None
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            close = float(row["close"])
            if prev_close is not None and prev_close > 0 and close > 0:
                rets.append(float(np.log(close / prev_close)))
                fr = row.get("funding_rate") or ""
                fund.append(float(fr) if fr not in ("", "None") else 0.0)
            prev_close = close
    return np.array(rets, dtype=np.float64), np.array(fund, dtype=np.float64)


def annualized_sigma(hourly_rets: np.ndarray) -> float:
    return float(np.std(hourly_rets, ddof=1) * np.sqrt(HOURS_YEAR))


def kelly_fraction(mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 0.0
    return mu / (sigma * sigma)


def draw_blocks(rng: np.random.Generator, ret: np.ndarray, fund: np.ndarray, n_paths: int, hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Bootstrap contiguous 24h blocks; funding kept only on stamp hours (abs j % 8 == 0)."""
    n_blocks = hours // BLOCK_H
    max_start = len(ret) - BLOCK_H - 1
    starts = rng.integers(0, max_start, size=(n_paths, n_blocks))
    offs = np.arange(BLOCK_H)
    base = starts[:, :, None] + offs[None, None, :]
    idx = base.reshape(n_paths, hours)
    r = ret[idx]
    f = np.zeros((n_paths, hours), dtype=np.float64)
    first = (-starts) % 8
    block_ids = np.arange(n_blocks)[None, :]
    rows = np.arange(n_paths)[:, None]
    for k in (0, 8, 16):
        pos = first + k
        ok = pos < BLOCK_H
        abs_idx = starts + np.where(ok, pos, 0)
        flat = block_ids * BLOCK_H + np.where(ok, pos, 0)
        f[rows, flat] = np.where(ok, fund[abs_idx], 0.0)
    return r, f


def simulate_fixed(r_hourly: np.ndarray, f_hourly: np.ndarray, leverage: int, e0: float = E0) -> dict[str, np.ndarray]:
    n0 = e0 * leverage
    price = np.exp(np.cumsum(r_hourly, axis=1))
    cumfund = np.cumsum(f_hourly, axis=1) * n0
    equity = e0 - n0 * FEE_RT_SIDE + n0 * (price - 1.0) - cumfund
    liq = equity <= MM * n0
    liq_hour = np.where(liq.any(axis=1), liq.argmax(axis=1) + 1, np.inf)
    out: dict[str, np.ndarray] = {}
    for hname, h in HORIZONS.items():
        eq_h = equity[:, h - 1].copy()
        eq_h = np.where(liq_hour <= h, 0.0, np.maximum(eq_h - n0 * FEE_RT_SIDE, 0.0))
        out[hname] = eq_h
    out["liq_hour"] = liq_hour
    return out


def simulate_rebalanced(r_hourly: np.ndarray, f_hourly: np.ndarray, leverage: int, e0: float = E0) -> dict[str, np.ndarray]:
    n_paths, hours = r_hourly.shape
    price = np.ones(n_paths)
    equity = np.full(n_paths, e0)
    units = np.full(n_paths, e0 * leverage)
    equity -= units * FEE_RT_SIDE
    live = np.ones(n_paths, dtype=bool)
    liq_hour = np.full(n_paths, np.inf)
    snaps: dict[int, np.ndarray] = {}
    for i in range(1, hours + 1):
        p_prev = price
        price = p_prev * np.exp(r_hourly[:, i - 1])
        notional_prev = units * p_prev
        equity = equity + units * (price - p_prev) - notional_prev * f_hourly[:, i - 1]
        notional_now = units * price
        blow = live & (equity <= MM * notional_now)
        if blow.any():
            liq_hour[blow] = i
            equity[blow] = 0.0
            live[blow] = False
        if i % BLOCK_H == 0 and i < hours:
            target = np.where(live, leverage * equity, units * price)
            trade = target - notional_now
            equity = equity - np.where(live, np.abs(trade) * FEE_RT_SIDE, 0.0)
            units = np.where(live, target / np.where(price > 0, price, 1.0), units)
        if i in HORIZONS.values():
            snaps[i] = equity.copy()
    out: dict[str, np.ndarray] = {}
    for hname, h in HORIZONS.items():
        eq_h = np.where(liq_hour <= h, 0.0, np.maximum(snaps[h] - units * price * FEE_RT_SIDE, 0.0))
        out[hname] = eq_h
    out["liq_hour"] = liq_hour
    return out


def stats(eq: np.ndarray) -> dict:
    return {
        "p_liq": float((eq <= 0).mean()),
        "p_below_50": float((eq < LOW_EQUITY).mean()),
        "median": float(np.median(eq)),
        "p10": float(np.percentile(eq, 10)),
        "p90": float(np.percentile(eq, 90)),
        "mean": float(eq.mean()),
    }


def run_grid(ret: np.ndarray, fund: np.ndarray, n_paths: int = N_PATHS) -> dict:
    rng = np.random.default_rng(SEED)
    results: dict = {
        "modes": {mode: {str(mu): {str(lev): {h: {"eq": []} for h in HORIZONS} for lev in LEVERAGES} for mu in MUS} for mode in MODES},
        "sigma_annualized": annualized_sigma(ret),
        "n_paths": n_paths,
    }
    sigma = results["sigma_annualized"]
    results["kelly"] = {str(mu): kelly_fraction(mu, sigma) for mu in MUS}
    max_hours = max(HORIZONS.values())
    for start in range(0, n_paths, CHUNK):
        n = min(CHUNK, n_paths - start)
        r_chunk, f_chunk = draw_blocks(rng, ret, fund, n, max_hours)
        for mode_name in MODES:
            sim = simulate_fixed if mode_name == "fixed" else simulate_rebalanced
            for lev in LEVERAGES:
                for mu in MUS:
                    r_mu = r_chunk + mu / HOURS_YEAR
                    out = sim(r_mu, f_chunk, lev)
                    slot = results["modes"][mode_name][str(mu)][str(lev)]
                    for hname in HORIZONS:
                        slot[hname]["eq"].append(out[hname])
    for mode_name in MODES:
        for mu_key in results["modes"][mode_name]:
            for lev_key in results["modes"][mode_name][mu_key]:
                for hname, cell in results["modes"][mode_name][mu_key][lev_key].items():
                    eq = np.concatenate(cell["eq"])
                    cell.clear()
                    cell.update(stats(eq))
    return results


def fmt_money(x: float) -> str:
    return f"${x:,.0f}"


def fmt_pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def git_hash() -> str:
    try:
        return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "--short", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return "unknown"


def report_md(res: dict, started: str, ended: str) -> str:
    lines = [
        "# R1/R2 Leverage ruin + Kelly study — canonical run",
        "",
        f"- Run (UTC): {started} -> {ended}",
        f"- Spec: PRE_REGISTRATION.md APPENDIX 12 (locked 8988718). Script: studies/leverage_ruin_study.py @ {git_hash()}",
        f"- Data: SOLUSDT 1h 2020-09-23 -> 2026-08-12 | sigma annualized = {fmt_pct(res['sigma_annualized'])} | N={res['n_paths']} paths, seed {SEED}",
        f"- Repairs disclosed: {REPAIRS or 'none'}",
        "- No-edge (mu=0) is the reference case; mu scenarios are hypothetical, not predictions.",
        "",
    ]
    for mode in MODES:
        lines += [f"## Mode: {mode} (e0=$500)", ""]
        for mu_key in [str(mu) for mu in MUS]:
            lines += [f"### mu = {mu_key}", "", "| L | horizon | P(liq) | P(eq<$50) | median | p10 | p90 | mean |", "|---|---|---|---|---|---|---|---|"]
            for lev in LEVERAGES:
                for hname in HORIZONS:
                    c = res["modes"][mode][mu_key][str(lev)][hname]
                    lines.append(
                        f"| {lev}x | {hname} | {fmt_pct(c['p_liq'])} | {fmt_pct(c['p_below_50'])} | {fmt_money(c['median'])} | "
                        f"{fmt_money(c['p10'])} | {fmt_money(c['p90'])} | {fmt_money(c['mean'])} |"
                    )
            lines.append("")
    lines += [f"## R2 Kelly (f* = mu / sigma^2, sigma = {res['sigma_annualized']:.1%})", "", "| mu | f* |", "|---|---|"]
    for mu, f in res["kelly"].items():
        lines.append(f"| {mu} | {f:.3f} |")
    lines += [
        "",
        "Read: f* near or below 0.25 even at a hypothetical +20%/yr edge; any leverage >2x",
        "implies an effective fraction >0.50 of capital, far above Kelly for this volatility.",
        "With no validated edge (mu=0), f* = 0 — leverage is a negative-EV lottery for this",
        "account size (BIBLE Art. V: no live execution).",
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true")
    args = ap.parse_args()
    started = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ret, fund = load_series(DATA)
    n_paths = 200 if args.fast else N_PATHS
    res = run_grid(ret, fund, n_paths)
    ended = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if args.fast:
        print(json.dumps({"fast_smoke": True, "sigma": res["sigma_annualized"], "n_paths": n_paths}, indent=2))
        return 0
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "leverage_ruin_2026-09-17.json").write_text(json.dumps(res, indent=2))
    REPORT.write_text(report_md(res, started, ended))
    print(json.dumps({"sigma": res["sigma_annualized"], "kelly": res["kelly"], "n_paths": n_paths}, indent=2))
    print(f"report: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
