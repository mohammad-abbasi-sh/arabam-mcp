# arabam-mcp 🇹🇷

Türkiye'nin ikinci el otomobil pazaryeri **arabam.com** için resmi olmayan, **salt okunur** MCP sunucusu — canlı ilan arama, 19 alanlık özellik tablosuyla tam ilan detayı, marka/model tarama ve piyasa fiyat istatistikleri.

> Mohammad Abbasi tarafından "Turkey MCP factory" (Sepehr tarzı hat) kapsamında geliştirildi. arabam.com ile bağlantısı yoktur.

## Yapay zekâ ajanları için

MCP istemci yapılandırmanıza (stdio) ekleyin:

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

Veya yerelde çalıştırın: `python -m arabam_mcp.server` (`mcp<2`, `httpx` gerekir).

## Araçlar

| Araç | Açıklama |
|------|----------|
| `arabam_search` | İlan arama — `brand` ("bmw"), `model` ("bmw-3-serisi"), `page` 1..50 |
| `arabam_listing_detail` | Tek ilanın tam detayı (arama sonucundaki URL): fiyat + 19 alanlık özellik tablosu |
| `arabam_list_brands` | ~77 markanın tamamı, ilan sayıları ve URL kısaltmalarıyla |
| `arabam_list_models` | Bir markanın modelleri (örn. "bmw"), sayılar ve kısaltmalarla |
| `arabam_price_stats` | Piyasa istatistiği: N sayfadaki ilanların en düşük/en yüksek/ortanca/ortalama fiyatı (TL) |

Örnek çıktı (`arabam_search` / bmw 3-serisi):

```json
{"model": "bmw-3-serisi", "page": 1, "count": 20,
 "listings": [{"id": "45288789", "title": "214 BİN KMDE SORUNSUZ A4 TDI",
  "brand": "Audi", "year": 2019, "km": 214000, "price_try": 789900,
  "url": "https://www.arabam.com/ilan/.../45288789"}]}
```

Notlar:
- Veriler arabam.com'un herkese açık sunucu taraflı sayfalarından gelir (schema.org Vehicle/Car JSON-LD + özellik tablosu) — anahtar yok, giriş yok, salt okunur.
- Özellik tablosu etiketleri Türkçedir (Marka, Seri, Model, Yıl, Kilometre, Vites tipi, Yakıt tipi, Kasa tipi, Renk, Motor hacmi, Motor gücü, Çekiş, Kimden…).
- İstekler arasında ~0,8 sn beklenir (nazik kullanım).
- MITM proxy arkasındaki ortamlar: `SSL_CERT_FILE` ile proxy'ye güvenen bir CA paketi gösterin.

## Geliştirme

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_listings.py` — çevrimdışı, gerçek yakalanmış örneklerle
- `tests/test_live.py` — arabam.com'a karşı 5 temkinli canlı istek

## Lisans

MIT
