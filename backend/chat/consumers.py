import json
import logging
import time
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async # 👈 برای کوئری زدن به دیتابیس در حالت Async
from django.conf import settings
from groq import AsyncGroq

from .security import ConnectionLimiter, SlidingWindowLimiter, clean_message, client_ip
from store.models import Product # 👈 ایمپورت مدل محصول برای خواندن از دیتابیس

logger = logging.getLogger(__name__)

MAX_HISTORY = 12
MAX_MESSAGE_LEN = 500
MAX_FRAME_CHARS = 4096
MAX_MESSAGES_PER_CONNECTION = 200
MIN_INTERVAL = 1.0

connection_limiter = ConnectionLimiter(settings.CHAT_MAX_CONNECTIONS_PER_IP)
message_limiter = SlidingWindowLimiter(settings.CHAT_MAX_MESSAGES_PER_MINUTE, 60)

# ---------------------------------------------------------
# توابع کمکی برای خواندن داینامیک از دیتابیس
# ---------------------------------------------------------

@database_sync_to_async
def get_dynamic_catalog():
    """لیست محصولات رو از دیتابیس می‌خونه و به متن تبدیل می‌کنه"""
    products = Product.objects.all()
    if not products:
        return "در حال حاضر هیچ محصولی در فروشگاه موجود نیست."
    
    text = ""
    for p in products:
        text += f"- نام: {p.name} | قیمت: {p.price} تومان | دسته‌بندی: {p.category}\n  توضیحات: {p.description}\n\n"
    return text

@database_sync_to_async
def find_product_ids_dynamic(reply_text):
    """بر اساس جواب هوش مصنوعی، محصولاتی که اسمشون توی متن اومده رو پیدا می‌کنه"""
    products = Product.objects.all()
    found_ids = []
    for p in products:
        # اگه اسم محصول توی جواب ربات بود، آیدیش رو اضافه کن
        if p.name in reply_text:
            found_ids.append(p.id)
    return found_ids


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.history = []
        self.closed = False
        self.registered = False
        self.sent_count = 0
        self.last_message_at = None
        self.ip = client_ip(self.scope, settings.TRUSTED_PROXY_COUNT)
        self.client = (
            AsyncGroq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        )
        await self.accept()

        if not connection_limiter.acquire(self.ip):
            await self._send("error", "تعداد اتصال‌های همزمان شما بیش از حد مجاز است.")
            await self.close(code=1008)
            return
        self.registered = True

    async def disconnect(self, close_code):
        self.closed = True
        self.history = []
        if self.registered:
            connection_limiter.release(self.ip)
            self.registered = False

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        if len(text_data) > MAX_FRAME_CHARS:
            await self._send("error", "پیام ارسالی بیش از حد بزرگ است.")
            await self.close(code=1009)
            return

        try:
            data = json.loads(text_data)
            if not isinstance(data, dict):
                raise ValueError("payload must be an object")
            raw_message = data.get("message", "")
            if not isinstance(raw_message, str):
                raise ValueError("message must be a string")
            
            is_admin_mode = data.get("admin_mode", False)
            
        except ValueError:
            await self._send("error", "فرمت پیام نامعتبر است.")
            return

        message = clean_message(raw_message)
        if not message:
            return
        if len(message) > MAX_MESSAGE_LEN:
            await self._send("error", f"پیام نباید بیشتر از {MAX_MESSAGE_LEN} کاراکتر باشد.")
            return
        if self.client is None:
            await self._send("error", "سرویس هوش مصنوعی هنوز تنظیم نشده است (GROQ_API_KEY).")
            return

        if self.sent_count >= MAX_MESSAGES_PER_CONNECTION:
            await self._send("error", "سقف پیام‌های این گفتگو پر شد. صفحه را تازه‌سازی کنید.")
            await self.close(code=1008)
            return

        now = time.monotonic()
        if self.last_message_at is not None and now - self.last_message_at < MIN_INTERVAL:
            await self._send("error", "لطفاً کمی آهسته‌تر پیام بدهید.")
            return
        if not message_limiter.allow(self.ip):
            await self._send("error", "تعداد پیام‌های شما زیاد است. کمی بعد دوباره تلاش کنید.")
            return
        self.last_message_at = now
        self.sent_count += 1

        self.history.append({"role": "user", "content": message})
        
        # 👈 ساخت پرامپت بر اساس نقش و محصولات داینامیک دیتابیس
        if is_admin_mode:
            current_prompt = """تو یک مشاور کسب و کار و دستیار مدیر فروشگاه اینترنتی هستی.
وظیفه‌ات کمک به مدیر (ادمین) برای مدیریت بهتر فروشگاه، تحلیل آمار فروش، و ارائه استراتژی‌های فروش است.
همیشه به فارسی، حرفه‌ای، تحلیلی و کوتاه پاسخ بده."""
        else:
            catalog_text = await get_dynamic_catalog()
            current_prompt = f"""تو یک دستیار فروشگاه هستی.
وظیفه‌ات کمک به مشتری برای انتخاب محصول مناسب است.

قوانین:
- همیشه به فارسی، مودبانه و کوتاه پاسخ بده.
- فقط از محصولات فهرست زیر پیشنهاد بده.
- هر محصول را دقیقاً با نام کامل بنویس.
- قیمت‌ها را به تومان بنویس.

فهرست محصولات موجود در فروشگاه:
{catalog_text}
"""

        messages = [{"role": "system", "content": current_prompt}] + self.history[-MAX_HISTORY:]

        parts = []
        try:
            stream = await self.client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=messages,
                temperature=0.6,
                max_tokens=600,
                stream=True,
            )
            async for chunk in stream:
                if self.closed:
                    return
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta.content
                if delta:
                    parts.append(delta)
                    await self._send("chunk", delta)
        except Exception as e:
            logger.exception("Groq request failed")
            self.history.pop()
            await self._send("error", "مشکلی در ارتباط با دستیار پیش آمد. لطفاً دوباره تلاش کنید.")
            return

        reply = "".join(parts).strip()
        if not reply:
            self.history.pop()
            await self._send("error", "متأسفم، نتوانستم پاسخی تولید کنم. لطفاً دوباره تلاش کنید.")
            return

        self.history.append({"role": "assistant", "content": reply})
        self.history = self.history[-MAX_HISTORY:]
        
        # 👈 پیدا کردن آیدی محصولات به صورت داینامیک
        product_ids = await find_product_ids_dynamic(reply) if not is_admin_mode else []
        
        await self._send("done", reply, product_ids=product_ids)

    async def _send(self, msg_type, message, **extra):
        payload = {"type": msg_type, "message": message, **extra}
        await self.send(text_data=json.dumps(payload, ensure_ascii=False))
