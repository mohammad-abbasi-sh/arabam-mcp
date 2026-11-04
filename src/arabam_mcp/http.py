"""HTTP layer for arabam_mcp — polite scraping of public SSR pages.

arabam.com serves fully server-rendered pages with no bot wall: listing data
comes from embedded JSON-LD (schema.org Vehicle/Car) and a facets JSON blob.
We keep requests gentle (one at a time, ~0.8s apart) and read-only.
"""
from __future__ import annotations

import os
import re
import time

import httpx

BASE = "https://www.arabam.com"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)
TIMEOUT = 25.0
MIN_INTERVAL = 0.8  # seconds between requests — be polite

_last_fetch = 0.0


class ArabamError(RuntimeError):
    pass


def _client() -> httpx.Client:
    # NOTE: proxy URL is read from the environment but never logged.
    # trust_env=False because httpx fails to parse bracketed IPv6 entries
    # (e.g. [::1]) that some environments put in no_proxy.
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    # Standard SSL_CERT_FILE convention lets MITM-proxied environments
    # point at a CA bundle that trusts the proxy; default uses certifi,
    # which is correct for normal users.
    verify: object = True
    cafile = os.environ.get("SSL_CERT_FILE")
    if cafile:
        import ssl

        verify = ssl.create_default_context(cafile=cafile)
    return httpx.Client(
        headers={"User-Agent": UA, "Accept-Language": "tr-TR,tr;q=0.9"},
        timeout=TIMEOUT,
        proxy=proxy or None,
        verify=verify,
        trust_env=False,
        follow_redirects=True,
    )


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


def fetch(url: str) -> str:
    """GET a page; raises ArabamError on failure or bot-wall."""
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    try:
        with _client() as c:
            r = c.get(url)
    except httpx.HTTPError as e:
        raise ArabamError(f"network error fetching {url}: {e}") from e
    _last_fetch = time.monotonic()
    if r.status_code != 200:
        raise ArabamError(f"arabam.com returned HTTP {r.status_code} for {url}")
    text = r.text
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
