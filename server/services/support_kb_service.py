import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List


class SupportKBService:
    """Searchable knowledge base for customer-support playbook entries."""

    def __init__(self, kb_path: str | None = None):
        base_dir = Path(__file__).resolve().parent.parent
        self.kb_path = Path(kb_path) if kb_path else base_dir / "knowledge_base" / "support_playbook.json"
        self._data: Dict[str, Any] | None = None

    def _load(self) -> Dict[str, Any]:
        if self._data is None:
            with self.kb_path.open("r", encoding="utf-8") as f:
                self._data = json.load(f)
        return self._data

    def get_catalog(self) -> Dict[str, Any]:
        return self._load()

    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower()
        text = "".join(
            ch
            for ch in unicodedata.normalize("NFD", text)
            if unicodedata.category(ch) != "Mn"
        )
        return text

    def _expand_tokens(self, tokens: set[str]) -> set[str]:
        synonym_groups = [
            {"commande", "order", "orders"},
            {"livraison", "expedition", "shipment", "shipping"},
            {"retour", "retours", "remboursement", "refund", "returns"},
            {"paiement", "payment", "facturation", "billing", "facture", "invoice"},
            {"annuler", "annulation", "cancel", "cancellation"},
            {"suivi", "tracking", "track"},
        ]

        expanded = set(tokens)
        for group in synonym_groups:
            if expanded.intersection(group):
                expanded.update(group)
        return expanded

    def _tokenize(self, text: str) -> set[str]:
        normalized = self._normalize_text(text)
        return {
            token
            for token in re.findall(r"[a-z0-9']+", normalized)
            if len(token) >= 2
        }

    def search_entries(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        data = self._load()
        query_tokens = self._expand_tokens(self._tokenize(query))
        matches: List[Dict[str, Any]] = []

        for category in data.get("categories", []):
            for level in ("simple", "complex"):
                for item in category.get(level, []):
                    question_tokens = self._expand_tokens(self._tokenize(item.get("question", "")))
                    intent_tokens = self._expand_tokens(
                        self._tokenize(item.get("intention", "") or item.get("challenge", ""))
                    )
                    guidance_tokens = self._expand_tokens(
                        self._tokenize(item.get("recommended_answer", "") or item.get("expected", ""))
                    )
                    required_tokens = self._expand_tokens(
                        self._tokenize(" ".join(item.get("required_data", [])))
                    )

                    question_overlap = len(query_tokens.intersection(question_tokens))
                    intent_overlap = len(query_tokens.intersection(intent_tokens))
                    guidance_overlap = len(query_tokens.intersection(guidance_tokens))
                    required_overlap = len(query_tokens.intersection(required_tokens))

                    raw_score = (
                        (question_overlap * 3)
                        + (intent_overlap * 2)
                        + guidance_overlap
                        + required_overlap
                    )
                    score = min(raw_score, 10)

                    if raw_score > 0:
                        matches.append(
                            {
                                "category_id": category.get("id"),
                                "category_title": category.get("title"),
                                "level": level,
                                "score": score,
                                "raw_score": raw_score,
                                "question": item.get("question"),
                                "intention": item.get("intention") or item.get("challenge"),
                                "required_data": item.get("required_data", []),
                                "recommended_answer": item.get("recommended_answer"),
                                "expected": item.get("expected"),
                            }
                        )

        matches.sort(key=lambda item: item["raw_score"], reverse=True)
        return matches[:top_k]

    def format_hits_for_prompt(self, hits: List[Dict[str, Any]]) -> str:
        lines: List[str] = []
        for hit in hits:
            lines.append(
                "- "
                + f"[{hit['category_title']}] Q: {hit['question']} | "
                + f"Intention: {hit['intention']} | "
                + f"Data needed: {', '.join(hit.get('required_data', [])) or 'n/a'} | "
                + f"Guidance: {hit.get('recommended_answer') or hit.get('expected') or 'n/a'}"
            )
        return "\n".join(lines)

    def build_direct_answer(self, query: str) -> str | None:
        hits = self.search_entries(query, top_k=1)
        if not hits:
            return None

        top = hits[0]
        if top["score"] < 5:
            return None

        guidance = top.get("recommended_answer") or top.get("expected")
        needed = top.get("required_data", [])

        response = f"{guidance}"
        if needed:
            response += "\n\nPour traiter votre demande maintenant, il me faut: " + ", ".join(needed) + "."

        return response
