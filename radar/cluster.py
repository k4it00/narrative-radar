import math
import time
from collections import Counter, defaultdict

from radar.model import Signal

MIN_CLUSTER = 2
SCORE_FLOOR = 6.0
TAU = 0.16


def _idf(n: int, df: Counter) -> dict[str, float]:
    return {t: math.log((n + 1) / (c + 1)) + 1.0 for t, c in df.items()}


def cluster_signals(signals: list[Signal]) -> list[dict]:
    live = [s for s in signals if s.weight > 0 and s.tokens]
    n = len(live)
    if n == 0:
        return []
    df = Counter()
    for s in live:
        for t in s.tokens:
            df[t] += 1
    drop = {t for t, c in df.items() if c > max(12, n // 8)}
    idf = _idf(n, df)

    vecs = []
    for s in live:
        toks = s.tokens - drop
        if not toks:
            vecs.append((s, {}))
            continue
        norm = math.sqrt(sum(idf[t] ** 2 for t in toks)) or 1.0
        vecs.append((s, {t: idf[t] / norm for t in toks}))

    centroids: list[dict[str, float]] = []
    members: list[list[int]] = []
    for idx, (s, v) in enumerate(vecs):
        if not v:
            continue
        best, best_sim = -1, 0.0
        for ci, cent in enumerate(centroids):
            small, big = (v, cent) if len(v) < len(cent) else (cent, v)
            sim = sum(w * big.get(t, 0.0) for t, w in small.items())
            if sim > best_sim:
                best, best_sim = ci, sim
        if best >= 0 and best_sim >= TAU:
            members[best].append(idx)
            m = len(members[best])
            for t, w in v.items():
                centroids[best][t] = centroids[best].get(t, 0.0) * (m - 1) / m + w / m
        else:
            centroids.append(dict(v))
            members.append([idx])

    now = time.time()
    narratives = []
    for ci, mem in enumerate(members):
        msigs = [live[i] for i in mem]
        if len(msigs) < MIN_CLUSTER:
            continue
        score = 0.0
        for s in msigs:
            age_days = max(0.0, (now - s.ts) / 86400)
            recency = 0.5 + 0.5 * math.exp(-age_days / 14.0)
            score += s.weight * recency
        srcs = {s.source.split(":")[0] for s in msigs}
        score *= 1.0 + 0.5 * (len(srcs) - 1)
        if len(msigs) < MIN_CLUSTER + 1 and len(srcs) < 2 and score < SCORE_FLOOR:
            continue
        cnt = Counter()
        for s in msigs:
            for t in (s.tokens - drop):
                cnt[t] += 1
        label_tokens = [t for t, c in cnt.most_common(6)
                        if c >= max(2, len(msigs) // 3) and t not in drop]
        narratives.append({
            "score": round(score, 2),
            "sources": sorted(srcs),
            "n_signals": len(msigs),
            "label_tokens": label_tokens,
            "signals": [s.to_dict() for s in sorted(
                msigs, key=lambda s: -s.weight)[:12]],
        })
    narratives.sort(key=lambda x: -x["score"])
    for i, nv in enumerate(narratives):
        nv["rank"] = i + 1
    return narratives[:10]
