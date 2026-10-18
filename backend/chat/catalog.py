"""کاتالوگ هاردکد نسخه اول.

⚠️ شناسه‌ها، نام‌ها و قیمت‌ها باید با frontend/src/data/products.js هماهنگ باشند.
`keyword` نام مدل لاتین است که برای پیدا کردن محصولات ذکر شده در پاسخ AI استفاده می‌شود.
"""

PRODUCTS = [
    {"id": 1, "name": "هدفون بی‌سیم نویزکنسلینگ Aura ANC", "keyword": "Aura ANC", "price": 1_850_000, "category": "audio"},
    {"id": 2, "name": "هدفون گیمینگ Vortex 7.1", "keyword": "Vortex 7.1", "price": 1_200_000, "category": "audio"},
    {"id": 3, "name": "هدفون بلوتوث اقتصادی Pulse Lite", "keyword": "Pulse Lite", "price": 690_000, "category": "audio"},
    {"id": 4, "name": "ساعت هوشمند Nova Fit 2", "keyword": "Nova Fit 2", "price": 3_900_000, "category": "wearable"},
    {"id": 5, "name": "اسپیکر بلوتوث ضدآب Boom Mini", "keyword": "Boom Mini", "price": 1_450_000, "category": "audio"},
    {"id": 6, "name": "کیبورد مکانیکال Keystone 75", "keyword": "Keystone 75", "price": 2_100_000, "category": "accessory"},
    {"id": 7, "name": "پاوربانک ۲۰۰۰۰ میلی‌آمپر FastCharge", "keyword": "FastCharge", "price": 650_000, "category": "accessory"},
    {"id": 8, "name": "ماوس بی‌سیم Glide Pro", "keyword": "Glide Pro", "price": 480_000, "category": "accessory"},
]

CATALOG_TEXT = "\n".join(f"- {p['name']}: {p['price']:,} تومان" for p in PRODUCTS)

MAX_SUGGESTED = 3


def find_product_ids(text):
    """شناسه محصولاتی که نام مدلشان در متن آمده را به ترتیب ظهور برمی‌گرداند."""
    lowered = (text or "").lower()
    hits = []
    for product in PRODUCTS:
        pos = lowered.find(product["keyword"].lower())
        if pos != -1:
            hits.append((pos, product["id"]))
    hits.sort()
    return [pid for _, pid in hits][:MAX_SUGGESTED]
