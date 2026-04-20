import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///ecommerce.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = (
        os.environ.get("JWT_SECRET_KEY") or "jwt-secret-key-change-in-production"
    )
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        seconds=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 3600))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

    PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.environ.get("PINECONE_INDEX_NAME", "ecommerce-products")

    FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:5173")

    EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION = 384

    # Non-Hallucination Policy Configuration
    # Minimum confidence score required to return KB-backed answer (0-10, token overlap)
    KB_CONFIDENCE_THRESHOLD = int(os.environ.get("KB_CONFIDENCE_THRESHOLD", "5"))
    # When False, always use LLM for non-KB support queries (safer)
    # When True, allow LLM with support context injected (more flexible)
    ALLOW_LLM_FOR_SUPPORT_QUERIES = os.environ.get("ALLOW_LLM_FOR_SUPPORT_QUERIES", "true").lower() == "true"

    # RAG Configuration
    SUPPORT_KB_NAMESPACE = os.environ.get("SUPPORT_KB_NAMESPACE", "support-kb")
    RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "4"))
    RAG_SIMILARITY_THRESHOLD = float(os.environ.get("RAG_SIMILARITY_THRESHOLD", "0.3"))


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
