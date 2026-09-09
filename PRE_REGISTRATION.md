# PRE-REGISTRATION — Narrative → Price Hypotheses (locked 2026-09-09)

This file is committed BEFORE the collector has produced any data. No hypothesis
below may be edited after data collection begins; only new hypotheses may be
appended with a new date. This is the discipline that separates research from
curve-fitting (and it is what killed two fake strategies on 2026-09-09).

## Data that will exist (collected hourly from now)
- `signals.jsonl` — raw narrative signals (6 sources)
- `narratives.jsonl` — hourly cluster snapshots (score, size, source diversity)
- `market_1h.jsonl` — SOL + 7 listed Solana-ecosystem perps (close + quote volume)
- Positioning data comes from the EXISTING Aegis futures_context collector
  (Binance liquidations + open interest + mark price, 25 symbols, live).

## H1 — narrative-momentum (long side)
Cluster formation event: narrative cluster with score >= 75th percentile of its
own trailing 30d distribution AND >= 2 distinct sources appears on day T.
Prediction: the SOL basket (EW of the 8 listed perps) earns positive abnormal
return over T+1..T+5 vs SOL itself, conditional on basket 24h quote volume
z-score > 1 at T (volume confirmation).

## H2 — social-only fade (short side / no-trade check)
Same cluster event WITHOUT volume confirmation.
Prediction: NO positive edge (or negative). If H2 shows an edge too, H1 was
probably just crypto beta, not narrative — treat as suspicious and investigate.

## Gate suite (identical to the 2026-09-09 strategy standard)
- Event-study, walk-forward, no overlap leakage; delay test: signals lagged +1 extra day
- Cost ladder: 10 / 15 / 20 bps per turnover (taker RT) + funding where applicable
- Benchmarks: SOL buy-and-hold over the same window; random-event bootstrap (1000 draws)
- Minimum data: >= 6 weeks of collection AND >= 30 qualifying cluster events before any verdict
- KILL: |event IR| not distinguishable from bootstrap at 90% -> archive, stop collecting for trading purposes

## Execution path (ONLY if a hypothesis passes)
Trade the LISTED proxies (Binance perps in the basket) — no Solana wallet keys,
no on-chain swaps, no memecoins. Any on-chain execution requires explicit,
separate user authorization and a new governed task.

## Status
- [x] Pre-registration committed 2026-09-09
- [ ] Data collection start (collector cron hourly)
- [ ] >= 6 weeks data + >= 30 events
- [ ] Gate suite run
- [ ] Verdict

---

# APPENDIX (2026-09-09, same day) — Positioning hypotheses from futures_context history

Context: Aegis futures_context already holds 60 days (2026-07-11..2026-09-09) of
Binance liquidations + open interest + mark price for 25 perps, collected live.
These hypotheses are locked BEFORE any test runs on that history. 60 days = ONE
regime window: any result is labeled PRELIMINARY and forward collection continues.

## H3 — OI-flush exhaustion (long side)
Event on pair P at day T: 24h OI change <= -5% AND 24h mark-price return <= -3%.
Prediction: P earns positive abnormal forward return over T+1..T+5 vs the
cross-sectional median of the 25-symbol panel, with effect stronger when the
24h long-side liquidation USD on P is in the panel's top quartile.

## H4 — liquidation-cascade exhaustion
Event on pair P at day T: 24h one-side liquidation USD >= $2M (longs flushed =
forced selling; shorts flushed = forced buying).
Prediction: longs-flushed events -> positive forward T+1..T+5 return;
shorts-flushed events -> negative forward T+1..T+5 return (mirror).
If BOTH directions show the SAME sign, the "exhaustion" story is wrong — treat
as momentum/beta, kill the exhaustion framing.

## Gate suite (same standard, PRELIMINARY flag for 60-day window)
- Delay test (+1d on event day), cost ladder 10/15/20bps, bootstrap (1000 random
  event draws, same count), benchmark = panel median + SOL B&H
- Minimum: >= 30 events per hypothesis; else "INSUFFICIENT_DATA" verdict
- KILL rule identical to H1/H2

## Status (positioning)
- [x] H3/H4 pre-registered 2026-09-09 (before any test run)
- [ ] 60-day preliminary gate run
- [ ] Verdict


---

# APPENDIX 2 (2026-09-09 evening) — H5 funding-CONTINUATION

Motivation: the killed funding-REVERSAL study (same day) documented that funding
extremes do NOT mean-revert — longs in high-funding coins LOST on the fade side,
i.e., extreme-funding coins CONTINUED. H5 pre-registers the opposite-sign
hypothesis on the same data, as a distinct family.

## H5 — funding-continuation cross-sectional
Signal: trailing 7d mean perp funding per pair (daily panel, 24 alts).
Book: weekly Monday rebalance. LONG the 3 pairs with HIGHEST trailing funding,
SHORT the 3 with LOWEST, EW +-1/3, vol-target 15% ann (trailing 30d book vol,
gross cap 2.0), close-T -> T+1 convention.
Prediction: positive OOS CAGR/Sharpe (crowding continues; shorts in low/negative
funding also collect carry).

## Gate suite
- 5-block walk-forward OOS (blocks 1-4 stitched), delay test +1 week,
  fee ladder 10/15/20bps per turnover, benchmarks BTC B&H + HMM variant-A book,
  correlation with HMM book reported (diversification check)
- KILL: PF <= 1.1 or Sharpe <= 0.8 at 10bps (same bar as the killed reversal)
- Max 1 iteration; no threshold tuning after results

## Status (H5)
- [x] Pre-registered 2026-09-09 BEFORE test
- [ ] Gate run
- [ ] Verdict
