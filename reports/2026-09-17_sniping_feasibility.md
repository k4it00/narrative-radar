# F1 — New-coin sniping feasibility (S20 addendum 4, Study 3)

- Spec: PRE_REGISTRATION.md APPENDIX 13 (locked 92b0065), prediction locked before recon: NOT FEASIBLE.
- Scope: desk research + arithmetic only. No wallet created, no transactions, no bot deployed.
- Verdict: **NOT FEASIBLE for $500 capital on our stack.** Cost/EV tables below; sources cited; unverifiable cells marked UNVERIFIED.

## 1. Fixed cost stack (monthly)

| Line | Low | Base | High | Source / note |
|---|---|---|---|---|
| Low-latency RPC (staked) | $0 (free tier) | $50 | $250+ | Public tier prices vary; **UNVERIFIED exact tiers** — free/public RPC lacks stake-weighted ingress |
| VPS near region | $5 | $10 | $20 | commodity; latency to leaders still dominates without colocation |
| Bot software | $0 (OSS) | $0 | $50+/mo | OSS exists; the edge is infra+flow, not the bot code |
| **Fixed total** | **$5** | **$60** | **$320+** | vs $500 capital: base = **12%/month** of capital burned before any trade |

A single contested landing at professional fee levels (Jito's own sendTransaction guidance
example splits 0.7 SOL priority + 0.3 SOL tip ≈ 1.0 SOL total) costs ~$76 at SOL≈$76 —
**15% of the entire capital per attempt**. Even a modest contested bid (0.01–0.05 SOL ≈
$0.76–$3.8) costs 0.15–0.76% of capital per attempt, win or lose.

## 2. Per-attempt costs

| Item | Range | Note |
|---|---|---|
| Base fee | 0.000005 SOL | fixed, per signature |
| Priority fee (contested launch) | 0.001–0.05+ SOL | quiet-network average ~0.000056 SOL is irrelevant for launches |
| Jito tip (bundle path) | settles only if bundle lands | exact current minimum **UNVERIFIED**; contested tiers far above it |
| Token account rent | ~0.002 SOL | refundable on close, locked while held |
| DEX round-trip costs | ~1.5–3% of notional | swap fees + curve slippage (same ladder as APPENDIX 11) |
| Rug loss (tail) | −80% to −100% of position | see §4 |

## 3. Latency: we are structurally last in the queue

- Slot time ~400 ms; Jito runs discrete ~50 ms bundle auctions assembling blocks
  (Galaxy Research, Q4 2025). Professionals run colocated infrastructure + Jito
  shredstream/presigned transactions.
- **Public/unstaked RPC = the 20% lane**: priority fees order you *at* the leader but do
  not get you *to* the leader; stake-weighted QoS fills staked lanes first, and public RPC
  failures (rate-limit queuing, slot drift, no stake-weighted routing) are silent
  (Yavorovych, Jun 2026; Chorus One latency research: priority-fee size does not
  influence time-to-inclusion).
- Home connection, no colocation, no shred access → we are behind every professional
  and every insider. In a first-come auction, fills we *do* get are adversely selected:
  we land the moments nobody faster wanted.

## 4. Competition: the game is insider-collusive at the start

- Pine Analytics (Apr 2025; re-covered by Gate, Mar 2026): **>50% of pump.fun tokens are
  bought in the same block they are created**; deployer-funded sniper wallets did this
  across 15,000+ launches in one month extracting 15,000+ SOL; **87% of those insider
  snipes were profitable**; snipers typically exit within 1–2 swaps — i.e., "retail
  traders unknowingly provide exit liquidity."
- Q2 2026 context (Blockworks): launchpad volume −33% QoQ, memecoin activity unwinding,
  2.6M tokens created in the quarter (pump.fun ~97%). The alpha-per-token for outsiders
  is shrinking while the insider share of early flow persists.
- Our only empirical proxy: APPENDIX 11 (H14/H15) measures **late-buyer** EV at signal
  time — strictly worse than snipe time. Outcome pending; if it is negative, sniping from
  our seat is worse by construction.

## 5. EV model (per attempt, position size $50 = 10% of capital)

EV/attempt = P(fill) × [E(gain|fill) × $50 − round-trip cost] − fixed per-attempt costs.
Per-attempt costs (won or lost): priority+tip ~0.01 SOL ≈ $0.76 + rent ~0.002 SOL ≈ $0.15.
Round trip: 2% of $50 = $1.

| Scenario | P(fill) | E(gain\|fill) | EV per filled attempt | EV/attempt | Monthly (5/day) |
|---|---|---|---|---|---|
| Optimistic ("we get insider-grade fills") | 0.30 | +25% ($12.5) | +$9.6 | +$2.9 | +$432 |
| Base (adverse selection) | 0.30 | −15% (−$7.5) | −$9.4 | −$2.8 | −$424 |
| Pessimistic (pros take the winners we see) | 0.15 | −40% (−$20) | −$21.9 | −$3.3 | −$493 |

- The optimistic cell requires E(gain|fill) of a **deployer-funded insider wallet**
  (87% profitable, exits in 1–2 swaps, §4) — it is not an open-entry seat. The
  structural facts (§3–§4) are exactly what forces P(fill) and gain|fill to be
  inversely correlated for outsiders: when we fill, nobody faster wanted the other side.
- Even breaking even at the base case requires the optimistic seat; the desk is
  **negative-EV under every parameterization actually available to us**.
- Fixed $60/mo against $500 = 12% before any trade — the optimistic row is the only
  one that covers it, and it is not available.

## Verdict (per APPENDIX 13 decision rules)

1. **Do not build.** Negative EV under base and pessimistic assumptions; the optimistic
   cell (free RPC, no bad fills) is contradicted by §3–§4 evidence (queue position and
   adverse selection are structural, not tunable).
2. No wallet is created; no registration; no spend (BIBLE Art. V: execution stays
   disabled; wallet creation is master-gated and not requested).
3. Recorded for the money track: at $500, sniping is the worst available use of capital —
   infra alone costs 12–22%/month of the account.
4. Re-open condition (locked): only if (a) a validated edge from the radar gate exists AND
   (b) infra required is <$20/mo AND (c) master explicitly authorizes a snipe budget.
   None hold today.

## Sources
- Sniper Bot Index (Sep 2026): priority fees vs Jito bundles, base fee 5,000 lamports/sig.
- Jito docs (Low Latency Transaction Send): bundle tips, 70/30 split example, tip only on land.
- Yavorovych (Jun 2026): public-RPC 20% lane, pre-signing, shredstream tiers; Chorus One latency research (2024) cited therein.
- Pine Analytics via AiCoin (Jun 2025) / Gate Learn (Mar 2026): same-block deployer-funded sniping, 87% insider profitability, retail exit-liquidity.
- Blockworks Solana Tokenholder Reports Q1/Q2 2026: launchpad volume −33% QoQ, 2.6M tokens/quarter.
- Galaxy Research Q4 2025: Jito ~50 ms auctions, colocated infra.
- UNVERIFIED cells: current exact RPC tier prices and minimum Jito tip; treated as ranges, not invented numbers.
