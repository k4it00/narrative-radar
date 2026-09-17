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

---

# APPENDIX 3 (2026-09-09, continuation session) — H6 taker-flow + H7 1h-trend wide-ATR

User objective for this pair: beat the HMM book on OOS PnL with maxDD / PF / Sharpe
within tolerance of HMM (OOS 9bps: CAGR 16.8% / Sharpe 1.395 / maxDD -12.4% / PF 1.304 /
win-rate 50.7% daily / 1.65 fills-day), achieved via higher win rate and/or more trades
per day. Both hypotheses below are locked BEFORE any test run on the 6y hourly files.

## Master calendar (applies to both)
Calendar of the HMM engine: px,fun = v2.load_daily(); idx_a = px.index[warmup:];
blocks = 5 equal splits; OOS = blocks[1]..[4] stitched (starts ~2022-03); folds = blocks 1-4.
H6/H7 daily returns reindexed onto idx_a. Identical cost ladder 10/15/20bps per turnover
unit, funding applied by the engine where positions are held. Benchmarks: BTC B&H +
HMM variant-A OOS book at 9bps. Correlation with HMM book + 50/50 blend Sharpe reported.

## H6 — taker-flow imbalance continuation (daily panel, 24 alts)
- Data: hourly `volume` + `taker_buy_volume` from data/{PAIR}_1h_2020_2026.csv
  (coverage verified 100% on 7 pairs before this registration; 0% taker>vol rows).
  Universe: the H5 24-alt list; BTC excluded (benchmark only).
- Signal: daily buy share s_d = sum_h taker_buy_volume / sum_h volume;
  imbalance z_d = 2*s_d - 1; signal = 7d rolling mean of z_d (min_periods 7).
- Book: weekly Monday rebalance; LONG top-3 by signal / SHORT bottom-3; EW +-1/3;
  vol-target 15% ann (trailing 30d book vol); gross cap 2.0; T->T+1 via run_book.
- Distinct from the KILLED 15m flow screen (53 days, intrabar, W4/16 x theta grid):
  this is a 6-year daily-scale cross-sectional continuation test, different horizon.
- Prediction: sustained buy-side taker dominance continues (positive OOS CAGR/Sharpe
  net of 10bps).

## H7 — 1h trend with wide ATR stops (majors, long-only)
- Universe: BTC, ETH, SOL, BNB, XRP, DOGE (full 6y hourly coverage), EW 1/6 each.
- Per pair, causal on 1h bars: regime = EMA48(close) > EMA336(close).
- Entry: first hour after regime flips true (signal close t, exec t+1 open).
- Exit (first of): regime flips false; OR close < running-max(close since entry)
  - 2.0 x ATR14 (1h). One unit notional per active pair. No short leg in v1 (locked).
- Book: pair hourly PnL -> daily; book vol-target 15% ann (30d trailing), gross cap 2.0.
- Wide-stop cost math (handoff): BTC 1h ATR14 ~ 50-90bps -> stop 100-180bps =>
  10-20bps RT cost ~ 0.06-0.2R. Trade-level WR expected > 55%.
- Prediction: PnL >= HMM OOS with maxDD/PF/Sharpe near HMM, higher WR and fills TPD.

## KILL rules (locked, max 1 iteration, no threshold tuning after results)
- PF <= 1.1 OR Sharpe <= 0.8 at 10bps OR <=3/4 folds positive -> KILL (both H6/H7).
- CANDIDATE bar: OOS CAGR > HMM 9bps OOS CAGR (0.168) AND maxDD >= -0.14 AND
  PF >= 1.25 AND Sharpe >= 1.25 AND (daily WR > 0.507 OR fills TPD > 1.65).

## Status (H6/H7)
- [x] Pre-registered 2026-09-09 BEFORE test
- [x] Gate run 2026-09-09 (h6h7_gate_run.py)
- [x] Verdict: BOTH KILLED at locked rules (H6: Sharpe 0.47 / PF 1.07 / DD -27.9% at
      10bps, 2/4 folds; H7: CAGR -8.6% / Sharpe -0.36 / DD -48.9% at 10bps, 2/4 folds).
      No iteration allowed; families closed. Artifacts: reports/research/h6h7_gate_run.{py,json,log}

---

# APPENDIX 4 (2026-09-09, same session) — H8 low-volatility anomaly L/S

Motivation: H6/H7 died; one more genuinely-untried family this session. Prior art
checked BEFORE registration (AGENTS.md evidence step): Burggraf & Rudolf 2021 (FRL)
found NO low-vol premium 2013-2019; Pyo 2026 (FRL) documents a significant low-vol
premium post-2017 with 2-3 month vol formation and ~1 month holding; lottery-demand
lineage (Bali 2011 -> Ozdamar 2021 crypto MAX; Applied Economics 2025) says
high-lottery coins UNDERPERFORM. Distinct family: defensive quality, not momentum/
flow/funding/trend.

## H8 — cross-sectional low-volatility L/S book
- Universe: 25 symbols = the H5 24 alts + BTCUSDT (BTC eligible for both legs;
  BTC B&H remains the benchmark).
- Signal: trailing realized vol of daily returns = std(30d) x sqrt(365)  [V1]
          and std(75d) x sqrt(365)                                       [V2]
  (both variants locked upfront — literature window; NO post-hoc selection.)
- Book: weekly Monday rebalance; LONG 5 lowest-vol / SHORT 5 highest-vol; EW +-1/5;
  vol-target 15% ann (30d trailing book vol); gross cap 2.0; T->T+1 via run_book.
- Costs: ladder 10/15/20bps per turnover + engine funding.
- Master calendar identical to APPENDIX 3 (HMM engine idx_a, 5-block OOS blocks 1-4).
- Delay test: signal shifted +7d extra.
- Prediction: positive OOS CAGR/Sharpe net of 10bps; daily WR > HMM 50.7%;
  maxDD materially below HMM's -12.4% (defensive legs); corr with HMM low-moderate.

