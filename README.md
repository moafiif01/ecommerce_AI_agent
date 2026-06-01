# S-TORE — Agentic E-Commerce Assistant 🤖🛒

S-TORE is an advanced, production-grade AI shopping assistant built with **LangChain**. It bridges natural language user requests with structural backend data execution, utilizing tool calling, semantic retrieval, and real-time state synchronization.

---

## 🏗️ System Architecture

The agent acts as an orchestrator between the user interface, custom execution layers, and memory persistence:

```text
  User Input ──> [ LangChain Agentic Brain ] <──> [ RAG Context / Guardrails ]
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
  [ Vector Search ]   [ DB Tool Call ]  [ Memory State ]
  (Product Discovery)  (PostgreSQL UI)  (Session/Cart Sync)

  ✨ Core Features
Agentic Tool Calling: The assistant dynamically decides when to query the inventory, update customer carts, or initiate transactional cancellations.

RAG & Search Guardrails: Uses vector embeddings to match natural language queries with accurate catalog products while validating bounds (e.g., stopping unauthorized discount application).

Session Persistence: Manages multi-turn conversations and cart states reliably using PostgreSQL session handlers.

Robust Integrity & Test-Driven Design: Supported by 28 rigorous unit tests verifying exact calculations for cart revisions, dynamic shipping fees, and complex partial order updates.

🛠️ Tech Stack
Core Framework: LangChain, Python

Database & Storage: PostgreSQL (Transactional Data), Vector Database (Semantic Search)

Testing Suite: PyTest

🚦 Getting Started
1. Prerequisites
Python 3.10+

PostgreSQL instance

2. Installation
Bash
git clone [https://github.com/moafiif01/ecommerce_AI_agent.git](https://github.com/moafiif01/ecommerce_AI_agent.git)
cd ecommerce_AI_agent
pip install -r requirements.txt
3. Running the Test Suite
To verify the system's compliance with edge-case logic (cart mutations, shipping rules, and edge-case cancellation behaviors), run:

Bash
pytest tests/
📝 Key Engineering Takeaways
Designed safe execution scopes for agentic tools, preventing database injection risks during natural language parsing.

Achieved a highly reliable, deterministic cart synchronization system using atomic SQL transaction wrappers.
