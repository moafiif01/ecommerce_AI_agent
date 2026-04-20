"""
Script to index all support KB documents (FAQ + CGV) into Pinecone.

Run inside the Flask app context:
    flask shell < scripts/index_support_kb.py
Or:
    docker-compose exec backend python scripts/index_support_kb.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from services.rag_service import RAGService
from services.vector_service import VectorService


def main():
    app = create_app()
    with app.app_context():
        print("Initializing vector service...")
        vector_service = VectorService()
        vector_service.initialize()

        print("Building and indexing support KB...")
        rag_service = RAGService()
        rag_service.initialize(vector_service)

        count = rag_service.index_all_documents()
        print(f"Done! Indexed {count} chunks into Pinecone namespace 'support-kb'.")


if __name__ == "__main__":
    main()
