# Presentation Scope: Features To Keep Only

This file now contains only the requested feature scope.

## 1) Core Chatbot Interface Features

### Persistent Chat Widget
- Floating or embedded chat window accessible from any page.

### Streaming Responses
- Stream generated text token by token (or chunk by chunk) for faster perceived responsiveness with Groq.

### Conversational Memory
- Keep session-level context so follow-up questions remain coherent.
- Example: user asks "What about the blue one?" and the bot understands previous context.

### Suggested Prompts
- Quick-reply buttons for common intents, for example:
  - Track my order
  - Shipping policy
  - Return policy
  - Invoice help

## 2) RAG And Knowledge Base Integration

### Semantic Product Search
- Use Pinecone vector retrieval to match user intent, not only literal keywords.
- Example: "I need something for a rainy day" should map to relevant product features.

### Policy Consultation
- Answer Returns, Exchanges, and Refunds questions by retrieving indexed policy content.

### Source Attribution
- Show the cited source document/policy in responses to increase trust and reduce hallucination risk.

## 3) Order And Account Management (API Integration)

### Real-Time Order Tracking
- Ask for an order ID and return live status via API.
- Example: "Where is order #12345?"

### Modification/Cancellation Assistance
- Provide guided flow and eligibility checks for changing or cancelling orders post-purchase.

### Invoice Access
- Direct users to downloadable invoice location or endpoint.

## 4) Advanced Task-Oriented Capabilities

### Dispute And Litigative Handling
- Dedicated flows for issues like:
  - Item not received
  - Damaged goods
- Create or route support tickets when required.

### Multi-Step Reasoning
- Support tasks requiring chained logic, such as:
  - Product comparisons
  - Total price calculations including shipping based on destination.

### Out-of-Domain Guardrails
- Politely decline non-ecommerce topics (for example, political or unrelated questions).
- Keep brand-safe and professional tone.

## 5) Technical And DevOps Features

### Dockerization
- Containerize the full stack (Flask backend, frontend, chatbot logic) for consistent deployment across environments.

