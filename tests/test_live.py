"""Live tests — hit the real arabam.com. Cautious: a handful of requests,
spaced ~0.8s apart by the http layer.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set ARABAM_SKIP_LIVE=1)
"""
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from arabam_mcp import http as _H
from arabam_mcp import listings as _L

pytestmark = pytest.mark.live
SKIP = os.environ.get("ARABAM_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="ARABAM_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_search_page_parses(self):
        html = _H.fetch_search(None, None, 1)
        rows = _L.parse_search(html)
        self.assertGreater(len(rows), 0, "search page should list vehicles")
        priced = [r for r in rows if r["price_try"]]
        self.assertGreater(len(priced), 0)
        for r in rows[:5]:
            self.assertTrue(r["id"] and r["id"].isdigit())
            self.assertTrue(r["url"].startswith("https://www.arabam.com/ilan/"))
        print(f"\nLIVE: {len(rows)} listings on page 1; "
              f"cheapest seen: {min(r['price_try'] for r in priced):,} TRY")

    def test_brand_search(self):
        html = _H.fetch_search("bmw", None, 1)
        rows = _L.parse_search(html)
        self.assertGreater(len(rows), 0)
        brands = {r["brand"] for r in rows if r["brand"]}
        self.assertIn("BMW", brands)

    def test_detail_page_parses(self):
        html = _H.fetch_search("honda", None, 1)
        rows = _L.parse_search(html)
        self.assertGreater(len(rows), 0)
        d = _L.parse_detail(_H.fetch_detail(rows[0]["url"]))
        self.assertTrue(d["title"])
        self.assertGreater(len(d["specs"]), 5)
        self.assertIn("Marka", d["specs"])
        print(f"\nLIVE detail: {d['title'][:60]} | {d['price_text']}")

    def test_brands_list(self):
        brands = _L.parse_brands(_H.fetch_brands_page())
        self.assertGreater(len(brands), 50)
        names = [b["name"] for b in brands]
        self.assertIn("BMW", names)
        self.assertIn("Honda", names)
        print(f"\nLIVE: {len(brands)} brands")

    def test_models_list(self):
        models = _L.parse_models(_H.fetch_brand_page("bmw"))
        self.assertGreater(len(models), 5)
        names = [m["name"] for m in models]
        self.assertIn("3 Serisi", names)
        print(f"\nLIVE: BMW models: {', '.join(names[:8])}")


if __name__ == "__main__":
    unittest.main()
