# Ecommerce Chatbot - Project Overview

## 📋 Project Description

A full-stack ecommerce chatbot application that combines natural language processing with intelligent cart management and fully autonomous tool calling. Users can browse products, ask policy questions (FAQ/CGV), track orders, and add items to cart through conversational AI. The system adopts a strict **RAG (Retrieval-Augmented Generation)** architecture coupled with **LangChain Tool Calling** using an LLM (Groq / Llama 3) for intelligent, grounded responses that prevent hallucinations.

**Status:** ✅ Production Ready - Core features functional and spec-validated

---

## 🏗️ Architecture Overview

```text
┌─────────────────────────────────────────┐
│    Frontend (Next.js 15.1.11)           │
│  - Chat Interface (page.tsx)            │
│  - Product Display / Cart Summary       │
└────────┬────────────────────────────────┘
         │ HTTP/REST
         ↓
┌─────────────────────────────────────────┐
│    Backend (Flask + Python 3.12)        │
│  ┌─────────────────────────────────┐   │
│  │  Chat Service (LangChain Agent) │   │
│  │  Autonomous LLM Tool Calling    │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Services                       │   │
│  │  - CartService / OrderService   │   │
│  │  - RAGService (Faiss/Pinecone)  │   │
│  │  - VectorService + Policy RAG   │   │
│  └─────────────────────────────────┘   │
└────┬───────────┬──────────┬──────────────┘
     │           │          │
     ↓           ↓          ↓
┌────────────┐ ┌────────┐ ┌──────────┐
│ SQLite     │ │Pinecone│ │Groq API  │
│ Database   │ │Vector  │ │(Llama 3) │
│            │ │Search  │ │          │
└────────────┘ └────────┘ └──────────┘
```

---

## 🎯 Chat Service: Autonomous Agent System

Instead of outdated deterministic keyword branches, the system relies entirely on an intelligent LLM injected with dynamic context and functional tools.

### 1. Vectorized Memory & Context (RAG)
- **Playbook & CGV Injection:** User queries are vectorized dynamically against `support-kb`. Relevant contextual chunks (return policies, shipping, etc.) are injected into the System Prompt.
- **Support Context Overlays:** Prevents hallucination by restricting the LLM to only respond based on the retrieved factual context.

### 2. Deep Tool Integration (Function Calling)
The LLM dynamically invokes backend functions via LangChain `bind_tools`:
- `track_order`: Looks up the database for live status (with auto `ORD-` prefixing tolerance).
- `cancel_order`: Cancels active orders and computes refunds.
- `add_to_cart`: Modifies the user's persistent database cart with explicit product IDs.
- `search_products` & `filter_products`: Uses Vector Search to intelligently match products to user inquiries without guessing names or prices.
- `get_product_details`: Retrieves absolute product specs, descriptions, and stock status using exact ID or name lookup.
- `get_recommendations`: Uses Pinecone semantic similarity to fetch top 4 similar products based on a reference product or description.
- `lookup_support_policy`: Retrieves policy-grounded support context from the RAG knowledge base (FAQ + CGV).

### 3. Anti-Hallucination Guardrails
- **Grounded Policy Answers:** The LLM is instructed to use policy retrieval tools and refuse unsupported claims when support context is missing.

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 15.1.11 (TypeScript, Tailwind CSS)
- **Features:** Server-side rendering, real-time cart updates, streaming chat text

### Backend
- **Framework:** Flask (Python 3.12)
- **Architecture:** LangChain Agents, SentenceTransformers (Embeddings)
- **Vector DB:** Pinecone
- **LLM:** Groq (Llama-3.1-8b-instant)
- **Database:** Internal SQLite

### Infrastructure
- **Containerization:** Docker & Docker Compose (`docker-compose up --build`)
- **Testing:** Comprehensive `unittest` suite measuring 28 specification constraints.

---

## ✅ Verified Specifications (specifications.md)

- [x] **Commandes & Suivi :** Order tracking, delay estimates, partial delivery handling.
- [x] **Livraison & Expédition :** Shipping costs, tracking neighbor deliveries, DOM-TOM calculations.
- [x] **Paiement & Facturation :** Refusals, installment methods, promo codes.
- [x] **Retours & Échanges :** Return policies, shipping labels, and refund timelines.

*All 28 critical business specs verified via `test_spec_scenarios.py` with 100% pass rate.*

---

## 🚀 Running the Application

### Production (Docker Compose)
```bash
# Set your .env parameters first
docker-compose up -d --build
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

### Run Specifications Tests
```bash
docker-compose exec backend python -m unittest discover -s tests -v
```

**Last Updated:** April 2026
**Status:** Spec-Compliant MVC Release