## KILL rules (locked, max 1 iteration, no threshold tuning after results)
- PF <= 1.1 OR Sharpe <= 0.8 at 10bps OR <=3/4 folds positive -> KILL (both V1/V2).
- CANDIDATE bar: OOS CAGR > 0.168 (HMM) AND maxDD >= -0.14 AND PF >= 1.25 AND
  Sharpe >= 1.25 AND (daily WR > 0.507 OR fills TPD > 1.65).
- If neither variant passes gates but both are profitable at 10bps, verdict is
  "ALIVE_BELOW_BAR" — report as diversification candidate only if
  corr(H8,HMM) < 0.5 and 50/50 blend Sharpe > 1.40 (HMM alone).

## Status (H8)
- [x] Pre-registered 2026-09-09 BEFORE test
- [x] Gate run 2026-09-09 (h8_lowvol_gate_run.py)
- [x] Verdict: KILLED both variants at locked rules (V1 30d: CAGR -11.0% / Sharpe -0.63 /
      PF 0.91 / DD -53.0% at 10bps, 0/4 folds; V2 75d: CAGR -2.6% / Sharpe -0.08 /
      PF 0.99 / DD -38.9% at 10bps, 0/4 folds). Daily WR 52.7-53.7% EXCEEDED the HMM
      50.7% bar yet PnL negative — WR alone is not a PnL lever. Short-high-vol leg
      bled through 2023-24 alt rallies on this liquid-perp universe.
      Artifact: reports/research/h8_lowvol_gate_run.{py,json,log}

---

# APPENDIX 5 (2026-09-09, second continuation session) — H9 dominance rotation + conditional H10 blend

Prior-art check BEFORE registration (AGENTS.md evidence step): category dual
momentum long-only (new_candidates_search.py CDM) and dual-horizon TS trend
(search_cycle_2026-09-02c F3) both FAILED — but neither tested the 2-asset
BTC vs alt-basket relative-strength switch. Capital rotation between BTC and
alts (BTC-dominance cycles) is the family here; distinct from category
cross-sectional momentum and from dual-lookback BTC trend.

## H9 — BTC/alt-basket relative-strength rotation (long-only, 2 states + cash)
- Data: daily closes, 25 symbols (24 H5 alts + BTC). Alt basket = EW return of
  alts with >=90d history; basket index = cumprod of that EW series (starts when
  first alts qualify, no extra parameter). RS ratio R_t = BTC_close / basket_index.
- Variant A (pure RS switch): hold BTC when R > EMA50(R), else hold alt basket
  (EW of listed alts). No cash state, no short leg.
- Variant B (dual-momentum gate): variant A, but each leg additionally requires
  its own trailing 50d absolute return > 0; if neither qualifies -> cash.
- Book: weekly Monday rebalance, vol-target 15% ann (30d trailing book vol),
  gross cap 2.0 (long-only, normally binds at 1.0), T->T+1 via run_book,
  funding applied by engine. EMA50 lookback LOCKED (single value, no grid).
- Gate suite: identical to APPENDIX 3/4 (master calendar, 5-block OOS blocks
  1-4, ladder 10/15/20bps, delay +7d, BTC B&H + HMM 9bps benchmarks,
  corr + 50/50 blend Sharpe).
- KILL rules (locked): PF <= 1.1 OR Sharpe <= 0.8 at 10bps OR <=3/4 folds.

## H10 — three-sleeve champion blend (CONDITIONAL: only if H9 A or B passes gates)
- Blend: 0.4 MTSOM(180d, tgt 0.15) + 0.4 RegSwitch(bear-only) + 0.2
  [H9 passing variant; if both pass, higher OOS 10bps Sharpe wins — selection
  between exactly two locked variants, declared upfront].
- HMM variant-A regime scalar applied on top (same as champion).
- Gates vs champion on identical OOS window (candidate bar from APPENDIX 3):
  OOS CAGR > 0.168, maxDD >= -0.14, PF >= 1.25, Sharpe >= 1.25, folds >= 3,
  delay-clean (scalar +1d drop <= 30%).

## Status (H9/H10)
- [x] Pre-registered 2026-09-09 BEFORE test
- [x] Gate run 2026-09-09 (h9h10_gate_run.py)
- [x] Verdict: H9 A KILLED (OOS 10bps: CAGR 3.2% / Sharpe 0.27 / PF 1.04 / DD -30.6%,
      folds 3/4 but delay drop -57%: 3.18% -> 1.38% — no stable edge). H9 B KILLED
      (CAGR -0.6% / Sharpe 0.11 / DD -38.2%, daily WR 29%). H10 VOID per conditional
      (no passing variant to blend). BTC-vs-alt RS rotation family CLOSED.
      Artifact: reports/research/h9h10_gate_run.{py,json,log}

---

# APPENDIX 6 (2026-09-09, session 3) — compounding frontier + regime-dial sensitivity

User request: "find the optimal setting of everything for HMM, compound fast."
REFUSED as stated: post-hoc grid-search of champion parameters on seen data is
curve-fitting by construction (two fake strategies died today from exactly this).
REGISTERED instead, before any run:

## A. Leverage ladder (the only clean compounding dial)
- L in {1.0, 1.5, 2.0, 2.5, 3.0} applied multiplicatively to the FROZEN champion
  weights (blend x HMM scalar x L), identical 5-block OOS, 9bps AND 20bps.
- Liquidation boundary (cross margin, maintenance margin ~0.5%):
  liq_adverse ~= 1/L - 0.005 of equity. Survivability rule (locked):
  L x OOS_maxDD(1x)=0.124 must stay <= 0.50 x liq_adverse (2x safety factor).
  Expectation declared upfront: frontier ends at L=2.0; L=2.5 thin; L=3.0 has
  liquidation INSIDE the worst-observed drawdown -> not survivable.

## B. Regime-dial sensitivity (one-at-a-time; SENSITIVITY, NOT SELECTION)
- S1: RISK_OFF_W 0.3 -> 0.5 (milder de-risking).
- S2: p_on threshold 0.5 -> 0.6 (stay risk-on longer).
- Each evaluated at 9bps on the identical OOS window with delay test.
- VERDICT RULE (locked): any difference vs champion is reported as IN-SAMPLE
  and NOT promotable. If a variant dominates champion, it may only enter the
  NEXT pre-registered verification cycle (fresh commitment, no cherry-picks).
