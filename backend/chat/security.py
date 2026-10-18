"""ابزارهای امنیتی WebSocket (بدون وابستگی به Django تا ساده تست شوند)."""
import re
import time
from collections import defaultdict, deque

# کاراکترهای کنترلی (به جز \t و \n) + کاراکترهای نامرئی/جهت‌دهنده‌ی قابل سوءاستفاده.
# توجه: نیم‌فاصله (U+200C) عمداً حفظ می‌شود چون در فارسی لازم است.
_UNSAFE_CHARS = re.compile(
    "[\x00-\x08\x0b-\x1f\x7f\u200b\u200e\u200f\u202a-\u202e\u2066-\u2069\ufeff]"
)
_MANY_NEWLINES = re.compile(r"\n{3,}")


def clean_message(text):
    text = _UNSAFE_CHARS.sub("", text)
    text = _MANY_NEWLINES.sub("\n\n", text)
    return text.strip()


def client_ip(scope, trusted_hops=0):
    """آی‌پی کاربر. پشت پراکسی‌های مورد اعتماد، از X-Forwarded-For (از انتها) استفاده می‌شود.

    مقادیر سمت چپِ هدر قابل جعل‌اند؛ فقط ورودیِ اضافه‌شده توسط پراکسی خودمان معتبر است.
    """
    if trusted_hops > 0:
        headers = dict(scope.get("headers", []))
        raw = headers.get(b"x-forwarded-for", b"").decode("latin-1")
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        if len(parts) >= trusted_hops:
            return parts[-trusted_hops][:64]
    client = scope.get("client")
    return str(client[0])[:64] if client else "unknown"


class SlidingWindowLimiter:
    """حداکثر `limit` رویداد در هر `window` ثانیه برای هر کلید."""

    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self._events = defaultdict(deque)
        self._calls = 0

    def allow(self, key, now=None):
        now = time.monotonic() if now is None else now
        self._calls += 1
        if self._calls % 500 == 0:
            self._cleanup(now)

        events = self._events[key]
        while events and now - events[0] >= self.window:
            events.popleft()
        if len(events) >= self.limit:
            return False
        events.append(now)
        return True

    def _cleanup(self, now):
        stale = [k for k, ev in self._events.items() if not ev or now - ev[-1] >= self.window]
        for key in stale:
            del self._events[key]


class ConnectionLimiter:
    """حداکثر تعداد اتصال همزمان برای هر کلید."""

    def __init__(self, limit):
        self.limit = limit
        self._active = defaultdict(int)

    def acquire(self, key):
        if self._active[key] >= self.limit:
            return False
        self._active[key] += 1
        return True

    def release(self, key):
        if self._active.get(key, 0) <= 1:
            self._active.pop(key, None)
        else:
            self._active[key] -= 1
