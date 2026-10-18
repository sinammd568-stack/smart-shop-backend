from types import SimpleNamespace
from unittest.mock import patch

from channels.testing import WebsocketCommunicator
from django.test import SimpleTestCase, override_settings

from .catalog import PRODUCTS, find_product_ids
from .consumers import ChatConsumer
from .security import ConnectionLimiter, SlidingWindowLimiter, clean_message, client_ip


class HttpTests(SimpleTestCase):
    def test_health(self):
        res = self.client.get("/api/health/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "ok")

    def test_security_headers(self):
        res = self.client.get("/api/health/")
        self.assertEqual(res["X-Content-Type-Options"], "nosniff")
        self.assertEqual(res["X-Frame-Options"], "DENY")

    def test_products_list_and_filter(self):
        res = self.client.get("/api/products/")
        self.assertEqual(res.json()["count"], len(PRODUCTS))
        res = self.client.get("/api/products/?category=wearable")
        self.assertEqual(res.json()["count"], 1)
        self.assertNotIn("keyword", res.json()["results"][0])


class CatalogTests(SimpleTestCase):
    def test_find_product_ids_orders_by_position(self):
        text = "پیشنهاد من Boom Mini و بعد Aura ANC است"
        self.assertEqual(find_product_ids(text), [5, 1])

    def test_find_product_ids_empty(self):
        self.assertEqual(find_product_ids("سلام"), [])


class SecurityHelpersTests(SimpleTestCase):
    def test_clean_message_strips_unsafe_but_keeps_zwnj(self):
        self.assertEqual(clean_message("a\x00b\u202ec"), "abc")
        self.assertEqual(clean_message("می\u200cخواهم"), "می\u200cخواهم")
        self.assertEqual(clean_message("a\n\n\n\nb"), "a\n\nb")

    def test_sliding_window(self):
        limiter = SlidingWindowLimiter(2, 60)
        self.assertTrue(limiter.allow("ip", now=0))
        self.assertTrue(limiter.allow("ip", now=1))
        self.assertFalse(limiter.allow("ip", now=2))
        self.assertTrue(limiter.allow("ip", now=61))
        self.assertTrue(limiter.allow("other", now=2))

    def test_connection_limiter(self):
        limiter = ConnectionLimiter(2)
        self.assertTrue(limiter.acquire("ip"))
        self.assertTrue(limiter.acquire("ip"))
        self.assertFalse(limiter.acquire("ip"))
        limiter.release("ip")
        self.assertTrue(limiter.acquire("ip"))

    def test_client_ip_uses_trusted_hop_only(self):
        scope = {"headers": [(b"x-forwarded-for", b"6.6.6.6, 1.2.3.4")], "client": ("10.0.0.1", 1)}
        self.assertEqual(client_ip(scope, 1), "1.2.3.4")  # مقدار جعلی سمت چپ نادیده گرفته می‌شود
        self.assertEqual(client_ip(scope, 0), "10.0.0.1")


class FakeStream:
    def __init__(self, parts):
        self.parts = parts

    async def __aiter__(self):
        for part in self.parts:
            yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=part))])


class FakeGroq:
    def __init__(self, **kwargs):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    async def _create(self, **kwargs):
        return FakeStream(["پیشنهاد من ", "Boom Mini است."])


class ConsumerTests(SimpleTestCase):
    @override_settings(GROQ_API_KEY="test-key")
    async def test_streaming_reply(self):
        with patch("chat.consumers.AsyncGroq", FakeGroq):
            comm = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            connected, _ = await comm.connect()
            self.assertTrue(connected)

            await comm.send_json_to({"message": "اسپیکر می‌خوام"})
            first = await comm.receive_json_from()
            second = await comm.receive_json_from()
            done = await comm.receive_json_from()

            self.assertEqual(first["type"], "chunk")
            self.assertEqual(second["type"], "chunk")
            self.assertEqual(done["type"], "done")
            self.assertEqual(done["product_ids"], [5])
            await comm.disconnect()

    @override_settings(GROQ_API_KEY="")
    async def test_missing_api_key(self):
        comm = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
        await comm.connect()
        await comm.send_json_to({"message": "سلام"})
        res = await comm.receive_json_from()
        self.assertEqual(res["type"], "error")
        await comm.disconnect()

    @override_settings(GROQ_API_KEY="test-key")
    async def test_rejects_non_string_and_oversized(self):
        with patch("chat.consumers.AsyncGroq", FakeGroq):
            comm = WebsocketCommunicator(ChatConsumer.as_asgi(), "/ws/chat/")
            await comm.connect()

            await comm.send_json_to({"message": {"evil": True}})
            res = await comm.receive_json_from()
            self.assertEqual(res["type"], "error")

            await comm.send_json_to({"message": "x" * 600})
            res = await comm.receive_json_from()
            self.assertEqual(res["type"], "error")
            await comm.disconnect()
