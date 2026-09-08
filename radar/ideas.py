from collections import Counter

CATEGORIES = {
    "ai-agents": ["agent", "agents", "ai", "llm", "gpt", "bot", "autonomous", "swarm", "eliza"],
    "defi": ["defi", "dex", "amm", "liquidity", "yield", "swap", "vault", "lending", "perp", "perps", "orderbook"],
    "memecoins": ["memecoin", "memecoins", "pump", "moonshot", "viral", "meme"],
    "depin": ["depin", "mining", "mesh", "wireless", "sensor", "compute", "gpu", "storage"],
    "payments": ["payment", "payments", "stablecoin", "stablecoins", "usdc", "usdg", "remittance", "merchant"],
    "gaming": ["game", "gaming", "nft", "nfts", "metaverse", "player"],
    "rwa": ["rwa", "tokenized", "treasury", "real-world", "bonds", "commodity"],
    "infra": ["rpc", "indexer", "sdk", "validator", "node", "infra", "zk", "light", "client"],
    "security": ["audit", "exploit", "hack", "security", "drainer", "scam", "phish"],
    "consumer": ["social", "creator", "app", "mobile", "wallet", "consumer"],
}

IDEA_TEMPLATES = {
    "ai-agents": [
        ("Agent capability marketplace on Solana",
         "Agents that pay each other for tools/data need a settlement rail with sub-cent fees."),
        ("On-chain agent reputation registry",
         "As agent count grows, verifiable track records (payout history, task success) become the trust layer."),
        ("Natural-language portfolio copilot with program constraints",
         "Users want agent-managed positions but need hard on-chain guardrails the agent cannot override."),
    ],
    "defi": [
        ("Cross-pool MEV-aware router with simulation guardrails",
         "Fragmented liquidity across CLMM pools makes naive routing expensive at size."),
        ("Automated LP position manager for concentrated liquidity",
         "Active-range management is manual and time-costly for retail LPs."),
        ("Real-time risk dashboard for perp traders",
         "Funding + liquidation data exist on-chain but are not surfaced in one decision view."),
    ],
    "memecoins": [
        ("Liquidity-health scanner for new launches",
         "Most launches die to honeypots and thin liquidity; a pre-trade health score has clear demand."),
        ("Social-momentum tracker wired to on-chain flows",
         "Price moves lag social spikes; joining the two gives an early-warning feed."),
    ],
    "depin": [
        ("DePIN coverage explorer with verifiable uptime",
         "Buyers of physical network coverage need proof-of-service maps, not marketing."),
        ("DePIN token sink designer toolkit",
         "Most DePIN tokens lack demand sinks; a reusable bonding/burn module is reusable infra."),
    ],
    "payments": [
        ("Merchant checkout widget with auto-stablecoin conversion",
         "Accepting volatile crypto scares merchants; instant USDC settlement removes the fear."),
        ("Payroll streaming for global teams",
         "Per-second stablecoin streams fit contractor work and dodge banking delays."),
    ],
    "gaming": [
        ("On-chain achievement passport",
         "Portable player reputation across games enables reward syndication."),
        ("Serverless game asset marketplace kit",
         "Small studios lack custody/royalty plumbing; a drop-in SDK lowers the barrier."),
    ],
    "rwa": [
        ("RWA proof-of-reserve oracle kit",
         "Tokenized assets need recurring attestation plumbing to stay trusted."),
        ("Compliance-aware transfer hooks library",
         "Issuers need allow/deny rules on transfers without hard-forking their program."),
    ],
    "infra": [
        ("High-signal Solana program diff watcher",
         "Anchored upgrades change behavior silently; a diff-alert service protects integrators."),
        ("Free-tier Solana event stream to webhooks",
         "Small teams need push notifs on program events without running infra."),
    ],
    "security": [
        ("Drainer-pattern early-warning feed for wallets",
         "Frontend builders can auto-warn users when a destination matches known drainer patterns."),
        ("Pre-flight simulation Linter for dApp teams",
         "Dry-running unsigned transactions against heuristics catches approvals gone wrong."),
    ],
    "consumer": [
        ("Shared-wallet allowances for families/teams",
         "Spending controls on-chain are stronger than card limits and barely exist."),
        ("Creator tip-stream with public receipts",
         "Tipping with verifiable on-chain receipts doubles as creator analytics."),
    ],
}

GENERIC = [
    ("Signal dashboard for this narrative",
     "Consolidate the underlying feeds below into one live view with alerts."),
    ("Indexer/analytics for the entities named in the signals",
     "The named projects lack public dashboards; usage stats are currently anecdotal."),
    ("Notification bot wired to the leading indicators below",
     "Early movers in this narrative are discoverable programmatically before consensus forms."),
]


def _category(label_tokens: list[str], signals: list[dict]) -> str:
    text = " ".join(label_tokens) * 3 + " " + " ".join(
        s["summary"].lower() for s in signals)
    scores = Counter()
    for cat, kws in CATEGORIES.items():
        for kw in kws:
            if kw in text:
                scores[cat] += 1
    return scores.most_common(1)[0][0] if scores else "infra"


def _fmt(sig: dict) -> str:
    src = sig["source"]
    title = sig["summary"].split(" :: ")[0]
    return f"{src} | {title}"


def _names(signals: list[dict]) -> list[str]:
    out = []
    for s in signals[:8]:
        t = s["summary"]
        if t.startswith("[" ) or " :: " in t:
            head = t.split(" :: ")[0]
        else:
            head = t
        if s["source"].startswith("github") and "]" in head:
            seg = head.split("]", 1)[1].strip()
            out.append(seg.split(" stars=")[0].strip())
        elif s["source"].startswith("superteam"):
            seg = head.split("'")
            if len(seg) > 1:
                out.append(f"Superteam Earn: {seg[1]}")
        elif s["source"].startswith("dexscreener"):
            for part in head.split():
                if len(part) >= 8 and part.isalnum():
                    out.append(part[:8] + "…")
        else:
            out.append(head[:70])
    seen, res = set(), []
    for n in out:
        if n and n not in seen:
            seen.add(n)
            res.append(n)
    return res[:4]


def generate_ideas(narrative: dict) -> list[dict]:
    label_tokens = narrative.get("label_tokens", [])
    signals = narrative.get("signals", [])
    cat = _category(label_tokens, signals)
    picks = IDEA_TEMPLATES.get(cat, [])[:3]
    if len(picks) < 3:
        picks = (picks + GENERIC)[:3]
    names = _names(signals)
    name_ctx = ", ".join(names) if names else "the leading signals"
    ideas = []
    for i, (title, why) in enumerate(picks, 1):
        hook = _fmt(signals[i % len(signals)]) if signals else "n/a"
        ideas.append({
            "title": title,
            "why_now": why,
            "evidence": "; ".join(_fmt(s) for s in signals[:3]),
            "tie_in": f"Named demand signals: {name_ctx}. Hook: {hook}",
        })
    return ideas
