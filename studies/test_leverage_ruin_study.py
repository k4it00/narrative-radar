"""Hermetic tests for the R1/R2 leverage study (APPENDIX 12) — synthetic data only."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import leverage_ruin_study as m  # noqa: E402


def test_kelly_fraction() -> None:
    assert abs(m.kelly_fraction(0.2, 0.9) - 0.2 / 0.81) < 1e-12
    assert m.kelly_fraction(0.0, 0.9) == 0.0
    assert m.kelly_fraction(0.2, 0.0) == 0.0


def test_annualized_sigma() -> None:
    rets = np.zeros(100)
    assert m.annualized_sigma(rets) == 0.0
    rets2 = np.full(100, 0.001)
    assert m.annualized_sigma(rets2) < 1e-9
    rets3 = np.array([0.01, -0.01] * 50)
    assert m.annualized_sigma(rets3) > 0


def test_draw_blocks_shapes_and_stamp_alignment() -> None:
    rng = np.random.default_rng(1)
    n = 51_600
    ret = np.linspace(-0.001, 0.001, n)
    fund = np.arange(n, dtype=np.float64)
    r, f = m.draw_blocks(rng, ret, fund, 50, 240)
    assert r.shape == (50, 240) and f.shape == (50, 240)
    starts = None
    nz_rows, nz_cols = np.nonzero(f)
    for row, col in zip(nz_rows[:200], nz_cols[:200]):
        block, pos = divmod(col, 24)
        with np.errstate(invalid="ignore"):
            abs_idx = int(f[row, col])
        assert abs_idx % 8 == 0


def test_simulate_fixed_zero_returns() -> None:
    r = np.zeros((10, max(m.HORIZONS.values())))
    f = np.zeros_like(r)
    out = m.simulate_fixed(r, f, leverage=1)
    expected = 500 - 0.0007 * 500 - 0.0007 * 500
    for h in m.HORIZONS:
        assert abs(out[h][0] - expected) < 1e-9


def test_simulate_fixed_liquidation() -> None:
    hours = max(m.HORIZONS.values())
    r = np.zeros((1, hours))
    r[0, 0] = np.log(0.90)
    f = np.zeros_like(r)
    out = m.simulate_fixed(r, f, leverage=10)
    assert out["liq_hour"][0] == 1
    assert all(out[h][0] == 0.0 for h in m.HORIZONS)


def test_simulate_rebalanced_zero_returns() -> None:
    r = np.zeros((5, max(m.HORIZONS.values())))
    f = np.zeros_like(r)
    out = m.simulate_rebalanced(r, f, leverage=1)
    expected = 500 - 0.0007 * 500 - 0.0007 * 500
    for h in m.HORIZONS:
        assert abs(out[h][0] - expected) < 1e-6


def test_simulate_rebalanced_liquidation() -> None:
    hours = max(m.HORIZONS.values())
    r = np.full((1, hours), np.log(0.98))
    f = np.zeros_like(r)
    out = m.simulate_rebalanced(r, f, leverage=10)
    assert np.isfinite(out["liq_hour"][0])
    assert out["liq_hour"][0] < 720
    assert out["365d"][0] == 0.0


def test_funding_charges_in_fixed_mode() -> None:
    hours = max(m.HORIZONS.values())
    r = np.zeros((1, hours))
    f = np.zeros_like(r)
    f[0, 7] = 0.0001
    out = m.simulate_fixed(r, f, leverage=2)
    expected = 500 - 0.0007 * 1000 - 1000 * 0.0001 - 0.0007 * 1000
    assert abs(out["365d"][0] - expected) < 1e-9


def test_stats_basic() -> None:
    eq = np.array([0.0, 0.0, 100.0, 200.0, 400.0])
    s = m.stats(eq)
    assert s["p_liq"] == 0.4
    assert s["p_below_50"] == 0.4
    assert s["median"] == 100.0


def test_run_grid_fast_integration() -> None:
    rng = np.random.default_rng(2)
    ret = rng.normal(0, 0.01, 5000)
    fund = np.zeros(5000)
    res = m.run_grid(ret, fund, n_paths=50)
    for mode in m.MODES:
        for mu_key in res["modes"][mode]:
            for lev_key in res["modes"][mode][mu_key]:
                for hname in m.HORIZONS:
                    assert "p_liq" in res["modes"][mode][mu_key][lev_key][hname]
    assert set(res["kelly"].keys()) == {str(mu) for mu in m.MUS}
