# H14/H15 Meme-signal EV study — canonical run

- Run (UTC): 2026-09-17T14:33:06Z -> 2026-09-17T17:07:04Z
- Spec: PRE_REGISTRATION.md APPENDIX 11 (locked fd94bb8). Script: studies/boost_ev_study.py @ 682c10d
- Sample: 600 signals >=7d old (135 boost, 465 newprofile), 542 unique mints
- Network calls: 1920 | HTTP errors: 8
- Repairs disclosed: ['pre-run (before canonical execution): collapse/DD windows exclude the exit candle (hourly lows after the exit open are future info; spec-intent fix, no parameter change)', 'pre-run (before canonical execution, transport only): parallel fetch pool + dispatch limiter 24 req/min + per-mint FetchError isolation (fetch failures are excluded and reported, never counted as dead); measurement spec unchanged']

Cost standard = 2.00% round trip; sensitivity 1.50%/3.00% in JSON.

## BOOST (H14)

n=135 signals / 133 mints (fetch-errors excluded: 2) | mean maxDD(7d)=-54.44% | migration-flagged: 0

| horizon | n tradeable | dead% | gross mean | net mean (2%) | median net | win% | p10 net | p90 net | all-in mean (2%) |
|---|---|---|---|---|---|---|---|---|---|
| 1h | 109 | +18.05% | -7.61% | -9.61% | -2.08% | +32.11% | -58.04% | +16.48% | -25.91% |
| 6h | 87 | +34.59% | -9.95% | -11.95% | -5.91% | +31.03% | -71.64% | +27.84% | -42.40% |
| 24h | 69 | +48.12% | -7.07% | -9.07% | -14.90% | +21.74% | -93.66% | +37.21% | -52.82% |
| 7d | 32 | +75.94% | +6.44% | +4.44% | -29.08% | +15.62% | -96.56% | +10.97% | -74.87% |

Dead reasons (24h): {"collapse_99": 9, "no_exit_candle": 49, "no_entry_candle": 4, "no_pool": 2}

Source split (24h):

- dexscreener:topboost: n=133, dead%=+48.12%, mean net 24h=-9.07%

Volume buckets (tradeable mean net):

| bucket | 1h n/net | 6h n/net | 24h n/net | 7d n/net |
|---|---|---|---|---|
| lt10k | 82 / -5.36% | 82 / -8.81% | 82 / -19.56% | 82 / -36.41% |
| 10k_100k | 32 / -14.55% | 32 / -16.66% | 32 / +18.83% | 32 / +79.81% |
| ge100k | 13 / -20.68% | 13 / -17.70% | 13 / -68.91% | 13 / -65.50% |
| unknown | 6 / n/a | 6 / n/a | 6 / n/a | 6 / n/a |

**Verdict (boost): MIXED** (candidate horizons: none)

## NEWPROFILE (H15)

n=465 signals / 459 mints (fetch-errors excluded: 6) | mean maxDD(7d)=-45.14% | migration-flagged: 4

| horizon | n tradeable | dead% | gross mean | net mean (2%) | median net | win% | p10 net | p90 net | all-in mean (2%) |
|---|---|---|---|---|---|---|---|---|---|
| 1h | 340 | +25.93% | -9.12% | -11.12% | -4.62% | +19.12% | -58.04% | +9.97% | -34.16% |
| 6h | 271 | +40.96% | -15.56% | -17.56% | -15.28% | +18.45% | -79.81% | +23.20% | -51.32% |
| 24h | 194 | +57.73% | -23.45% | -25.45% | -30.93% | +18.04% | -90.68% | +29.93% | -68.49% |
| 7d | 43 | +90.63% | -18.72% | -20.72% | -59.49% | +18.60% | -97.55% | +25.79% | -92.57% |

Dead reasons (24h): {"no_exit_candle": 205, "collapse_99": 9, "no_entry_candle": 16, "no_pool": 35}

Volume buckets (tradeable mean net):

| bucket | 1h n/net | 6h n/net | 24h n/net | 7d n/net |
|---|---|---|---|---|
| lt10k | 302 / -6.79% | 302 / -12.01% | 302 / -26.47% | 302 / -29.98% |
| 10k_100k | 75 / -19.93% | 75 / -31.41% | 75 / -15.89% | 75 / +5.72% |
| ge100k | 31 / -25.15% | 31 / -20.39% | 31 / -50.16% | 31 / -61.13% |
| unknown | 51 / n/a | 51 / n/a | 51 / n/a | 51 / n/a |

**Verdict (newprofile): CONFIRMED_HARMFUL** (candidate horizons: none)

## Limitations (pre-stated in APPENDIX 11)

- Hourly granularity; next-hourly-open entry models 0-60 min latency.
- Flat round-trip cost understates thin-pool slippage; all results are best-case for a taker.
- Pool reserve is read now, not point-in-time; entry-hour volume is the point-in-time activity proxy.
- Migration-flagged tokens (chosen pool created after signal +2h) carry pool-identity risk.

No trading, no wallet, no registration — research measurement only.
