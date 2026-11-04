"""Offline tests — parse real captured arabam.com fixtures (no network)."""
import json
import pathlib
import re
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from arabam_mcp import listings as _L

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _ldjson_script(items: list[dict]) -> str:
    return ("<html><head>" + "".join(
        f'<script type="application/ld+json">{json.dumps(i, ensure_ascii=False)}</script>'
        for i in items) + "</head></html>")


class TestParseSearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = json.loads((FIX / "search_vehicles.json").read_text())
        cls.html = _ldjson_script(cls.items)

    def test_three_vehicles_parsed(self):
        rows = _L.parse_search(self.html)
        self.assertEqual(len(rows), 3)

    def test_first_listing_fields(self):
        r = _L.parse_search(self.html)[0]
        self.assertEqual(r["id"], "45291610")
        self.assertEqual(r["brand"], "Honda")
        self.assertEqual(r["year"], 1998)
        self.assertEqual(r["km"], 330000)
        self.assertEqual(r["price_try"], 425000)
        self.assertEqual(r["price_currency"], "TRY")
        self.assertTrue(r["url"].startswith("https://www.arabam.com/ilan/"))

    def test_listing_id_from_url(self):
        self.assertEqual(
            _L._listing_id("https://www.arabam.com/ilan/x/y/45291610"), "45291610")
        self.assertIsNone(_L._listing_id("https://www.arabam.com/ilan/x/y/"))

    def test_missing_offers_does_not_crash(self):
        rows = _L.parse_search(_ldjson_script(
            [{"@type": "Vehicle", "name": "bare"}]))
        self.assertEqual(len(rows), 1)
        self.assertIsNone(rows[0]["id"])
        self.assertIsNone(rows[0]["price_try"])

    def test_non_vehicle_blocks_ignored(self):
        html = _ldjson_script(
            [{"@type": "BreadcrumbList"}, {"@type": "Vehicle", "name": "v"}])
        self.assertEqual(len(_L.parse_search(html)), 1)


class TestParseDetail(unittest.TestCase):
    def test_specs_parsed(self):
        html = (FIX / "detail_specs.html").read_text()
        d = _L.parse_detail(html)
        self.assertIn("Marka", d["specs"])
        self.assertEqual(d["specs"]["Marka"], "Honda")
        self.assertEqual(d["specs"]["Kilometre"], "330.000 KM")
        self.assertEqual(d["specs"]["Kimden"], "Galeriden")

    def test_html_entities_unescaped(self):
        d = _L.parse_detail((FIX / "detail_specs.html").read_text())
        self.assertIn("Düz", d["specs"]["Vites tipi"])
        self.assertIn("Önden Çekiş", d["specs"]["Çekiş"])

    def test_price_parsed(self):
        d = _L.parse_detail((FIX / "detail_price.html").read_text())
        self.assertEqual(d["price"], 425000)
        self.assertEqual(d["price_currency"], "TRY")
        self.assertEqual(d["price_text"], "425.000 TL")

    def test_car_jsonld_parsed(self):
        car = json.loads((FIX / "detail_car.json").read_text())
        d = _L.parse_detail(_ldjson_script([car]))
        self.assertEqual(d["brand"], "Honda")
        self.assertEqual(d["model"], "Civic")
        self.assertEqual(d["year"], 1998)
        self.assertTrue(len(d["images"]) >= 1)
        self.assertTrue(d["url"].endswith("/45291610"))


class TestParseFacets(unittest.TestCase):
    def test_brands_parsed(self):
        doc = json.loads((FIX / "facets_brands.json").read_text())
        html = ("<html><script>var facets = " + json.dumps(doc)
                + ";</script></html>")
        brands = _L.parse_brands(html)
        self.assertEqual(len(brands), 4)
        self.assertEqual(brands[0]["name"], "Alfa Romeo")
        self.assertEqual(brands[0]["slug"], "alfa-romeo")
        self.assertEqual(brands[0]["count"], 285)

    def test_models_parsed(self):
        doc = json.loads((FIX / "facets_models.json").read_text())
        html = ("<html><script>var facets = " + json.dumps(doc)
                + ";</script></html>")
        models = _L.parse_models(html)
        self.assertEqual(len(models), 4)
        self.assertEqual(models[2]["name"], "3 Serisi")
        self.assertEqual(models[2]["slug"], "bmw-3-serisi")
        self.assertEqual(models[2]["count"], 3645)

    def test_no_facets_returns_empty(self):
        self.assertEqual(_L.parse_brands("<html></html>"), [])
        self.assertEqual(_L.parse_models("<html></html>"), [])


class TestPriceStats(unittest.TestCase):
    def test_stats(self):
        rows = [{"price_try": p} for p in (100, 200, 300, 400)]
        s = _L.price_stats(rows)
        self.assertEqual(s["count"], 4)
        self.assertEqual(s["min"], 100)
        self.assertEqual(s["max"], 400)
        self.assertEqual(s["median"], 250)
        self.assertEqual(s["average"], 250)
        self.assertEqual(s["currency"], "TRY")

    def test_empty(self):
        self.assertEqual(_L.price_stats([]), {"count": 0})

    def test_ignores_missing_prices(self):
        s = _L.price_stats([{"price_try": 100}, {"price_try": None}, {}])
        self.assertEqual(s["count"], 1)


class TestSearchUrlValidation(unittest.TestCase):
    def test_brand_slug(self):
        from arabam_mcp import http as _H
        self.assertEqual(_H.search_url("bmw", None, 1),
                         "https://www.arabam.com/ikinci-el/otomobil/bmw")

    def test_model_overrides_brand(self):
        from arabam_mcp import http as _H
        self.assertEqual(_H.search_url("bmw", "bmw-3-serisi", 2),
                         "https://www.arabam.com/ikinci-el/otomobil/bmw-3-serisi?page=2")

    def test_bad_slug_rejected(self):
        from arabam_mcp import http as _H
        with self.assertRaises(_H.ArabamError):
            _H.search_url("../../etc", None, 1)

    def test_bad_detail_url_rejected(self):
        from arabam_mcp import http as _H
        with self.assertRaises(_H.ArabamError):
            _H.fetch_detail("https://evil.example.com/ilan/1")


if __name__ == "__main__":
    unittest.main()
