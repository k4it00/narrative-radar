from dataclasses import dataclass, field, asdict


@dataclass
class Signal:
    source: str
    title: str
    summary: str
    url: str
    ts: float
    weight: float
    tokens: set[str] = field(default_factory=set)

    def to_dict(self):
        d = asdict(self)
        d["tokens"] = sorted(self.tokens)
        return d


def tokens_of(text: str, stop: set[str], min_len: int = 3, max_len: int = 24) -> set[str]:
    out = set()
    cur = []
    for ch in text.lower():
        if ch.isalnum() or ch in "-_.":
            cur.append(ch)
        else:
            if cur:
                w = "".join(cur).strip("-_.")
                if min_len <= len(w) <= max_len and w not in stop and not w.isdigit():
                    out.add(w)
                cur = []
    if cur:
        w = "".join(cur).strip("-_.")
        if min_len <= len(w) <= max_len and w not in stop and not w.isdigit():
            out.add(w)
    return out


STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "you",
    "are", "was", "were", "will", "can", "how", "what", "why", "who", "new",
    "all", "any", "not", "but", "has", "have", "had", "one", "two", "out",
    "get", "use", "via", "per", "its", "it's", "his", "her", "them", "they",
    "been", "more", "than", "then", "over", "just", "like", "about", "after",
    "before", "when", "where", "which", "while", "also", "only", "very",
    "much", "many", "some", "such", "here", "there", "being", "does", "did",
    "done", "now", "way", "day", "days", "week", "weeks", "month", "year",
    "https", "http", "www", "com", "org", "github", "reddit", "twitter",
    "says", "said", "top", "best", "vs", "eps", "etc",
}
