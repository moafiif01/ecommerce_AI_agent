# Ecommerce Chatbot - Project Overview

## 📋 Project Description

A full-stack ecommerce chatbot application that combines natural language processing with intelligent cart management. Users can browse products, ask questions, track orders, and add items to cart through conversational AI. The system uses vector search for product discovery and an LLM (Groq) for intelligent responses.

**Status:** ✅ MVP Complete - Core features functional and tested

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────┐
│    Frontend (Next.js 15.1.11)           │
│  - Chat Interface (page.tsx)            │
│  - CartSummary Component                │
│  - Product Display                      │
│  - Checkout Workflow                    │
└────────┬────────────────────────────────┘
         │ HTTP/REST
         ↓
┌─────────────────────────────────────────┐
│    Backend (Flask + Python 3.12)        │
│  ┌─────────────────────────────────┐   │
│  │  Chat Service (4-Branch)        │   │
│  │  1. Add-to-Cart Intent          │   │
│  │  2. Order Tracking              │   │
│  │  3. Support/FAQ                 │   │
│  │  4. General Chat (LLM)          │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  Services                       │   │
│  │  - CartService                  │   │
│  │  - OrderService                 │   │
│  │  - CheckoutService              │   │
│  │  - SupportAgentService          │   │
│  └─────────────────────────────────┘   │
└────┬───────────┬──────────┬──────────────┘
     │           │          │
     ↓           ↓          ↓
