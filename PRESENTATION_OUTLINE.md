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

## 3) Autonomous Order Management (Tool Calling)

### Real-Time Order Tracking
- The agent autonomously invokes the `track_order` tool when an intent is detected.
- Example: "Where is order #12345?" (Agent extracts ID safely).

### Modification/Cancellation Execution
- Uses the `cancel_order` tool to programmatically refund and cancel eligible orders without human intervention.

### Invoice Access
- Direct users to downloadable invoice location or endpoint.

## 4) Advanced Agentic Behaviors

### Autonomous Product Operations
- Agent calls `search_products`, `filter_products`, and `get_recommendations` based on conversational needs.
- Formats and displays products dynamically with exact IDs bound to UI elements via `[RECOMMENDED_IDS]`.

### Native Add-to-Cart Action
- Rather than mere suggestions, the agent physically drives the ecommerce state using `add_to_cart` tool integration based on conversational intent.

### Out-of-Domain Guardrails
- System prompts block and politely decline non-ecommerce topics (e.g., political or unrelated questions).
- Strict adherence to factual data avoiding hallucinations on inventory/price.

## 5) Technical And DevOps Features

### Dockerization
- Containerize the full stack (Flask backend, frontend, chatbot logic) for consistent deployment across environments.

