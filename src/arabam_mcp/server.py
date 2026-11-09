"""MCP server: unofficial read-only access to arabam.com car listings."""
from __future__ import annotations

import json
import sys

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import listings as _listings

mcp = FastMCP("arabam-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for arabam.com, Türkiye's used-car \
marketplace (~176k listings). Data comes from arabam.com's public \
server-rendered pages: listing cards carry schema.org Vehicle JSON-LD \
(id, title, brand, year, km, price), detail pages carry a full spec table \
(İlan No, İlan Tarihi, Marka, Seri, Model, Yıl, Kilometre, Vites, Yakıt, \
Kasa, Renk, Motor hacmi/gücü, Çekiş, hasar kaydı, Kimden) plus the price. \
Prices are in Turkish Lira (TRY) unless noted. Brand slugs look like \
"bmw"; model slugs like "bmw-3-serisi" (see arabam_list_brands / \
arabam_list_models). Read-only, no login, no API key. Be polite: the \
server spaces requests ~0.8s apart. Built by Mohammad Abbasi \
(mohammad-abbasi-sh) — https://almanibama.ir · https://mabbasi.ir — Turkey MCP factory.\
"""


def _err(e: Exception) -> str:
    return json.dumps({"error": str(e)}, ensure_ascii=False)


@mcp.tool()
def arabam_search(brand: str = "", model: str = "", page: int = 1) -> str:
    """Search used-car listings. brand: slug like "bmw" (optional), \
model: slug like "bmw-3-serisi" (optional, overrides brand), \
page: 1..50. Returns compact listings with id, title, brand, year, \
km, price_try and detail URL."""
    try:
        html = _http.fetch_search(brand or None, model or None, page)
        rows = _listings.parse_search(html)
    except _http.ArabamError as e:
        return _err(e)
    return json.dumps(
        {"brand": brand, "model": model, "page": page,
         "count": len(rows), "listings": rows},
        ensure_ascii=False,
    )


@mcp.tool()
def arabam_listing_detail(url: str) -> str:
    """Full detail of one listing: title, price, 19-field spec table \
(Marka, Seri, Model, Yıl, Kilometre, Vites, Yakıt, Renk, Motor, \
hasar kaydı, Kimden…), images. url: the listing URL from arabam_search."""
    try:
        html = _http.fetch_detail(url)
        d = _listings.parse_detail(html)
    except _http.ArabamError as e:
        return _err(e)
    return json.dumps(d, ensure_ascii=False)


@mcp.tool()
def arabam_list_brands() -> str:
    """All ~77 car brands on arabam.com with listing counts and URL slugs \
(use the slug with arabam_search / arabam_list_models)."""
    try:
        html = _http.fetch_brands_page()
        brands = _listings.parse_brands(html)
    except _http.ArabamError as e:
        return _err(e)
    return json.dumps(
        {"count": len(brands), "brands": brands}, ensure_ascii=False)


@mcp.tool()
def arabam_list_models(brand: str) -> str:
    """Models of one brand with listing counts and URL slugs. \
brand: slug like "bmw" (from arabam_list_brands)."""
    try:
        html = _http.fetch_brand_page(brand)
        models = _listings.parse_models(html)
    except _http.ArabamError as e:
        return _err(e)
    if not models:
        return json.dumps(
            {"error": f"no models found for brand {brand!r} — "
                      "check the slug with arabam_list_brands"},
            ensure_ascii=False)
    return json.dumps(
        {"brand": brand, "count": len(models), "models": models},
        ensure_ascii=False)


@mcp.tool()
def arabam_price_stats(brand: str = "", model: str = "",
                       pages: int = 3) -> str:
    """Market stats for a brand/model: count, min, max, median and \
average price (TRY) across the first N search pages \
(pages: 1..5, default 3)."""
    pages = max(1, min(int(pages), 5))
    rows: list[dict] = []
    try:
        for p in range(1, pages + 1):
            html = _http.fetch_search(brand or None, model or None, p)
            rows.extend(_listings.parse_search(html))
    except _http.ArabamError as e:
        return _err(e)
    stats = _listings.price_stats(rows)
    stats.update({"brand": brand, "model": model, "pages_scanned": pages})
    return json.dumps(stats, ensure_ascii=False)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
