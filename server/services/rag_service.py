"""
RAG Service — Retrieval-Augmented Generation over company documents.

Handles:
1. Loading & chunking FAQ playbook + CGV documents
2. Embedding chunks using SentenceTransformer
3. Indexing chunks into Pinecone (namespace: "support-kb")
4. Retrieval: embedding user query → vector search → return top-K context chunks
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app

logger = logging.getLogger(__name__)

SUPPORT_KB_NAMESPACE = "support-kb"
CHUNK_SIZE = 300
CHUNK_OVERLAP = 50


class RAGService:
    """Retrieval-Augmented Generation over FAQ + CGV documents."""

    def __init__(self, vector_service=None):
        self.vector_service = vector_service
        self.indexed = False
        self._playbook_data = None
        self._cgv_chunks = None

    def initialize(self, vector_service):
        """Initialize with a shared VectorService instance."""
        self.vector_service = vector_service
        logger.info("RAG service initialized")

    # ─── Document Loading ──────────────────────────────────────────

    def _load_playbook(self) -> Dict[str, Any]:
        """Load FAQ playbook entries."""
        if self._playbook_data is not None:
            return self._playbook_data

        base_dir = Path(__file__).resolve().parent.parent
        playbook_path = base_dir / "knowledge_base" / "support_playbook.json"

        with playbook_path.open("r", encoding="utf-8") as f:
            self._playbook_data = json.load(f)
        return self._playbook_data

    def _load_cgv(self) -> str:
        """Load CGV markdown document."""
        base_dir = Path(__file__).resolve().parent.parent
        cgv_path = base_dir / "knowledge_base" / "cgv.md"

        if not cgv_path.exists():
            logger.warning("CGV file not found at %s", cgv_path)
            return ""

        with cgv_path.open("r", encoding="utf-8") as f:
            return f.read()

    # ─── Chunking ──────────────────────────────────────────────────

    def _chunk_text(self, text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
        """Split text into overlapping word-based chunks."""
        words = text.split()
        chunks = []
        start = 0
        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk.strip())
            start += chunk_size - overlap
        return chunks

    def _build_playbook_chunks(self) -> List[Dict[str, str]]:
        """Convert playbook entries into indexable chunks with metadata."""
        data = self._load_playbook()
        chunks = []

        for category in data.get("categories", []):
            cat_title = category.get("title", "")
            cat_id = category.get("id", "")

            for level in ("simple", "complex"):
                for item in category.get(level, []):
                    question = item.get("question", "")
                    answer = item.get("recommended_answer") or item.get("expected", "")
                    intention = item.get("intention") or item.get("challenge", "")

                    text = f"Question: {question}\nIntention: {intention}\nReponse: {answer}"
                    chunk_id = f"faq-{cat_id}-{len(chunks)}"

                    chunks.append({
                        "id": chunk_id,
                        "text": text,
                        "metadata": {
                            "source": "faq",
                            "category": cat_title,
                            "category_id": cat_id,
                            "level": level,
                            "question": question,
                        }
                    })

        return chunks

    def _build_cgv_chunks(self) -> List[Dict[str, str]]:
        """Split CGV into overlapping chunks with section metadata."""
        raw_text = self._load_cgv()
        if not raw_text:
            return []

        # Split by article headings to preserve section context
        sections = re.split(r"(?=^## Article \d+)", raw_text, flags=re.MULTILINE)
        chunks = []

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # Extract section title from first line
            first_line = section.split("\n")[0].strip("# ").strip()

            text_chunks = self._chunk_text(section)
            for i, chunk in enumerate(text_chunks):
                chunk_id = f"cgv-{len(chunks)}"
                chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "source": "cgv",
                        "section": first_line,
                    }
                })

        return chunks

    # ─── Indexing ──────────────────────────────────────────────────

    def index_all_documents(self):
        """Embed and upsert all FAQ + CGV chunks into Pinecone."""
        if not self.vector_service or not self.vector_service.initialized:
            logger.error("Cannot index: VectorService not initialized")
            return 0

        faq_chunks = self._build_playbook_chunks()
        cgv_chunks = self._build_cgv_chunks()
        all_chunks = faq_chunks + cgv_chunks

        logger.info("Indexing %d FAQ chunks + %d CGV chunks = %d total",
                     len(faq_chunks), len(cgv_chunks), len(all_chunks))

        vectors = []
        for chunk in all_chunks:
            try:
                embedding = self.vector_service.generate_embedding(chunk["text"])
                vectors.append({
                    "id": chunk["id"],
                    "values": embedding,
                    "metadata": {
                        **chunk["metadata"],
                        "text": chunk["text"][:1000],  # Store truncated text for retrieval
                    }
                })
            except Exception as e:
                logger.error("Failed to embed chunk %s: %s", chunk["id"], str(e))

        # Batch upsert to Pinecone in the support-kb namespace
        if vectors:
            batch_size = 50
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.vector_service.index.upsert(
                    vectors=batch,
                    namespace=SUPPORT_KB_NAMESPACE
                )

        self.indexed = True
        logger.info("Successfully indexed %d support KB chunks", len(vectors))
        return len(vectors)

    # ─── Retrieval ─────────────────────────────────────────────────

    def retrieve_context(self, query: str, top_k: int = 5, min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Retrieve relevant FAQ/CGV chunks for a user query."""
        if not self.vector_service or not self.vector_service.initialized:
            logger.warning("RAG retrieval skipped: VectorService not initialized")
            return []

        try:
            query_embedding = self.vector_service.generate_embedding(query)

            results = self.vector_service.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=SUPPORT_KB_NAMESPACE,
            )

            chunks = []
            for match in results.get("matches", []):
                if match["score"] >= min_score:
                    chunks.append({
                        "text": match.get("metadata", {}).get("text", ""),
                        "source": match.get("metadata", {}).get("source", "unknown"),
                        "category": match.get("metadata", {}).get("category", ""),
                        "section": match.get("metadata", {}).get("section", ""),
                        "question": match.get("metadata", {}).get("question", ""),
                        "score": match["score"],
                    })

            logger.info("RAG retrieved %d chunks for query: %.80s", len(chunks), query)
            return chunks

        except Exception as e:
            logger.error("RAG retrieval error: %s", str(e))
            return []

    def format_context_for_prompt(self, chunks: List[Dict[str, Any]]) -> str:
        """Format retrieved chunks into a string suitable for LLM prompt injection."""
        if not chunks:
            return ""

        lines = ["[CONTEXTE DOCUMENTAIRE RECUPERE — base de connaissances interne]"]
        for i, chunk in enumerate(chunks, 1):
            source_label = "FAQ" if chunk["source"] == "faq" else "CGV"
            header = f"[{source_label}]"
            if chunk.get("category"):
                header += f" Categorie: {chunk['category']}"
            if chunk.get("section"):
                header += f" Section: {chunk['section']}"

            lines.append(f"\n--- Document {i} (score: {chunk['score']:.2f}) {header} ---")
            lines.append(chunk["text"])

        lines.append("\n[FIN DU CONTEXTE DOCUMENTAIRE]")
        return "\n".join(lines)
