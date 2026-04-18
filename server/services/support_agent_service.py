import re
from typing import Optional, Dict, Any

from flask import current_app
from .order_service import OrderService
from .support_kb_service import SupportKBService


class SupportAgentService:
    """Deterministic support-agent layer used before LLM fallback.
    
    Enforces non-hallucination policy:
    - Only returns KB-backed answers when confidence >= KB_CONFIDENCE_THRESHOLD
    - Order tracking always returned (highest confidence)
    - Falls back to LLM for queries below threshold
    """

    ORDER_NUMBER_PATTERN = re.compile(r"\bORD-\d{8}\b", re.IGNORECASE)
    OUT_OF_DOMAIN_KEYWORDS = {
        "politique",
        "election",
        "president",
        "football",
        "match",
        "crypto",
        "bitcoin",
        "meteo",
        "horoscope",
        "recette",
        "sante",
    }

    def __init__(self):
        self.kb_service = SupportKBService()

    def extract_order_number(self, text: str) -> Optional[str]:
        match = self.ORDER_NUMBER_PATTERN.search((text or "").upper())
        return match.group(0) if match else None

    def is_out_of_domain(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(keyword in lowered for keyword in self.OUT_OF_DOMAIN_KEYWORDS)

    def build_order_tracking_answer(self, order_number: str) -> Optional[str]:
        order = OrderService.get_order_by_number(order_number)
        if not order:
            return None

        payload = order.to_dict(include_items=True)
        lines = [
            f"Commande {payload['orderNumber']} - statut: {payload['status']}",
            f"Transporteur: {payload.get('carrier') or 'non assigne'}",
            f"Suivi colis: {payload.get('trackingNumber') or 'non disponible'}",
            f"Livraison estimee: {payload.get('estimatedDeliveryAt') or 'non disponible'}",
            "Articles:",
        ]

        for item in payload.get("items", []):
            lines.append(
                f"- {item['productName']} x{item['quantity']} ({item['lineTotal']}$)"
            )

        return "\n".join(lines)

    def get_direct_support_answer_with_metadata(self, text: str) -> Dict[str, Any]:
        """Get direct support answer and return metadata about match confidence.
        
        Non-hallucination policy:
        - Returns KB answer only if score >= KB_CONFIDENCE_THRESHOLD
        - Score below threshold → return None for LLM fallback
        - Tracks confidence as normalized 0-1 range
        """
        if self.is_out_of_domain(text):
            return {
                "answer": "Je suis specialise dans le support e-commerce (commandes, livraison, paiement, retours). Posez-moi une question sur votre achat et je vous aiderai avec plaisir.",
                "matched": True,
                "confidence": 1.0,
                "category": "Hors domaine",
                "intent": "out_of_domain_guardrail",
                "required_data": [],
                "meets_threshold": True,
                "source": "guardrail",
                "matched_question": None,
            }

        hits = self.kb_service.search_entries(text, top_k=1)
        
        # Get config with fallback to defaults
        confidence_threshold = getattr(
            current_app.config, "KB_CONFIDENCE_THRESHOLD", 2
        )
        
        if not hits:
            return {
                "answer": None,
                "matched": False,
                "confidence": 0,
                "category": None,
                "intent": None,
                "required_data": [],
                "meets_threshold": False,
                "source": "llm",
                "matched_question": None,
            }
        
        top = hits[0]
        meets_threshold = top["score"] >= confidence_threshold
        
        if not meets_threshold:
            # Score below threshold - return None for LLM fallback
            # But include metadata for transparency
            return {
                "answer": None,
                "matched": False,
                "confidence": top["score"] / 10.0,  # Normalized to 0-1
                "category": top["category_title"],
                "intent": top.get("intention"),
                "required_data": top.get("required_data", []),
                "meets_threshold": False,
                "source": "llm",
                "matched_question": top.get("question"),
            }
        
        # Threshold met - return KB answer
        guidance = top.get("recommended_answer") or top.get("expected")
        needed = top.get("required_data", [])
        
        answer = f"{guidance}"
        if needed:
            answer += "\n\nPour traiter votre demande maintenant, il me faut: " + ", ".join(needed) + "."
        
        return {
            "answer": answer,
            "matched": True,
            "confidence": min(top["score"] / 10.0, 1.0),  # Normalize to 0-1 range
            "category": top["category_title"],
            "intent": top.get("intention"),
            "required_data": needed,
            "meets_threshold": True,
            "source": "direct_support",
            "matched_question": top.get("question"),
        }

    def get_direct_support_answer(self, text: str) -> Optional[str]:
        """Legacy method for backward compatibility."""
        result = self.get_direct_support_answer_with_metadata(text)
        return result["answer"]

    def get_support_context(self, text: str, top_k: int = 3) -> str:
        """Get support context for LLM injection when KB answer insufficient."""
        hits = self.kb_service.search_entries(text, top_k=top_k)
        return self.kb_service.format_hits_for_prompt(hits)
