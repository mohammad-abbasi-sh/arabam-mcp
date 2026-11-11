"""HTTP layer for arabam_mcp — polite scraping of public SSR pages.

arabam.com serves fully server-rendered pages behind a bot wall (verified 2026-11-10: plain httpx gets 403 / connection reset; curl-cffi impersonation required): listing data
comes from embedded JSON-LD (schema.org Vehicle/Car) and a facets JSON blob.
We keep requests gentle (one at a time, ~0.8s apart) and read-only.
"""
from __future__ import annotations

import re
import time


BASE = "https://www.arabam.com"

TIMEOUT = 25.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_last_fetch = 0.0


class ArabamError(RuntimeError):
    pass





def search_url(brand: str | None, model: str | None, page: int) -> str:
    slug_re = re.compile(r"^[a-z0-9][a-z0-9-]*$")
    path = "ikinci-el/otomobil"
    if model:
        m = model.strip().lower()
        if not slug_re.fullmatch(m):
            raise ArabamError(f"bad model slug: {model!r}")
        path += f"/{m}"
    elif brand:
        b = brand.strip().lower()
        if not slug_re.fullmatch(b):
            raise ArabamError(f"bad brand slug: {brand!r}")
        path += f"/{b}"
    url = f"{BASE}/{path}"
    if page and page > 1:
        url += f"?page={int(page)}"
    return url


from curl_cffi import requests as _r

_HEADERS = {
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport. Added 2026-11-10 (fleet audit fix).
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _r.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise ArabamError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise ArabamError(f"network error fetching {url}: {last_exc}") from last_exc


def fetch(url: str) -> str:
    """GET a page; raises ArabamError on failure or bot-wall."""
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        resp = _request(url, _HEADERS)
    except ArabamError:
        raise
    except Exception as e:
        raise ArabamError(f"network error fetching {url}: {e}") from e
    _last_fetch = time.monotonic()
    if resp.status_code == 403:
        raise ArabamError(
            "arabam.com refused the request (HTTP 403, bot wall) — try again later"
        )
    if resp.status_code == 429:
        raise ArabamError(
            "arabam.com rate-limited the request (HTTP 429) — try again later"
        )
    if resp.status_code != 200:
        raise ArabamError(f"arabam.com returned HTTP {resp.status_code} for {url}")
    text = resp.text
    if 'name="description" content="px-captcha"' in text or "PerimeterX" in text:
        raise ArabamError("arabam.com is showing a bot check for this request")
    return text


def fetch_search(brand: str | None = None, model: str | None = None,
                 page: int = 1) -> str:
    if page is not None and (int(page) < 1 or int(page) > 50):
        raise ArabamError("page must be between 1 and 50")
    return fetch(search_url(brand, model, int(page) if page else 1))


def fetch_detail(url: str) -> str:
    u = url.strip()
    if u.startswith("/"):
        u = BASE + u
    if not re.fullmatch(r"https://www\.arabam\.com/ilan/[a-z0-9\-/]+", u):
        raise ArabamError(
            "detail URL must be an arabam.com /ilan/ listing URL "
            "(get one from arabam_search first)"
        )
    return fetch(u)


def fetch_brands_page() -> str:
    return fetch(f"{BASE}/ikinci-el/otomobil")


def fetch_brand_page(brand: str) -> str:
    return fetch(search_url(brand, None, 1))


def health_check() -> dict:
    """One polite probe of the source site.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `arabam_health` tool
    and the daily smoke CI. Added 2026-11-10 (fleet audit fix).
    """
    url = "https://www.arabam.com/"
    try:
        fetch(f"{BASE}/")
    except ArabamError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
