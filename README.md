# arabam-mcp 🇹🇷

> ⚠️ **Status: DEGRADED (2026-11-10)** — arabam.com currently blocks automated access: the connection is reset on every fingerprint profile (chrome120 / chrome131 / safari17_0) from this environment. All tools return a clear "blocked" error until the site allows access again. Check `arabam_health` for the live status.


mcp-name: io.github.mohammad-abbasi-sh/arabam-mcp

Unofficial **read-only** MCP server for **arabam.com**, Türkiye's used-car marketplace (~176k listings) — live search, full listing details with the 19-field spec table, brand/model browser, and market price stats.

> Built by Mohammad Abbasi as part of the "Turkey MCP factory" (Sepehr-style pipeline). Not affiliated with arabam.com.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "arabam": {
      "command": "uvx",
      "args": ["arabam-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m arabam_mcp.server` (needs `mcp<2`, `curl-cffi`).

## Tools

| Tool | Description |
|------|-------------|
| `arabam_search` | Search listings — `brand` slug ("bmw"), `model` slug ("bmw-3-serisi"), `page` 1..50 |
| `arabam_listing_detail` | Full detail of one listing (URL from search): price + 19-field spec table |
| `arabam_list_brands` | All ~77 brands with listing counts and URL slugs |
| `arabam_list_models` | Models of a brand (e.g. "bmw") with counts and slugs |
| `arabam_price_stats` | Market stats: min/max/median/average TRY price over N pages |

Example output (`arabam_search` / bmw 3-serisi):

```json
{"brand": "", "model": "bmw-3-serisi", "page": 1, "count": 20,
 "listings": [{"id": "45288789", "title": "214 BİN KMDE SORUNSUZ A4 TDI",
  "brand": "Audi", "year": 2019, "km": 214000, "price_try": 789900,
  "url": "https://www.arabam.com/ilan/.../45288789"}]}
```

Example output (`arabam_listing_detail`):

```json
{"title": "Galeriden Honda Civic 1.4 S 1998 Model …", "price": 425000,
 "price_currency": "TRY", "price_text": "425.000 TL",
 "specs": {"Marka": "Honda", "Seri": "Civic", "Model": "1.4 S",
  "Yıl": "1998", "Kilometre": "330.000 KM", "Vites tipi": "Düz",
  "Yakıt tipi": "LPG & benzin", "Kimden": "Galeriden", …}}
```

Notes:
- Data comes from arabam.com's public server-rendered pages (schema.org Vehicle/Car JSON-LD + spec table) — no key, no login, read-only.
- Spec-table labels are Turkish (Marka, Seri, Model, Yıl, Kilometre, Vites tipi, Yakıt tipi, Kasa tipi, Renk, Motor hacmi, Motor gücü, Çekiş, Kimden…).
- Requests are spaced ~0.8s apart to stay polite.
- Environments behind an MITM proxy: set `SSL_CERT_FILE` to a CA bundle that trusts the proxy.

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_listings.py` — offline, parses real captured fixtures
- `tests/test_live.py` — 5 cautious live requests against arabam.com (needs `SSL_CERT_FILE` behind the lab proxy)

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