- Purpose: show the risk/return surface so the user sees leverage is the only
  real compounding lever and the frozen dials are already at (or near) optimum.

## Status (APPENDIX 6)
- [x] Pre-registered 2026-09-09 BEFORE test
- [x] Gate run 2026-09-09 (hmm_compound_frontier_20260909.py)
- [x] Verdict: (A) Leverage is the ONLY compounding lever — CAGR scales linearly
      (1x 16.8% -> 2x 34.6% -> 3x 53.2%) with Sharpe invariant at 1.395; locked
      survivability rule puts the comfortable frontier at L=1.5 (DD -18.2% vs liq
      -66.2%, 2x safety factor holds) and L=2.0 exactly AT the knife edge
      (2x-observed-DD 49.6% == liq 49.5% — a 2022-repeat wipes the account).
      L>=2.5 fails the rule outright. (B) Sensitivity: S1 RISK_OFF_W=0.5 gives
      +0.7pt CAGR for -0.9pt PF and +0.4pt DD = noise, not promotable; S2
      threshold 0.6 = byte-identical to champion (posteriors saturated, dial inert).
      FROZEN SETTINGS CONFIRMED OPTIMAL within noise. No config changes made.
      Artifacts: reports/research/hmm_compound_frontier_20260909.{py,json,log}

---

# APPENDIX 7 (2026-09-09, FX session 3) — FX-F1 carry / FX-F2 momentum / FX-F3 HMM port

Data phase COMPLETE first (task-770692fa9fa2, verify-5df4fa7a659d):
24 pairs × 15.7y (2011-01..2026-09), 0-blank daily panel, rate-differential
table, measured costs. Data exists BEFORE this registration — nothing below
may be tuned after the first OOS run. Agreed scope (HANDOFF_20260909_S2):
FX is a DIVERSIFICATION candidate, NOT a compounding accelerator (majors vol
~7-10% ann vs crypto 50-80%; matching champion CAGR needs 5-10x leverage and
the liquidation frontier follows).

Prior-art check BEFORE registration: no FX carry/momentum/HMM-regime book has
been tested on this machine (searched strategies/, reports/research/). Local
pairs_trading/pairs_spread are stat-arb spreads, a different family. This is
the first FX run.

## Data + costs (locked inputs)
- Prices: research/fx/processed/dukascopy_daily/{PAIR}.csv (daily OHLCV,
  h1-derived). Rates: rates/rate_differential_daily.csv (r_quote - r_base,
  forward-filled; monthly FRED/OECD series lag up to 30d — documented).
- Costs per unit turnover: measured median spread (measured_costs_fx.json,
  e.g. EURUSD 0.3 pips ≈ 0.26bp RT; p95 1.4 pips ≈ 1.2bp RT) + swap accrual
  differential/360 per day with ×3 Wednesday. COST LADDER (locked):
  1x measured median, 2x median, p95 spread — replaces the crypto 10/15/20bps
  ladder (FX majors RT spread is ~1-2bp; the crypto ladder is off-scale here).
  Swap is applied at the MEASURED differential in all rungs (no scenario
  haircut on top of the documented one).
- Universe: all 24 pairs (vs the >=20 acceptance bar); EW legs.

## FX-F1 — carry, dollar-neutral L/S
- Signal at rebalance T: latest daily rate differential (r_quote - r_base),
  data through T, execution at daily close T+1 (1-day execution lag, built in).
- Book: long the top tercile (8 most-positive differentials), short the bottom
  tercile (8 most-negative), EW within each leg, dollar-neutral (long notional
  = short notional). REBALANCE LOCKED: MONTHLY (first trading day of month).
- Vol target 15% ann on the BOOK (30d trailing daily-return vol), gross cap 2.0
  (dollar-neutral, normally binds at 1.0), T->T+1 daily closes, swap accrues
  daily on held positions (differential/360, ×3 Wed).
- Benchmark: the PASSIVE CARRY COMPOSITE — same book with NO vol-target and
  fixed unit gross (the class-standard buy-and-hold-equivalent twin).

## FX-F2 — momentum, Menkhoff-style
- Signal at rebalance T: trailing 6-month cumulative return of each pair
  (months -6..-1, inclusive of the just-finished month; FORMATION WINDOW
  LOCKED: 6m — single value, no grid).
- Book: long top tercile (8) / short bottom tercile (8), EW legs,
  dollar-neutral. REBALANCE LOCKED: MONTHLY (first trading day of month).
- Vol target 15% ann (30d trailing), gross cap 2.0, execution T+1, spread +
  swap costs as F1.
- Benchmark: the PASSIVE MOMENTUM COMPOSITE — same book, no vol-target, fixed
  unit gross.

## FX-F3 — HMM-regime port (champion family on FX)
- Model: 2-state GaussianHMM on monthly features [FX momentum: 6m return of
  the EW cross-rate index; FX realized vol: 30d annualized of the index;
  carry spread: mean differential across the 24 pairs] — same feature-class
  triple as the crypto champion. Monthly EXPANDING refit (refit on all
  history; min 36 monthly observations before first state call).
- Book: in the high-vol/risk-off state -> cash (flat); in risk-on -> the
  better of (carry composite, momentum composite) selected by the LOCKED
  tiebreak: the one with higher training-block Sharpe at 1x measured costs,
  chosen ONCE on the first training fold and FROZEN for all folds (no
  per-fold switching). State calls use the month-END posterior of month T for
  month T+1 (same 1-month shift discipline as the champion).
- Gates vs BOTH composites (must beat the risk-on composite it switches to,
  OOS at 1x measured costs).

## Gate suite (identical standard, FX master calendar)
- 5 contiguous blocks: B1 2011-01..2014-12, B2 2015-01..2018-12,
  B3 2019-01..2021-12, B4 2022-01..2024-12, B5 2025-01..2026-09. Folds =
  fit/evaluate on blocks 1..k, test block k+1 -> 4 OOS folds.
