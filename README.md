# S-TORE: AI-Powered E-commerce Platform

A full-stack e-commerce platform featuring an intelligent AI shopping assistant, vector-based product search with Pinecone, and a modern React/Next.js frontend. **Chatbot with advanced product search, recommendations, and order/cart management.**

![alt text](.github/res/image-1.png)
![alt text](.github/res/image.png)

## Features

### **AI Shopping Assistant**

- Natural language product search and recommendations
- State-of-the-art AI with 1M token context window
- Advanced conversation memory and tool orchestration
- AI-driven product suggestions based on user behavior

### **Advanced Search & Discovery**

- Vector-based product discovery using Pinecone
- Find products by description, features, or use cases
- Price range, brand, category, ratings, and availability
- Context-aware product suggestions

### **Complete E-commerce Experience**

- Persistent cart with real-time updates
- Favorites, likes, and personalized settings
- Real-time stock management and availability

## Architecture

```
├── Frontend (Next.js)
│   ├── Modern UI
│   ├── Responsive design & animations
│   ├── Real-time chat interface
│   └── Shopping cart & product pages
│
├── Backend API (Flask + Python)
│   ├── RESTful API endpoints
│   ├── JWT authentication
│   ├── Database models & services
│   └── AI chatbot integration
│
├── AI Services
│   ├── Groq-hosted LLM
│   ├── LangChain orchestration
│   ├── Pinecone vector database
│   └── Sentence Transformers
│
└── Data Layer
    ├── SQLite database (for dev)
    ├── Vector embeddings
    └── Session management
```

## Quick Start

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.12+ (for backend)
- **Groq** API key
- **Pinecone** account and API key

### Tech

- **Language Model**: Groq-hosted Llama models
- **Framework**: LangChain for orchestration
- **Vector Database**: Pinecone for semantic search
- **Embeddings**: Sentence Transformers

### Development Guidelines

- Follow TypeScript/Python best practices
- Add tests for new features
- Update documentation
- Ensure code passes linting

## Continuous Integration

GitHub Actions workflow:

- File: `.github/workflows/ci.yml`
- Trigger: push + pull_request
- Jobs:
    - Backend integration tests (`server/tests`) with Python 3.12
    - Backend dependency security scan with `pip-audit`
    - Frontend production build (`apps/web`) with Node.js 20
    - Docker image build validation for backend and frontend
    - Pull request dependency review (`actions/dependency-review-action`)

## Continuous Delivery

GitHub Actions workflow:

- File: `.github/workflows/cd.yml`
- Trigger: tag push matching `v*` or manual dispatch
- Publishes backend/frontend Docker images to GHCR:
    - `ghcr.io/<owner>/<repo>/backend`
    - `ghcr.io/<owner>/<repo>/frontend`

## Project Diagrams

- Open [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for Mermaid diagrams covering architecture, chat flow, Docker, CI/CD, orders, routes, and state transitions.

## Docker Quick Start

Prerequisite:

- Docker Desktop with Compose support

Steps:

1. Configure backend secrets in `server/.env` (at minimum `GROQ_API_KEY`, `PINECONE_API_KEY`, `SECRET_KEY`, `JWT_SECRET_KEY`)
2. Build and start all services:

```bash
docker compose up --build
```

If port 3000 or 5000 is already in use, override host ports before starting:

```bash
# PowerShell example
$env:FRONTEND_HOST_PORT="3001"
$env:BACKEND_HOST_PORT="5001"
docker compose up --build
```

3. Open apps:

- Frontend (default): http://localhost:3000
- Backend health (default): http://localhost:5000/api/health
- If you override host ports, use the overridden values.

To stop:

```bash
docker compose down
```

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.