┌────────────┐ ┌────────┐ ┌──────────┐
│ PostgreSQL │ │Pinecone│ │Groq LLM  │
│ Database   │ │Vector  │ │(Claude)  │
│            │ │Search  │ │          │
└────────────┘ └────────┘ └──────────┘
```

---

## 💾 Database Schema

### Core Models

**Products**
- `id` (UUID)
- `name` (string)
- `description` (text)
- `price` (float)
- `category` (string)
- `image_url` (string)
- `rating` (float)
- `in_stock` (boolean)
- `created_at` (timestamp)

**Cart & Cart Items**
- `cart.id` (UUID)
- `cart.session_id` (string) - Links guest carts to chat sessions
- `cart.created_at` (timestamp)
- `cart.updated_at` (timestamp)
- `cart_item.id` (UUID)
- `cart_item.cart_id` (FK)
- `cart_item.product_id` (FK)
- `cart_item.quantity` (int)

**Orders**
- `id` (UUID)
- `order_number` (string) - Format: `ORD-XXXXXXXX`
- `status` (enum: pending, processing, shipped, delivered, cancelled)
- `total_amount` (float)
- `shipping_address` (string)
- `shipping_method` (enum)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**Chat Sessions & Messages**
- `chat_session.id` (UUID)
- `chat_session.user_id` (FK, nullable)
- `chat_session.created_at` (timestamp)
- `message.id` (UUID)
- `message.session_id` (FK)
- `message.content` (text)
- `message.is_bot` (boolean)
- `message.type` (enum: text, product)
- `message.metadata` (JSON)
- `message.created_at` (timestamp)

---

## 🔌 API Endpoints

### Chat API
- `POST /api/chat/message`
  - **Input:** `{ message: string, session_id: string, cart_session_id: string }`
  - **Output:** `{ success: bool, response: Message, metadata: Object }`
  - **Intent Detection:** Analyzes message for add-to-cart, order tracking, support queries

- `GET /api/chat/history/:session_id`
  - **Output:** Array of messages with chat history

- `GET /api/chat/health`
  - **Output:** `{ status: "ok", services: Object }`
  - **Dependencies:** Pinecone, Groq, Database

### Cart API
- `POST /api/cart/add`
  - **Input:** `{ product_id: string, quantity: int, cart_session_id: string }`
  - **Output:** `{ success: bool, cart: Cart }`
  - **Mutation:** Deterministic - idempotent add operations

- `GET /api/cart/:cart_session_id`
  - **Output:** `{ items: Array, total: float, item_count: int }`

- `DELETE /api/cart/item/:item_id`
  - **Output:** `{ success: bool }`

### Checkout API
- `POST /api/checkout/validate`
  - **Input:** `{ cart_session_id: string, shipping_address: string }`
  - **Output:** `{ valid: bool, errors: Array }`

- `POST /api/checkout/place-order`
  - **Input:** `{ cart_session_id: string, shipping_address: string, shipping_method: string }`
  - **Output:** `{ success: bool, order_id: string, order_number: string }`

### Order API
- `GET /api/order/:order_number`
  - **Output:** `{ order: Order, items: Array, status: string }`

- `POST /api/order/track`
  - **Input:** `{ order_number: string }`
  - **Output:** `{ found: bool, order: Order }`

---

## 🎯 Chat Service: 4-Branch Intent Detection

### Branch 1: Add-to-Cart Intent
**Pattern:** Detects "add X product to cart"
- Extracts product name and quantity
- Searches products by name (exact match) or via Pinecone vector search
- Calls `CartService.add_item(cart_id, product_id, quantity)`
- Returns: `"Added X × [Product] to your cart"` (only if mutation succeeds)
- **Confidence:** High (deterministic pattern matching)

### Branch 2: Order Tracking
**Pattern:** Detects `ORD-XXXXXXXX` order number format
- Calls `OrderService.get_order_by_number(order_number)`
- Returns: Live order status, items, tracking info
- **Confidence:** High (format matching)

### Branch 3: Support/FAQ
**Pattern:** Detects support-related keywords (return, shipping, payment, etc.)
- Searches support knowledge base via semantic search
- If confidence ≥ threshold: Returns direct KB answer
- Otherwise: Falls back to Branch 4
- **Confidence:** Medium (threshold-based)

### Branch 4: General Chat (LLM)
**Pattern:** Fallback for all unmatched queries
- Queries Pinecone vector index for top 5 product matches
- Builds system prompt with:
  - Product catalog context
  - Chat history (last 5 messages)
  - Instructions: "Encourage user to use 'Add to Cart' button for products"
  - Constraint: "Don't hallucinate prices or features"
- Sends to Groq LLM (Claude backend)
- Returns: LLM-generated conversational response
- **Confidence:** Medium-High (LLM-based)

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 15.1.11
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **State Management:** React hooks
- **Features:**
  - Server-side rendering (SSR)
  - API route handlers
  - Real-time cart updates
  - Chat message streaming (ready)

### Backend
- **Framework:** Flask
- **Language:** Python 3.12
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL
- **Vector Search:** Pinecone (product embeddings)
- **LLM:** Groq (Claude 3)
- **Auth:** Session-based (guest & authenticated)

### Infrastructure
- **Containerization:** Docker & Docker Compose
- **Frontend Image:** Node 20 Alpine
- **Backend Image:** Python 3.12 slim
- **Ports:** Frontend 3000, Backend 5001
- **Environment:** Development & Production-ready

### External Services
- **Pinecone:** Vector embeddings for semantic product search
- **Groq API:** LLM generation for chat responses
- **PostgreSQL:** Primary data store

---

## ✅ Completed Features

### Core Functionality
- [x] Chat interface with real-time messaging
- [x] Product catalog (indexed in Pinecone)
- [x] Add-to-cart through natural language
- [x] Cart management (view, add, remove items)
- [x] Checkout workflow (address + shipping method)
- [x] Order placement and tracking
- [x] Order status detection by order number
- [x] Support KB integration
- [x] Multi-intent chat detection

### Backend Services
- [x] Chat service with 4-branch detection
- [x] Deterministic cart mutations
- [x] Cart session linking (guest carts)
- [x] Order tracking service
- [x] Support agent service
- [x] Database models and migrations
- [x] REST API endpoints
- [x] Error handling and validation

### Frontend UI
- [x] Chat page with message history
- [x] Product display in chat (with images, ratings)
- [x] Cart summary header widget
- [x] Cart panel (view/edit items)
- [x] Checkout page
- [x] Responsive design
- [x] Session persistence

### DevOps
- [x] Docker containerization
- [x] Docker Compose orchestration
- [x] Build optimization (multi-stage, Alpine)
- [x] Environment configuration (.env)
- [x] Health check endpoints

### Testing & Validation
- [x] End-to-end API tests
- [x] Cart mutation verification
- [x] Order tracking tests
- [x] Chat intent detection tests
- [x] Docker build validation

---

## 📝 Current Status

### Working Features
✅ Chat messaging and response generation  
✅ Add-to-cart through chat  
✅ Cart viewing and management  
✅ Order tracking by order number  
✅ Product search via Pinecone  
✅ Checkout workflow  
✅ Docker deployment  

### Known Limitations
- Payment integration: Mock only (Stripe not integrated)
- Order notifications: DB schema ready, pipeline not implemented
- Authentication: Session-based, no user accounts yet
- Product images: Static URLs, no image upload

---

## 🚀 Running the Application

### Prerequisites
```bash
# Environment Variables (.env)
DATABASE_URL=postgresql://user:pass@localhost/ecommerce
PINECONE_API_KEY=your_pinecone_key
GROQ_API_KEY=your_groq_key
FLASK_ENV=development
```

### Development (Local)
```bash
# Terminal 1: Backend
cd ecommerce-chatbot/server
python app.py  # Runs on http://localhost:5001