- Walk-forward OOS ONLY; per-fold + pooled metrics reported (CAGR, Sharpe,
  Sortino, maxDD, Calmar, PF, win rate, trade/turnover count).
- Delay test: all signals shifted +1 EXTRA rebalance month; clean if Sharpe
  drop <= 30% (same bar as the champion).
- Corr(FX book, crypto HMM champion daily returns) + 50/50 blend Sharpe
  reported for every passing book (diversification check).

## KILL rules (locked, IDENTICAL to crypto standard)
- PF <= 1.1 OR Sharpe <= 0.8 at 1x measured costs OR <= 3/4 folds.
- 1 iteration max after the first OOS run; zero re-tuning on favorable folds;
  zero post-hoc parameter changes of any kind.

## PROMOTION bar (diversification, not compounding — locked)
- A book promotes ONLY if it passes the gate suite AND corr vs the crypto HMM
  champion < 0.5 AND 50/50 blend Sharpe > champion alone (1.40).
- Literature priors (checked 2026-09-09, from S2 handoff): carry 0.8-0.9
  gross Sharpe (negative skew; peso/crash risk; Aug-2024 yen unwind), momentum
  0.6-0.95, carry+momentum 50/50 ~0.98 GROSS. Net expect 0.7-0.9: passes the
  kill bar, BELOW the champion (1.40). Honest prior: ONE family passes gates,
  none reaches champion; the value is diversification once capital justifies
  two books. A kill is the EXPECTED outcome for at least one family.

