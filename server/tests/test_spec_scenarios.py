"""
Test suite covering all 28 client scenarios from specifications.md §5.

Categories:
  1. Commandes & Suivi (7 tests)
  2. Livraison & Expedition (8 tests)
  3. Paiement & Facturation (8 tests)
  4. Retours, Echanges & Remboursements (5 tests)
"""

import unittest


class SpecScenarioTests(unittest.TestCase):
    """Validate chatbot responses against every spec test case."""

    @classmethod
    def setUpClass(cls):
        from app import create_app
        from routes.chat_routes import chat_service

        cls.app = create_app()
        cls.client = cls.app.test_client()

        # Push app context for DB access
        cls.app_context = cls.app.app_context()
        cls.app_context.push()

        # Avoid external LLM/Pinecone calls — mark initialized
        chat_service.initialized = True

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    def _send_chat(self, message: str, session_id: str) -> dict:
        """Helper: send a message and return the parsed JSON response."""
        response = self.client.post(
            "/api/chat/message",
            json={"message": message, "session_id": session_id},
        )
        self.assertEqual(response.status_code, 200, f"HTTP error for: {message}")
        payload = response.get_json()
        self.assertTrue(payload.get("success"), f"API failure for: {message}")
        return payload

    # ─── Category 1: Commandes & Suivi ─────────────────────────────

    def test_order_tracking(self):
        """Spec: 'Où en est ma commande n°12345 ?'"""
        # Get a real order number from seeded data
        resp = self.client.get("/api/orders/")
        orders = resp.get_json().get("orders", [])
        if not orders:
            self.skipTest("No seeded orders")
        order_num = orders[0]["orderNumber"]

        payload = self._send_chat(
            f"Ou en est ma commande {order_num} ?",
            "test-spec-cat1-tracking"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            order_num.lower() in content or "statut" in content or "commande" in content,
            f"Response should reference the order: {content[:200]}"
        )

    def test_delivery_date_estimate(self):
        """Spec: 'Quand vais-je recevoir ma commande ?'"""
        payload = self._send_chat(
            "Quand vais-je recevoir ma commande ?",
            "test-spec-cat1-delivery"
        )
        content = (payload.get("response") or {}).get("content", "")
        self.assertTrue(len(content) > 10, "Response should not be empty")

    def test_modify_order(self):
        """Spec: 'Puis-je modifier ma commande après validation ?'"""
        payload = self._send_chat(
            "Puis-je modifier ma commande apres validation ?",
            "test-spec-cat1-modify"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["modif", "preparation", "possible", "30 min"]),
            f"Response should address modification policy: {content[:200]}"
        )

    def test_cancel_order(self):
        """Spec: 'Comment annuler ma commande ?'"""
        payload = self._send_chat(
            "Comment annuler ma commande ?",
            "test-spec-cat1-cancel"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["annul", "rembours", "expedi"]),
            f"Response should address cancellation: {content[:200]}"
        )

    def test_no_confirmation_email(self):
        """Spec: 'Je n'ai pas reçu de confirmation de commande'"""
        payload = self._send_chat(
            "Je n'ai pas recu de confirmation de commande",
            "test-spec-cat1-noconfirm"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(len(content) > 10, "Response should not be empty")

    def test_partial_delivery(self):
        """Spec: 'J'ai commandé 3 articles mais je n'en ai reçu que 2'"""
        payload = self._send_chat(
            "J'ai commande 3 articles mais je n'en ai recu que 2",
            "test-spec-cat1-partial"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["colis", "expedi", "article", "reclam"]),
            f"Response should address partial delivery: {content[:200]}"
        )

    def test_delivered_not_received(self):
        """Spec: 'Ma commande est marquée livrée mais je ne l'ai pas reçue'"""
        payload = self._send_chat(
            "Ma commande est marquee livree mais je ne l'ai pas recue",
            "test-spec-cat1-notreceived"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["enquete", "transporteur", "adresse", "rembours"]),
            f"Response should address delivery dispute: {content[:200]}"
        )

    # ─── Category 2: Livraison & Expedition ────────────────────────

    def test_delivery_times(self):
        """Spec: 'Quels sont les délais de livraison ?'"""
        payload = self._send_chat(
            "Quels sont les delais de livraison ?",
            "test-spec-cat2-times"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["standard", "express", "jour", "ouvr"]),
            f"Response should list delivery times: {content[:200]}"
        )

    def test_corsica_dom_tom(self):
        """Spec: 'Livrez-vous en Corse / DOM-TOM ?'"""
        payload = self._send_chat(
            "Livrez-vous en Corse ou DOM-TOM ?",
            "test-spec-cat2-corsica"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["corse", "dom", "tom", "supplement", "oui"]),
            f"Response should address Corsica/DOM-TOM: {content[:200]}"
        )

    def test_choose_delivery_day(self):
        """Spec: 'Puis-je choisir le jour de livraison ?'"""
        payload = self._send_chat(
            "Puis-je choisir le jour de livraison ?",
            "test-spec-cat2-chooseday"
        )
        content = (payload.get("response") or {}).get("content", "")
        self.assertTrue(len(content) > 10, "Response should not be empty")

    def test_shipping_costs(self):
        """Spec: 'Combien coûtent les frais de port ?'"""
        payload = self._send_chat(
            "Combien coutent les frais de port ?",
            "test-spec-cat2-costs"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["gratuit", "4,99", "frais", "port"]),
            f"Response should address shipping costs: {content[:200]}"
        )

    def test_relay_point(self):
        """Spec: 'Proposez-vous la livraison en point relais ?'"""
        payload = self._send_chat(
            "Proposez-vous la livraison en point relais ?",
            "test-spec-cat2-relay"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["relais", "oui", "mondial", "disponible"]),
            f"Response should address relay delivery: {content[:200]}"
        )

    def test_absent_delivery(self):
        """Spec: 'Je serai absent le jour de la livraison, que faire ?'"""
        payload = self._send_chat(
            "Je serai absent le jour de la livraison, que faire ?",
            "test-spec-cat2-absent"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["reprogramm", "relais", "depot", "absent"]),
            f"Response should offer alternatives: {content[:200]}"
        )

    def test_neighbor_delivery(self):
        """Spec: 'Mon colis a été livré chez un voisin'"""
        payload = self._send_chat(
            "Mon colis a ete livre chez un voisin, comment le recuperer ?",
            "test-spec-cat2-neighbor"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["voisin", "avis", "passage", "transporteur"]),
            f"Response should address neighbor delivery: {content[:200]}"
        )

    def test_late_delivery(self):
        """Spec: 'La livraison est en retard par rapport à la date promise'"""
        payload = self._send_chat(
            "La livraison est en retard par rapport a la date promise",
            "test-spec-cat2-late"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["retard", "desol", "transporteur", "compens"]),
            f"Response should address late delivery: {content[:200]}"
        )

    # ─── Category 3: Paiement & Facturation ────────────────────────

    def test_payment_methods(self):
        """Spec: 'Quels moyens de paiement acceptez-vous ?'"""
        payload = self._send_chat(
            "Quels moyens de paiement acceptez-vous ?",
            "test-spec-cat3-methods"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["carte", "paypal", "visa", "paiement"]),
            f"Response should list payment methods: {content[:200]}"
        )

    def test_payment_refused(self):
        """Spec: 'Mon paiement a été refusé, pourquoi ?'"""
        payload = self._send_chat(
            "Mon paiement a ete refuse, pourquoi ?",
            "test-spec-cat3-refused"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["plafond", "solde", "refuse", "3d secure"]),
            f"Response should explain payment refusal: {content[:200]}"
        )

    def test_installment_payment(self):
        """Spec: 'Puis-je payer en plusieurs fois ?'"""
        payload = self._send_chat(
            "Puis-je payer en plusieurs fois ?",
            "test-spec-cat3-installment"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["plusieurs fois", "3 fois", "4 fois", "alma", "fractionn"]),
            f"Response should address installments: {content[:200]}"
        )

    def test_find_invoice(self):
        """Spec: 'Où trouver ma facture ?'"""
        payload = self._send_chat(
            "Ou trouver ma facture ?",
            "test-spec-cat3-invoice"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["facture", "espace client", "commande", "email"]),
            f"Response should explain how to find invoice: {content[:200]}"
        )

    def test_wrong_amount(self):
        """Spec: 'Le montant prélevé ne correspond pas à ma commande'"""
        payload = self._send_chat(
            "Le montant preleve ne correspond pas a ma commande",
            "test-spec-cat3-wrongamount"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["montant", "frais", "promotion", "pre-autori"]),
            f"Response should explain amount discrepancy: {content[:200]}"
        )

    def test_double_charge(self):
        """Spec: 'J'ai été débité deux fois pour la même commande'"""
        payload = self._send_chat(
            "J'ai ete debite deux fois pour la meme commande",
            "test-spec-cat3-doublecharge"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["double", "rembours", "transaction", "pre-autori"]),
            f"Response should address double charge: {content[:200]}"
        )

    def test_promo_code(self):
        """Spec: 'Je veux utiliser un code promo mais il ne fonctionne pas'"""
        payload = self._send_chat(
            "Je veux utiliser un code promo mais il ne fonctionne pas",
            "test-spec-cat3-promo"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["code", "promo", "expir", "condition", "cumulab"]),
            f"Response should address promo issues: {content[:200]}"
        )

    def test_change_payment_method(self):
        """Spec: 'Puis-je changer mon moyen de paiement après validation ?'"""
        payload = self._send_chat(
            "Puis-je changer mon moyen de paiement apres validation ?",
            "test-spec-cat3-changepayment"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["securite", "annul", "nouvelle commande", "impossible"]),
            f"Response should explain payment change: {content[:200]}"
        )

    # ─── Category 4: Retours, Échanges & Remboursements ────────────

    def test_return_procedure(self):
        """Spec: 'Comment retourner un article ?'"""
        payload = self._send_chat(
            "Comment retourner un article ?",
            "test-spec-cat4-return"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["retour", "etiquette", "espace client", "colis"]),
            f"Response should explain return procedure: {content[:200]}"
        )

    def test_return_deadline(self):
        """Spec: 'Sous quel délai puis-je retourner un produit ?'"""
        payload = self._send_chat(
            "Sous quel delai puis-je retourner un produit ?",
            "test-spec-cat4-deadline"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["14 jour", "30 jour", "retractation", "delai"]),
            f"Response should mention return deadline: {content[:200]}"
        )

    def test_return_shipping_costs(self):
        """Spec: 'Qui paie les frais de retour ?'"""
        payload = self._send_chat(
            "Qui paie les frais de retour ?",
            "test-spec-cat4-returncosts"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["frais", "defectueux", "charge", "avis"]),
            f"Response should explain return shipping: {content[:200]}"
        )

    def test_refund_timeline(self):
        """Spec: 'Quand serai-je remboursé ?'"""
        payload = self._send_chat(
            "Quand serai-je rembourse ?",
            "test-spec-cat4-refund"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["rembours", "jour", "bancaire", "48h"]),
            f"Response should explain refund timeline: {content[:200]}"
        )

    def test_exchange_size(self):
        """Spec: 'Puis-je échanger un article contre une autre taille ?'"""
        payload = self._send_chat(
            "Puis-je echanger un article contre une autre taille ?",
            "test-spec-cat4-exchange"
        )
        content = (payload.get("response") or {}).get("content", "").lower()
        self.assertTrue(
            any(w in content for w in ["echange", "retour", "nouvelle commande", "taille"]),
            f"Response should explain exchange procedure: {content[:200]}"
        )


if __name__ == "__main__":
    unittest.main()
