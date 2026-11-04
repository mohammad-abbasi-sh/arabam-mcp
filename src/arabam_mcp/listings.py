"""Domain logic: parse arabam.com SSR pages into compact dicts (stdlib only).

Data sources (all embedded in the public HTML, no JS needed):
- Search pages: schema.org Vehicle JSON-LD blocks (one per listing card).
- Detail pages: schema.org Car JSON-LD + property-key/property-value spec table.
- Brand/model facets: a `var facets = [...]` JSON blob in the search page.
"""
from __future__ import annotations

import html as _html
import json
import re

_LDJSON_RE = re.compile(
    r'<script type="application/ld\+json">(.*?)</script>', re.S)
# JSON never contains ';', so the lazy match ends exactly at the assignment's
# closing bracket.
_FACETS_RE = re.compile(r"var facets = (\[.*?\])\s*;", re.S)
_ID_RE = re.compile(r"/(\d+)/?$")
_PRICE_RE = re.compile(r"([\d.]+)\s*(TL|TRY|EUR|USD|GBP)")


def _ldjson_items(html_text: str) -> list[dict]:
    items: list[dict] = []
    for block in _LDJSON_RE.findall(html_text):
        try:
            doc = json.loads(block)
        except json.JSONDecodeError:
            continue
        for it in doc if isinstance(doc, list) else [doc]:
            if isinstance(it, dict):
                items.append(it)
    return items


def _listing_id(url: str) -> str | None:
    m = _ID_RE.search(url or "")
    return m.group(1) if m else None


def _num(value) -> int | float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return int(str(value).replace(".", "").replace(",", ""))
    except (ValueError, AttributeError):
        return None


def parse_search(html_text: str) -> list[dict]:
    """Parse a search-results page into compact listing dicts."""
    out: list[dict] = []
    for it in _ldjson_items(html_text):
        if it.get("@type") != "Vehicle":
            continue
        offers = it.get("offers") or {}
        brand = it.get("brand") or {}
        url = offers.get("url") or it.get("url") or ""
        odo = it.get("mileageFromOdometer") or {}
        out.append({
            "id": _listing_id(url),
            "title": (it.get("name") or "").strip(),
            "brand": (brand.get("name") if isinstance(brand, dict)
                      else brand) or it.get("manufacturer") or "",
            "year": it.get("vehicleModelDate") or it.get("productionDate"),
            "km": _num(odo.get("value")) if isinstance(odo, dict) else None,
            "price_try": _num(offers.get("price")),
            "price_currency": offers.get("priceCurrency") or "",
            "url": url,
            "image": it.get("image") or "",
            "drive": it.get("driveWheelConfiguration") or "",
        })
    return out


def _parse_specs(html_text: str) -> dict:
    # Nested divs inside property-value (e.g. the "copy" widget on İlan No)
    # break naive regexes, so parse with the stdlib HTML parser.
    from html.parser import HTMLParser

    class _SpecParser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.depth = 0
            self.state: str | None = None  # "key" | "value"
            self.key_buf: list[str] = []
            self.val_buf: list[str] = []
            self.specs: dict[str, str] = {}
            self._start_depth = 0

        def handle_starttag(self, tag, attrs):
            cls = dict(attrs).get("class", "")
            if tag == "div" and "property-item" in cls.split():
                self.state = None
                self._start_depth = self.depth
                self.depth += 1
            elif tag == "div" and "property-key" in cls.split():
                self.state = "key"
                self.key_buf = []
                self.depth += 1
            elif tag == "div" and "property-value" in cls.split():
                self.state = "value"
                self.val_buf = []
                self.depth += 1
            elif self.state:
                self.depth += 1

        def handle_endtag(self, tag):
            if self.state:
                self.depth -= 1
                if tag == "div" and self.depth == self._start_depth:
                    k = "".join(self.key_buf).strip()
                    v = re.sub(r"\s+", " ", "".join(self.val_buf)).strip()
                    if k and v:
                        self.specs[k] = v
                    self.state = None

        def handle_data(self, data):
            if self.state == "key":
                self.key_buf.append(data)
            elif self.state == "value":
                self.val_buf.append(data)

    p = _SpecParser()
    p.feed(html_text)
    return p.specs


def _parse_price_text(html_text: str) -> dict:
    m = re.search(
        r'<div data-testid="desktop-information-price"[^>]*>\s*([^<]+?)\s*</div>',
        html_text)
    if not m:
        return {"price": None, "price_text": ""}
    text = _html.unescape(m.group(1)).strip()
    pm = _PRICE_RE.search(text)
    return {
        "price": _num(pm.group(1)) if pm else None,
        "price_currency": (pm.group(2) if pm else "").replace("TL", "TRY"),
        "price_text": text,
    }


def parse_detail(html_text: str) -> dict:
    """Parse a listing detail page into full spec dict."""
    car: dict = {}
    images: list[str] = []
    for it in _ldjson_items(html_text):
        if it.get("@type") == "Car":
            car = it
            break
    if car:
        imgs = car.get("image") or []
        images = [imgs] if isinstance(imgs, str) else list(imgs)
    specs = _parse_specs(html_text)
    price = _parse_price_text(html_text)
    brand = car.get("brand") or car.get("manufacturer") or ""
    if isinstance(brand, dict):
        brand = brand.get("name", "")
    return {
        "title": _html.unescape(car.get("name", "")).strip(),
        "brand": brand,
        "model": car.get("model") or "",
        "year": car.get("productionDate"),
        "transmission": car.get("vehicleTransmission") or "",
        "color": car.get("color") or "",
        "condition": car.get("itemCondition") or "",
        **price,
        "specs": specs,
        "images": images[:8],
        "url": (car.get("offers") or {}).get("url", "") if car else "",
    }


def parse_facets(html_text: str) -> list[dict]:
    m = _FACETS_RE.search(html_text)
    if not m:
        return []
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return []


def parse_brands(html_text: str) -> list[dict]:
    """All car brands from the root search page's facets blob."""
    for facet in parse_facets(html_text):
        for item in facet.get("Items") or []:
            subs = item.get("SubCategories") or []
            if subs and str(subs[0].get("RelativeUrl", "")).startswith(
                    "ikinci-el/otomobil/"):
                return [
                    {"name": s.get("Name", ""),
                     "slug": (s.get("RelativeUrl") or "").split("/")[-1],
                     "path": s.get("RelativeUrl") or "",
                     "count": s.get("Count", 0)}
                    for s in subs
                ]
    return []


def parse_models(html_text: str) -> list[dict]:
    """Models of the selected brand from the brand page's facets blob."""
    for facet in parse_facets(html_text):
        sel = facet.get("SelectedCategory") or {}
        if sel.get("IsBrand"):
            return [
                {"name": s.get("Name", ""),
                 "slug": (s.get("RelativeUrl") or "").split("/")[-1],
                 "path": s.get("RelativeUrl") or "",
                 "count": s.get("Count", 0)}
                for s in sel.get("SubCategories") or []
            ]
    return []


def price_stats(listings: list[dict]) -> dict:
    """Min/max/median/average over listing prices (TRY)."""
    prices = sorted(l["price_try"] for l in listings
                    if isinstance(l.get("price_try"), (int, float)))
    if not prices:
        return {"count": 0}
    n = len(prices)
    mid = n // 2
    median = (prices[mid] if n % 2 else (prices[mid - 1] + prices[mid]) / 2)
    return {
        "count": n,
        "currency": "TRY",
        "min": prices[0],
        "max": prices[-1],
        "median": median,
        "average": round(sum(prices) / n, 2),
    }