## Status (APPENDIX 7)
- [x] Pre-registered 2026-09-09 BEFORE any test (data phase complete first)
- [x] Gate run 2026-09-09 (fxf_gate_run.py, research/fx/) — single run, zero tuning
- [x] Verdict: ALL THREE FAMILIES KILLED by the locked rules (pooled OOS 2015-01..2026-09
      at 1x measured costs). FX-F1 carry: CAGR +4.5% / Sharpe 0.595 / PF 1.115 /
      DD -12.1% / folds 4/4, delay-clean — KILLED on Sharpe (0.595 <= 0.8; real but
      small edge, matches the honest prior's low end). FX-F2 momentum (6m, majors):
      Sharpe -0.54 / PF 0.909 / folds 0/4, delay-unclean — KILLED decisively; no
      6m-momentum edge on this universe OOS. FX-F3 HMM port: chose carry composite
      (frozen B1 tiebreak) but the monthly HMM posterior NEVER left risk-on
      (147/147 months) -> byte-identical to the passive carry composite
      (0.591 vs 0.591, beat_composite False) — KILLED on Sharpe; HMM monthly gate
      is an inert dial on FX features. Cost ladder does not change any verdict
      (1x = 2x to 4dp; p95 within 0.01 Sharpe). Diversification bar NOT REACHED
      (only gate-passers get corr/blend vs champion; none passed). FX family
      CLOSED at the kill rules. Artifacts: reports/research/fxf_gate_run.{py,json,log}

---

# APPENDIX 8 (2026-09-09, session 4) — H11 delta-neutral perp-spot basis carry

## H11 — continuous basis-carry book (long spot / short perp, delta-neutral)

**Mechanism (who is constrained, why it may persist):** retail perp traders run a
structural long bias on hot altcoins and pay funding to levered longs; the
positive perpetual premium transfers cash to hedged shorts regardless of price
direction. Unlike the KILLED funding L/S sweep (funding_carry_sweep_fast.json:
perp-only, full price risk on both legs, price_sum >> funding_sum, all configs
CAGR -16%..-36%), this book hedges with the SPOT leg, so PnL per pair =
(spot_ret - perp_ret) + funding_collected - costs; the directional price term
cancels and only basis drift + funding remain. Distinct from
evaluate_basis_carry.py (24h-hold threshold event-study, 6 majors, never gated
or persisted) and from H5/AegisFundingOnly (directional). Continuous book,
sign-rule signal, ZERO free thresholds.

**Universe (locked):** pairs with BOTH spot (`binance/{S}_USDT-1h.feather`)
and perp (`futures/{S}_USDT_USDT-1h-futures.parquet` + funding parquet) on
disk: AAVE, APT, ARB, BNB, BTC, ETH, FIL, HBAR, ICP, INJ, LTC, OP, SEI, SOL,
UNI, WIF, XRP (17; 1000PEPE excluded - spot file is unit-mismatched vs perp).
Pairs join after 30d of overlapping daily data; integrity guard: any pair with
median |daily basis| > 5% is DROPPED (data-corruption guard, not a signal dial).

**Spec (locked, no tuning):**
- Signal V1: trailing 21d mean daily funding > 0 -> active (long spot + short
  perp, equal notional 1/n_active each, gross = 2 before scaling).
- Signal V2: identical with 63d trailing window. (Sensitivity, like H8 V1/V2.)
- Both legs marked daily (close-to-close); funding = daily mean x3 (8h rate).
- Book vol-target 15% ann (30d trailing book vol, lagged, min_periods=30),
  gross cap 2.0; weights formed at t, executed t+1 (engine shift).
- Cost ladder 10/15/20 bps per unit turnover (2 units per pair open/close ->
  20/30/40 bps per full 2-leg round trip; conservative vs spot~10bps +
  perp~4-5bps taker).

**Master calendar:** identical to APPENDIX 3/4 (HMM engine idx_a, 5-block OOS
blocks 1-4 stitched, pooled OOS used for all gate metrics).

**Gate suite (identical standard):** cost ladder 10/15/20bps; delay test
(weights lagged +1 extra day; KILL if delay-CAGR retains < 70% of base);
per-fold CAGR (KILL if <= 3/4 positive); benchmarks reported: BTC B&H and HMM
champion 9bps over the identical OOS span; corr(H11, HMM) + 50/50 blend Sharpe
computed regardless (reported as diagnostics).

**KILL rules (locked, max 1 iteration, no threshold tuning after results):**
PF <= 1.1 OR Sharpe <= 0.8 at 10bps OR folds <= 3/4 OR delay retention < 70%
-> KILL. All four variants of failure are terminal; no re-spec.

**Promotion bar (diversification, not compounding — locked):** only if gates
PASS: corr(H11, HMM) < 0.5 AND 50/50 blend Sharpe > HMM alone makes H11 a
companion-book candidate for the user's capital decision; otherwise archive.

## Status (APPENDIX 8)
- [x] Pre-registered 2026-09-09 BEFORE any test (evidence phase: killed
      funding L/S sweep + un-gated basis event-study verified as distinct)
- [x] Gate run 2026-09-09 (h11_basis_carry_gate_run.py) — executed twice,
      both disclosed: run 1 hit a loader gap (11 of 17 pairs skipped - perp
      1h data stored as .feather, loader read only .parquet) and tested a
      6-pair subset; run 2 = loader repaired to implement the LOCKED 17-pair
      universe, filed as THE gate observation (run 1 retained as
      h11_basis_carry_gate_run.run1_6pair_loader_gap.log). Zero signal,
      threshold, or kill-rule changes between runs.
- [x] Verdict: **H11 PASSES the locked gates** (master calendar
      2022-03-06..2026-08-12 OOS, cost ladder, delay, folds):
      V1_21d @10bps: CAGR 11.5% / Sharpe 7.39 / PF 4.21 / maxDD -2.4% /
      folds 4/4 / delay retention 0.955 — PASS (KILL at 15/20bps severe:
      folds 3/4, disclosed). V2_63d @10bps: CAGR 12.2% / Sharpe 8.85 / PF
      5.04 / maxDD -1.5% / folds 4/4 / delay 0.96 — PASS; @15bps still PASS
      (Sharpe 7.95 / folds 4/4); @20bps severe folds 3/4 (disclosed). Both
      variants were locked upfront; V2 dominates at every rung. PnL
      decomposition: funding_total +147% vs basis_total ~0% (gross 1.75,
      active 87.6% of days) — the payload is funding collection, the hedge
      removes the price term that killed the perp-only sweep.
      **Diversification bar MET**: corr(V2, HMM) = 0.064; 50/50 blend
      Sharpe 3.46 vs HMM same-span 1.75 -> companion-book candidate.
- [x] Caveats (required reading before any capital decision): (1) daily
      bars CANNOT model short-perp margin/liquidation risk during funding
      spikes - real deployment needs cross margin + reduced gross; (2) the
      Sharpe level is the honest arithmetic of near-deterministic carry
      accrual, not comparable to directional books' Sharpe; (3) 20bps
      severe-cost rung fails folds for both variants - edge is real but
      cost-fragile at extreme costs; (4) single-exchange (Binance) data;
      (5) promotion = companion RESEARCH candidate only - paper/canary
      campaign per the operator skill is a separate gated process. NO live
      orders. Champion HMM book remains primary and frozen.

---

# APPENDIX 9 (2026-09-10) — H12 UTC session opening-range breakout (ORB)

Motivation: the day-trader request logged in HANDOFF_2026-09-10. The day-trader
space already killed on record: 5m/15m/1h standalone (RESULTS.md), time-of-day
seasonality, squeeze breakout (daily + intraday), H6 taker-flow, H7 1h wide-ATR
trend, H9 rotation. The remaining untested day-trader structure with data on
disk is the classic UTC-session opening-range breakout. Locked BEFORE any H12
result was computed; only data verification preceded this registration (5m CSVs
carry columns timestamp,open,high,low,close,volume,taker_buy_volume,funding_rate,
open_interest; the 5m funding column is empty -> funding taken from the 1h files
at the 00/08/16 UTC stamps).

## H12 — UTC session opening-range breakout (intraday, flat overnight)

**Universe (locked):** the H11 17-pair universe, restricted to pairs with
`data/{S}USDT_5m_2020_2026.csv` on disk — all 17 qualify: AAVE, APT, ARB, BNB,
BTC, ETH, FIL, HBAR, ICP, INJ, LTC, OP, SEI, SOL, UNI, WIF, XRP. Late listings
simply produce no trades before their first 5m bar.

**Session (locked):** 00:00 UTC daily open; ORB window = first K complete 5m
bars of the UTC day.

**K (locked grid):** K in {2, 4, 8} bars (10/20/40 min). Per WF fold, K is
selected TRAIN-ONLY: on all master-calendar days strictly before the fold's
first day, maximize net Sharpe (9bps) of the fixed-slot book; ties -> smaller
K. Selection never sees fold data; zero free thresholds after selection.

**Entry (locked):** first bar after the ORB window whose close is above the ORB
high (long) or below the ORB low (short) — signal bar t; execute at the OPEN of
bar t+1. Signals on the day's final bar are ignored. One position per symbol per
UTC day; NO re-entry (max re-entry = 0).

**Stop / target / forced flat (locked):** initial stop = opposite ORB boundary;
target = entry +/- 2x the stop distance (2R; target distance >= stop distance).
Intrabar: if stop and target are both touched in the same bar, the STOP is
assumed first (conservative). If neither is touched, forced flat at the close of
the day's last bar (23:55 UTC). NO overnight.

**Sizing (locked):** fixed 1/17 book notional per symbol slot; unused slots stay
cash; no vol targeting, no leverage.

**Costs (locked):** 9bps per unit turnover (entry + exit = 2 units per round
trip = 18bps per unit notional per trade) + funding: the 8h rate (from the 1h
files, value stamped at 00:00/08:00/16:00 UTC) charged whenever the position is
open across a stamp (in practice 08:00/16:00; no 00:00 stamp since entries start
after the opening window).

**Data hygiene (locked):** a symbol-day only trades if its first K bars and bars
through 23:00 UTC are present; incomplete symbol-days are skipped (no trade).

**Walk-forward (locked):** identical master calendar to APPENDIX 3/4/8 — HMM
engine idx_a, 5 equal blocks, OOS = blocks 1-4 stitched, daily book returns
reindexed onto idx_a. OOS = per-fold selected-K returns. Delay test: every entry
delayed +1 extra bar (signal t -> execute t+2); retention < 70% = KILL.

**Gates (locked 10-gate standard):** g1 PF > 1.2; g2 Sharpe > 1.2; g3 MaxDD >
-30%; g4 >= 3/4 WF folds positive (per-block CAGR > 0); g5 OOS CAGR > BTC B&H
CAGR (same OOS span); g6 delay retention >= 70%; g89 UW streak <= 180d AND
yearly consistency (Sharpe > BTC in >=75% full years, no full year < -15%);
g10 all completed recoveries <= 150d AND recovery factor >= 0.75. PASS iff all
ten pass; any failure = KILL and the family closes.

**KILL rules (locked):** no threshold/param tuning after results; max 1
iteration = loader repairs only, disclosed. Single cost rung 9bps (standard).

**Diversification (locked, only on PASS):** corr(H12 daily OOS, champion HMM
daily) and corr(H12, H11 V2_63d daily) on the same span + 50/50 blend Sharpe vs
each. Unloadable series -> stated as a limitation, no invented numbers.

**Prediction (stated before the result):** if a session-breakout edge survives
9bps on liquid perps, positive OOS CAGR with folds >= 3/4; expected cost-fragile
(many small trades). Benchmarks: BTC B&H + HMM champion 9bps on the same OOS
span.

## Status (APPENDIX 9)
- [x] Pre-registered 2026-09-10 BEFORE any H12 result (data verification only
      preceded: 5m CSVs present for all 17 pairs; funding unavailable in 5m ->
      1h funding stamps used)
- [x] Gate run 2026-09-10 (h12_orb_gate_run.py) — executed 3 times, all disclosed:
      run 1 aborted on a loader/DataFrame construction bug (no result produced);
      run 2 completed but INVALID — a target-sign defect inverted the short-side
      2R target and did not implement the locked spec; run 3 = the canonical
      observation. Zero strategy-parameter changes across runs (universe, K grid,
      entry, stop, 2R target, costs, WF, gates all unchanged).
      Artifacts: reports/research/h12_orb_gate_run.{py,json,log} +
      run1_loader_gap.log + run2_target_sign_bug.log.
- [x] Verdict: **H12 KILLED at the locked gates** (OOS 2022-03-06..2026-05-26,
      1543 days, 9bps): CAGR -60.4% / Sharpe -4.05 / PF 0.56 / maxDD -98.0% /
      win rate 31.8% / 24,013 trades (15.56/day) / folds 0/4; delay retention
      N/A (base CAGR < 0). BTC B&H same span: CAGR 17.5% / Sharpe 0.57 /
      maxDD -66.7%. Per-fold K selection: K=8 chosen in EVERY fold (least-negative
      train Sharpe: -2.0/-2.7/-3.4/-3.5 for K=8 vs -2.9/-3.4/-4.1/-4.1 for K=4
      and -5.5/-5.7/-6.0/-5.6 for K=2). All evaluated gates (g1-g6, g8, g9, g10)
      failed; recovery factor -0.62 with an open underwater episode. Breakout
      entries on 5m systematically reverted into the opposite ORB boundary:
      win rate 31.8% sits at the 2R breakeven (~33%) BEFORE the 18bps round-trip
      cost, so the book bleeds mechanically. Diversification check N/A (PASS-only
       clause; no blend numbers computed). Family CLOSED per kill rules; no re-spec.

---

# APPENDIX 10 (2026-09-10) — H13 pairs/cointegration statistical arbitrage

Motivation: after H11 (funding carry PASS) and H12 (ORB KILL), the remaining
genuinely untested swing family on disk is cross-sectional cointegration
stat-arb. Prior attempts on record are all materially different and are
disclosed: (a) `research/pairs_trading.py` — fixed 5 pairs, rolling-beta
ETH/SOL/BNB/DOGE/XRP vs BTC hedge on daily bars, ad-hoc grid window {30,60}d,
z_in {1.5,2.0}, z_exit 0, max_hold {10,20}, simple equity sim, ungated (no
walk-forward, no extended gates); (b) `research/pairs_spread.py` — fixed 6
pairs on 15m bars (day-trade family), z 2.0/0.5/4.0, WIN 200, max_hold 8 bars;
(c) the FAILED screen `eth_btc_relative_value`
(reports/research/candidate_screens/summary.json): ONE fixed pair
ETHUSDT|BTCUSDT, dev window 2021-01..2023-01, 168 trades, mean gross edge
-11.0bps, net PF 0.54, failed every screen check (raw edge, net PF, net R,
breadth). H13 differs materially: 136-pair panel, TRAIN-ONLY Engle-Granger
selection per WF fold (hedge ratio train-fit), top-N=3 portfolio, the locked
10-key OOS gate standard, 9bps costs. Loader patterns reused from
category_momentum_v2.load_daily (daily-resampled closes, common end date);
the pair simulator is new code sign-audited before the run.

**Data (locked):** /home/k4it0/Aegis_System/data/ has ZERO *_1d_* and ZERO
*_4h_* CSVs on disk; 33 *_1h_* CSVs. Daily bars are therefore derived from the
1h files: open = first hourly open of the UTC day, close = last hourly close.
Coverage for the 17 H11 symbols (counts taken BEFORE this registration, data
only): all 17 present; first/last: LTC 2020-01-09 / 2026-08-12; UNI 2020-09-18;
BNB,BTC,ETH,SOL,XRP 2020-09-23; AAVE,FIL 2020-10-16; HBAR 2021-03-17; OP
2022-06-01; INJ 2022-08-17; ICP 2022-09-27; APT 2022-10-19; ARB 2023-03-23;
SEI 2023-08-17; WIF 2024-01-18; all end 2026-08-12. Data hygiene: 12
symbol-days missing the hour-0 bar and 17 missing the hour-23 bar across all
17 pairs (edges; the day's first/last available bar is used); funding_rate is
non-null at every 08:00 and 16:00 UTC stamp. No 5m/15m data used.

**Universe (locked):** all C(17,2) = 136 pairs from the H11 universe {AAVE,
APT, ARB, BNB, BTC, ETH, FIL, HBAR, ICP, INJ, LTC, OP, SEI, SOL, UNI, WIF,
XRP}. A pair is eligible in a fold only if both legs have >= 180 joint daily
closes in that fold's TRAIN window.

**Pair selection (locked, TRAIN-ONLY per WF fold):** on the train window of
each fold k=1..4 (all master-calendar days strictly before the fold's first
day): for each candidate pair (A,B), x=log(close_A), y=log(close_B); fit OLS
with intercept x = alpha + beta*y + e (train only); require beta > 0.
Engle-Granger residual test: ADF on e with no constant, lag order by AIC over
p in 0..ceil(12*(n/100)^0.25); QUALIFY iff ADF t-stat < -3.3361 = MacKinnon
(2010) asymptotic 5% critical value for the EG residual test with one
regressor and a constant (equivalently p<0.05; source: statsmodels
adfvalues.mackinnoncrit / coint; the manual ADF was validated to 1e-6 against
statsmodels.tsa.stattools.adfuller on synthetic series before this
registration). Half-life filter: fit AR(1) dE_t = c + lambda*E_{t-1} + u on
train residuals; phi = 1+lambda; require 0 < phi < 1 and HL = -ln2/ln(phi) in
[0.5, 30] days (12h-30d in daily bars). Select top N=3 by most negative ADF
t-stat (ties: alphabetical). Fewer qualifiers -> trade what qualifies; zero
qualifiers -> fold flat. Selection and hedge ratio NEVER see fold data.

**Signal (locked):** spread s_t = logA_t - alpha - beta*logB_t with the fold's
train-fitted alpha,beta. z_t = (s_t - rolling_mean_W) / rolling_std_W, W=30
daily bars, min_periods=30, ddof=1. Entry at close t if flat and |z_t| >= 2:
z_t >= +2 -> SHORT spread (short A, long B); z_t <= -2 -> LONG spread (long A,
short B). Exit at close t in position if |z_t| <= 0.5, or stop |z_t| >= 4;
time stop when (t - entry_exec_idx + L) >= 30 bars (exactly 30 days of
holding). Re-entry allowed when flat after an exit (no cooldown).

**Execution (locked):** decision at bar close t, executed at the NEXT bar
open (t+L). Base L=1; delay test L=2 for EVERY entry and exit. Daily MTM on
open-to-open leg returns while held; positions open on a fold's last day are
marked to that day's close (fold-boundary artifact, disclosed). At each fold
start the book is flat; the last train day's close may produce the fold's
first-day entry signal (point-in-time).

**Sizing (locked):** fixed 1/17 book notional per pair slot (legs share the
slot): long-spread dollar shares A:+1/(1+beta), B:-beta/(1+beta); short-spread
mirrored. Up to 3 pairs -> book gross <= 3/17. No leverage, no vol targeting,
no cash yield.

**Costs (locked):** 9bps per leg-unit turnover; each leg entry = 1 unit,
exit = 1 unit -> a pair round trip = 4 units = 36bps of pair notional (18bps
at entry + 18bps at exit of the 1/17 slot), charged on the execution day.
INTENTIONALLY conservative vs strict leg-share accounting (legs share the
slot -> strict would be 18bps/round trip); locked as specified.

**Funding (locked):** both legs are perps. For every day d the position is
open across the 08:00 and 16:00 UTC stamps (entry open through the day before
exit; exit-day stamps not charged), funding PnL = -sum_legs pos_leg *
(r08_leg + r16_leg) where pos_leg is the signed leg share of pair notional and
r08/r16 are the 1h-file funding_rate values at those stamps (net across legs;
missing stamp = 0). Book contribution = /17.

**Walk-forward (locked):** identical master calendar to APPENDIX 3/4/8/9 —
v2.load_daily() px; warmup = K_CAT+PORT_LB+MIN_HIST+200+1 = 381 days;
idx_a = px.index[warmup:] (2021-01-24 -> 2026-08-12); 5 equal blocks; OOS =
blocks 1-4 stitched (starts 2022-03-06); folds = blocks 1-4. Per-fold
selection; fold returns stitched into the OOS series.

**Gates (locked 10-key standard):** g1 PF>1.2; g2 Sharpe>1.2; g3 MaxDD>-30%;
g4 >=3/4 folds positive (per-block CAGR>0); g5 OOS CAGR > BTC B&H CAGR same
span; g6 delay retention >=70% (base CAGR<=0 -> fail); g89 UW streak <=180d
AND yearly consistency (Sharpe > BTC in >=75% full years, no full year <
-15%); g10 all completed recoveries <=150d AND recovery factor >=0.75. PASS
iff all pass; any failure = KILL and the family closes.

**KILL rules (locked):** no threshold/param tuning after results; max 1
iteration = loader repairs only, disclosed. Single cost rung 9bps. Before the
first run: self-review of entry/exit/stop signs against this spec (H12 lost
runs to a sign defect); implementation repairs that restore compliance with
this locked spec are allowed and must be disclosed (no parameter changes).

**Diversification (locked, only on PASS):** corr(H13 daily OOS, champion HMM
daily) and corr(H13, H11 V2_63d) on the same span + 50/50 blend Sharpe vs
each. Unloadable series -> stated as a limitation, no invented numbers.

**Prediction (stated before the result):** daily cointegration on liquid
crypto perps is plausible but the published record is fragile. Prediction:
small positive gross edge at best; likely cost-fragile and odds-on to fail g5
(market-neutral CAGR vs a strong BTC B&H span) or g1/g2.
**State of crypto stat-arb (web, 2026):** recent work still reports positive
OOS results in crypto with careful design (Tadi & Witzany 2025, Financial
Innovation: copula + cointegration on Binance USDT-M futures; Palazzi 2025,
Journal of Futures Markets: lookback-optimized pairs beat B&H OOS), while the
broader pairs literature documents decaying profitability (Rad, Low & Faff)
and parameter-degradation/cointegration-stability risk from calibration to
deployment (Chen & Alexiou 2025, Journal of Asset Management). The honest
test is train-only selection + WF + costs, exactly as specified here.

## Status (APPENDIX 10)
- [x] Pre-registered 2026-09-10 BEFORE any H13 strategy result (data
      verification only preceded: file/coverage counts; ADF tooling validated
      on synthetic series; no pair was tested)
- [ ] Gate run (h13_pairs_gate_run.py) — interpreter
      /home/k4it0/Aegis_System/venv/bin/python; executed once (canonical);
      implementation repairs if any disclosed in the run log header
- [ ] Verdict

# APPENDIX 11 (2026-09-17, S20 addendum 4 / S21) — Meme-signal EV study: H14 paid boosts + H15 new profiles

**Directive:** master, 2026-09-17: "lets study leverage + memes + new coins..
we have solana radar" — approved as RESEARCH with kill rules (no trading, no
wallet, no registration). Study 1 of 3 (boosts first). S20 wording said
"pre-register H3+H4"; H3/H4 are taken (OI-flush, liq-cascade), so numbering
continues at **H14/H15**; the mapping is exact: H14 = paid boosts,
H15 = new profiles.

**Research question (locked):** do DexScreener *paid promotion signals*
(boosted / topboost) and *new-profile signals* on Solana tokens carry a
tradeable taker edge after realistic DEX costs, or are they toxic flow?
This is a signal-EV measurement, not a strategy backtest.

## Data (locked)
- Source: `data/signals.jsonl` (radar collector), sources
  `dexscreener:boosted`, `dexscreener:topboost`, `dexscreener:newprofile`.
  Mint = last path segment of `url`. Signal ts = `ts` (epoch).
- Sample: ALL signals with `ts <= run_time - 7d` (full 7d outcome window
  exists). Dedupe: earliest signal per (mint, class); a mint carrying both a
  boost signal and a profile signal enters BOTH class samples with its own
  earliest timestamp per class (classes are evaluated independently).
- As of 2026-09-17 15:30 CEST: 606 signals >=7d old (451 newprofile,
  123 boosted, 32 topboost) over 527 unique mints. Counts only — no return
  was computed before this appendix was committed.
- Prices: GeckoTerminal public API (no key). Pool selection rule: fetch
  `networks/solana/tokens/{mint}/pools`; among returned pools prefer pools
  with `pool_created_at <= signal_ts + 2h`, choose highest `reserve_in_usd`;
  if none qualifies, use highest-reserve pool and flag `migration_risk`.
  OHLCV: `networks/solana/pools/{pool}/ohlcv/hour`, hourly candles, fetched
  with `before_timestamp = signal_ts + 7d + 3600`.

## Measurement (locked)
- **Entry:** open of the first hourly candle with `open_time >= signal_ts`
  (honest, no look-ahead; models 0-60 min signal-to-fill latency at hourly
  granularity, stated limitation).
- **Exit:** open of the first candle at/after `signal_ts + H` for
  H in {1h, 6h, 24h, 7d} (candle within +1h slack accepted).
- **Returns:** gross = exit_open/entry_open - 1 per horizon.
- **Costs:** round-trip cost applied once per position: **2.00% standard**;
  sensitivity grid 1.50% / 3.00%. (DEX swap fee + slippage + priority fee;
  thin-pool slippage is *understated* by any flat cost — stated limitation.)
- **Dead / rug classification:** a position is `dead` if (a) no pool
  returned for the mint, or (b) no candle exists at exit (pool died), or
  (c) min(low) over the window <= 1% of entry (-99%+). Dead contributes
  -100% (gross) in the **all-in** view; excluded from the **tradeable**
  view. Both views are always reported.
- **Drawdown:** min(hourly low over window)/entry - 1.
- **Stratification (report-only, no selection):** entry-hour candle
  `volume_usd` buckets: <$10k, $10k-100k, >=$100k. Current pool
  `reserve_in_usd` reported as a limitation context (not point-in-time).
- Clock/latency/slippage beyond the above are NOT modeled; results are
  best-case for a taker.

## Hypotheses (locked, falsifiable)
- **H14 (paid boosts):** tokens at a paid-boost signal (boosted/topboost)
  are promotional flow; prediction: **negative net EV for a taker at all
  horizons**, rug/dead rate materially above the newprofile class's base
  (paid boosts cluster on live memecoins, not literal fresh rugs).
- **H15 (new profiles):** a new-profile signal marks a barely-traded token;
  prediction: **negative net EV at all horizons** and the **highest
  dead/rug rate** of the three sources (very new tokens die fastest).
- Stated before the result: both classes fail; the study's value is the
  measured body count, not a strategy.

## Decision rules (locked)
- **CONFIRMED HARMFUL (archive/kill):** mean net EV < 0 at ALL horizons in
  the tradeable view, for that class. Archive the trading idea; one recorded
  learning; no resurrection without new evidence + new gate.
- **CANDIDATE EDGE (promote to Phase 2, still no trading):** any
  class x horizon with tradeable-view mean net EV > +5.00% AND median net
  return > 0 AND n >= 30. Phase 2 = point-in-time walk-forward study with
  fill-level modeling, pre-registered separately. Entry into Phase 2 is a
  research promotion only — never live, never wallet.
- **INCONCLUSIVE:** n < 50 unique mints per class. Extend collection; re-run
  the IDENTICAL grid at 14d signal age. No parameter changes.
- **KILL rules (locked):** no threshold/parameter tuning after results; ONE
  canonical run of the grid; implementation repairs allowed only to restore
  compliance with this locked spec and must be disclosed in the run log
  header. Any deviation voids the run.

## Status (APPENDIX 11)
- [x] Pre-registered 2026-09-17 BEFORE any return computation (only counts,
  API schema, and tooling were verified; no token price/return was examined)
- [ ] Canonical run (studies/boost_ev_study.py) — interpreter
      /home/k4it0/Aegis_System/venv/bin/python; executed once; repairs if any
      disclosed in the run log header
- [ ] EV table + verdict
