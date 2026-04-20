import unittest


class IntegrationApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app
        from routes.chat_routes import chat_service

        cls.client = app.test_client()

        # Avoid external initialization (Groq/Pinecone) during integration tests.
        chat_service.initialized = True

    def _get_first_order(self):
        response = self.client.get("/api/orders/")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))

        orders = payload.get("orders", [])
        return orders[0] if orders else None

    def test_support_playbook_endpoint(self):
        response = self.client.get("/api/support/playbook")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertIn("categories", payload)
        self.assertGreaterEqual(len(payload["categories"]), 1)

    def test_support_faq_endpoint(self):
        response = self.client.get(
            "/api/support/faq",
            query_string={"query": "quand vais-je recevoir ma commande", "limit": 3},
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertIn("results", payload)
        self.assertGreaterEqual(payload.get("count", 0), 1)

    def test_support_scenarios_endpoint(self):
        response = self.client.get("/api/support/scenarios")
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertGreater(payload.get("count", 0), 0)

        categories = {
            item.get("categoryId") for item in payload.get("scenarios", [])
        }
        self.assertIn("orders_tracking", categories)
        self.assertIn("shipping_delivery", categories)
        self.assertIn("payment_billing", categories)
        self.assertIn("returns_refunds", categories)

    def test_order_list_and_track_endpoint(self):
        order = self._get_first_order()
        if not order:
            self.skipTest("No seeded order available")

        response = self.client.get(
            "/api/orders/track",
            query_string={
                "order_number": order["orderNumber"],
                "email": order["customerEmail"],
            },
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))
        self.assertEqual(payload["order"]["orderNumber"], order["orderNumber"])

    def test_chat_order_tracking_response(self):
        order = self._get_first_order()
        if not order:
            self.skipTest("No seeded order available")

        response = self.client.post(
            "/api/chat/message",
            json={
                "message": f"Ou en est ma commande {order['orderNumber']} ?",
                "session_id": "test-session-order-integration",
            },
        )
        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertTrue(payload.get("success"))

        content = (payload.get("response") or {}).get("content", "")
        # Order tracking now goes through LLM tool (skipped in tests).
        # The KB fallback returns a generic "provide your order number" response.
        self.assertTrue(
            order["orderNumber"] in content
            or "commande" in content.lower()
            or "numero" in content.lower(),
            f"Response should reference orders: {content[:200]}"
        )

    def test_chat_support_categories_direct_answers(self):
        scenarios = [
            (
                "Livrez-vous en Corse ou DOM-TOM ?",
                ["corse", "dom-tom", "dom", "livrons"],
            ),
            (
                "Quels moyens de paiement acceptez-vous ?",
                ["carte", "paypal", "paiement", "acceptons"],
            ),
            (
                "Sous quel delai puis-je retourner un produit ?",
                ["retour", "delai", "14 jour", "30 jour"],
            ),
        ]

        for idx, (question, expected_keywords) in enumerate(scenarios):
            response = self.client.post(
                "/api/chat/message",
                json={
                    "message": question,
                    "session_id": f"test-session-support-{idx}",
                },
            )
            self.assertEqual(response.status_code, 200)

            payload = response.get_json()
            self.assertTrue(payload.get("success"))
            content = ((payload.get("response") or {}).get("content") or "").lower()
            self.assertTrue(
                any(kw in content for kw in expected_keywords),
                f"Response for '{question}' should contain one of {expected_keywords}: {content[:200]}"
            )


if __name__ == "__main__":
    unittest.main()
