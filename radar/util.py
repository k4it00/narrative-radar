import json
import time
import urllib.request
import urllib.error

UA = "narrative-radar/1.0 (solana ecosystem research; contact: repo README)"
TIMEOUT = 25


def http_get(url: str, headers: dict | None = None, retries: int = 2) -> bytes:
    hdrs = {"User-Agent": UA}
    if headers:
        hdrs.update(headers)
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=hdrs)
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"GET failed {url}: {last_err}")


def get_json(url: str, headers: dict | None = None):
    return json.loads(http_get(url, headers).decode("utf-8", "replace"))