# Terminal 2: Frontend
cd ecommerce-chatbot/apps/web
npm run dev    # Runs on http://localhost:3001
```

### Production (Docker)
```bash
cd ecommerce-chatbot
docker compose up -d --build

# Access
# Frontend: http://localhost:3000
# Backend: http://localhost:5001
```

---

## 📊 Project Statistics

| Metric | Value |
|--------|-------|
| **Frontend Files** | 15+ .tsx components |
| **Backend Routes** | 12 API endpoints |
| **Database Tables** | 8 core tables |
| **Chat Branches** | 4 intent detectors |
| **External Services** | 3 (Pinecone, Groq, PostgreSQL) |
| **Container Images** | 2 (Frontend, Backend) |
| **Completed Tasks** | 7/8 |

---

## 🎯 Next Steps (Future)

1. **Payment Integration**
   - Integrate Stripe for real transactions
   - Handle payment webhooks
   - Store payment methods

2. **Order Notifications**
   - Email notifications on order status changes
   - SMS alerts
   - In-app notification center

3. **User Authentication**
   - Email/password signup
   - OAuth integration
   - Order history per user

4. **Advanced Chat Features**
   - Message streaming (SSE)
   - Typing indicators
   - Message reactions
   - Chat search/filters

5. **Analytics**
   - User behavior tracking
   - Chat intent analysis
   - Conversion funnel
   - Popular products

6. **Admin Dashboard**
   - Order management
   - Product inventory
   - Support KB management
   - Analytics reporting

---

## 📂 Project Structure

```
ecommerce-chatbot/
├── apps/
│   └── web/                    # Next.js Frontend
│       ├── app/
│       │   ├── chat/           # Chat page
│       │   ├── checkout/       # Checkout flow
│       │   └── layout.tsx      # Root layout
│       ├── components/         # Reusable components
│       │   ├── ChatMessage.tsx
│       │   ├── CartSummary.tsx
│       │   ├── ChatInput.tsx
│       │   └── ProductCard.tsx
│       └── package.json
├── server/                     # Flask Backend
│   ├── app.py                  # Entry point
│   ├── routes/
│   │   ├── chat_routes.py      # Chat endpoints
│   │   ├── cart_routes.py      # Cart endpoints
│   │   ├── checkout_routes.py  # Checkout endpoints
│   │   └── order_routes.py     # Order endpoints
│   ├── services/
│   │   ├── chat_service.py     # Chat logic (4-branch)
│   │   ├── cart_service.py     # Cart mutations
│   │   ├── order_service.py    # Order tracking
│   │   └── support_service.py  # KB search
│   ├── models/
│   │   └── models.py           # SQLAlchemy ORM
│   └── requirements.txt
├── docker-compose.yml          # Orchestration
├── Dockerfile.backend          # Python container
└── PROJECT_OVERVIEW.md         # This file
```

---

## 🔍 Key Code Flow: "Add 2 iPhone 15 Pro to cart"

1. **User types:** `"add 2 iPhone 15 Pro to cart"`
2. **Frontend sends:** `POST /api/chat/message`
   - `message: "add 2 iPhone 15 Pro to cart"`
   - `cart_session_id: "abc123"`
3. **Backend Chat Service Branch 1 triggers:**
   - Regex: `r"add\s+(\d+)\s+(.+?)\s+to\s+cart"`
   - Extracts: quantity=2, product_name="iPhone 15 Pro"
   - Searches DB or Pinecone
4. **CartService.add_item() called:**
   - Finds product_id
   - Creates/updates CartItem (quantity: 2)
   - Commits to DB (deterministic)
5. **Response sent:**
   ```json
   {
     "content": "Added 2 × iPhone 15 Pro to your cart",
     "type": "text",
     "metadata": { "source": "cart_action", "items_added": 2 }
   }
   ```
6. **Frontend updates:**
   - Renders message in chat
   - CartSummary shows new badge count
   - User can click cart icon to review

---

## 🐛 Debugging Tips

### Chat not responding?
- Check `/api/chat/health` endpoint
- Verify Pinecone and Groq keys in .env
- Check backend logs: `docker logs <backend-container>`

### Cart not updating?
- Verify `cart_session_id` is persisted in localStorage
- Check `/api/cart/:session_id` returns items
- Inspect database: `SELECT * FROM cart_items WHERE cart_id = ...`

### Products not found?
- Verify Pinecone index contains product embeddings
- Test vector search: Check Pinecone dashboard
- Fallback to exact name match in database

### Order tracking fails?
- Confirm order number format: `ORD-XXXXXXXX`
- Check database: `SELECT * FROM orders WHERE order_number = ...`
- Verify OrderService in backend

---

**Last Updated:** April 18, 2026  
**Status:** Production Ready (MVP)
