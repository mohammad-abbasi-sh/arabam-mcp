# arabam-mcp 🇹🇷

سرور MCP غیررسمی و **فقط‌خواندنی** برای **arabam.com**، بازار خودروهای دست‌دوم ترکیه (حدود ۱۷۶ هزار آگهی) — جست‌وجوی زنده، جزئیات کامل هر آگهی با جدول ۱۹ فیلدی مشخصات، مرور برند/مدل و آمار قیمت بازار.

> ساختهٔ محمد عباسی در قالب «کارخانهٔ Turkey MCP» (خط تولید به سبک سپهر). وابستگی به arabam.com ندارد.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی کلاینت MCP خود (stdio) اضافه کنید:

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

یا به‌صورت محلی اجرا کنید: `python -m arabam_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `arabam_search` | جست‌وجوی آگهی‌ها — `brand` مثل «bmw»، `model` مثل «bmw-3-serisi»، `page` از ۱ تا ۵۰ |
| `arabam_listing_detail` | جزئیات کامل یک آگهی (آدرس از خروجی جست‌وجو): قیمت + جدول ۱۹ فیلدی مشخصات |
| `arabam_list_brands` | همهٔ ~۷۷ برند با تعداد آگهی و نام کوتاه آدرس |
| `arabam_list_models` | مدل‌های یک برند (مثلاً «bmw») با تعداد و نام کوتاه |
| `arabam_price_stats` | آمار بازار: کمینه/بیشینه/میانه/میانگین قیمت (لیر) روی N صفحه |

خروجی نمونه (`arabam_search` / ب‌ام‌و سری ۳):

```json
{"model": "bmw-3-serisi", "page": 1, "count": 20,
 "listings": [{"id": "45288789", "title": "214 BİN KMDE SORUNSUZ A4 TDI",
  "brand": "Audi", "year": 2019, "km": 214000, "price_try": 789900,
  "url": "https://www.arabam.com/ilan/.../45288789"}]}
```

نکته‌ها:
- داده‌ها از صفحات عمومی سمت‌سرور arabam.com می‌آیند (JSON-LD از نوع Vehicle/Car در schema.org + جدول مشخصات) — بدون کلید، بدون ورود، فقط خواندنی.
- برچسب‌های جدول مشخصات ترکی‌اند (Marka، Seri، Model، Yıl، Kilometre، Vites tipi، Yakıt tipi، Kasa tipi، Renk، Motor hacmi، Motor gücü، Çekiş، Kimden…).
- بین درخواست‌ها حدود ۰٫۸ ثانیه فاصله گذاشته می‌شود تا به سایت فشار نیاید.
- پشت پروکسی MITM: متغیر `SSL_CERT_FILE` را به بستهٔ CA مورد اعتماد پروکسی بدهید.

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" curl-cffi pytest
.venv/bin/python -m pytest tests/ -q
```

- `tests/test_listings.py` — آفلاین، با نمونه‌های واقعی ذخیره‌شده
- `tests/test_live.py` — ۵ درخواست محتاطانهٔ زنده به arabam.com

## مجوز

MIT
