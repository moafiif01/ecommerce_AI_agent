# Ecommerce Chatbot - Mermaid Diagrams

## 1. System Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["Frontend (Next.js)"]
        Chat["Chat Page<br/>page.tsx"]
        Checkout["Checkout Page<br/>checkout.tsx"]
        Cart["Cart Panel<br/>CartSummary.tsx"]
        Input["ChatInput"]
        Message["ChatMessage"]
    end

    subgraph Backend["Backend (Flask)"]
        ChatRoute["Chat Routes<br/>POST /api/chat/message"]
        CartRoute["Cart Routes<br/>POST /api/cart/add"]
        CheckoutRoute["Checkout Routes<br/>POST /api/checkout/place-order"]
        OrderRoute["Order Routes<br/>GET /api/order/:number"]
        
        ChatService["Chat Service<br/>(LangChain Agent)"]
        CartService["Cart Service"]
        OrderService["Order Service"]
        SupportService["Support Service"]
    end

    subgraph Database["Data Layer"]
        PostgreSQL["PostgreSQL<br/>Database"]
        Products["Products Table"]
        Carts["Carts Table"]
        Orders["Orders Table"]
        Messages["Messages Table"]
    end

    subgraph External["External Services"]
        Pinecone["Pinecone<br/>Vector Search"]
        Groq["Groq LLM<br/>Claude 3"]
    end

    Chat -->|"POST /api/chat/message"| ChatRoute
    Input -->|"User Input"| Chat
    Message -->|"Display"| Chat
    Cart -->|"GET /api/cart"| CartRoute
    Checkout -->|"POST /api/checkout"| CheckoutRoute

    ChatRoute -->|"Process"| ChatService
    CartRoute -->|"Manage"| CartService
    CheckoutRoute -->|"Process"| CartService
    OrderRoute -->|"Fetch"| OrderService

    ChatService -->|"Search Products"| Pinecone
    ChatService -->|"Generate Response"| Groq
    ChatService -->|"Query KB"| SupportService

    ChatService -->|"Read/Write"| PostgreSQL
    CartService -->|"Read/Write"| PostgreSQL
    OrderService -->|"Read"| PostgreSQL

    PostgreSQL --> Products
    PostgreSQL --> Carts
    PostgreSQL --> Orders
    PostgreSQL --> Messages

    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style Database fill:#f3e5f5
    style External fill:#e8f5e9
```

---

## 2. Chat Service - Autonomous Agent Flow (LangChain)

```mermaid
graph TD
    Input["User Message<br/>Received"]
    
    Input --> Memory["Load Chat History<br/>& Retrieve RAG Context"]
    Memory --> Guardrails{"Guardrail<br/>Check?"}
    
    Guardrails -->|Out of Domain| GuardResponse["Response:<br/>Polite rejection"]
    Guardrails -->|Valid| AgentPrompt["Build System Prompt<br/>Inject Support Context"]
    
    AgentPrompt --> LLM{"ChatGroq LLM<br/>(bind_tools)"}
    
    LLM -->|Tool Call: track_order| TrackTool["track_order(ORD...)"]
    TrackTool --> LLM
    
    LLM -->|Tool Call: add_to_cart| CartTool["add_to_cart(id, qty)"]
    CartTool --> LLM
    
    LLM -->|Tool Call: search/filter| SearchTool["search_products(query)"]
    SearchTool --> LLM
    
    LLM -->|Direct Answer| FinalAnswer["Generate Final text<br/>Extract [RECOMMENDED_IDS]"]
    
    FinalAnswer --> Metadata["Add Metadata<br/>source: llm, etc."]
    GuardResponse --> Metadata
    
    Metadata --> Return["Return to Frontend"]
    
    style Guardrails fill:#ffe2e2
    style LLM fill:#e1bee7
    style TrackTool fill:#bbdefb
    style CartTool fill:#c8e6c9
    style SearchTool fill:#fff9c4
    style Return fill:#b2ebf2
```

---

## 3. Add-to-Cart Flow (Autonomous Tooling)

```mermaid
sequenceDiagram
    actor User
    participant Frontend as Next.js<br/>Frontend
    participant Agent as LangChain<br/>Agent (LLM)
    participant Backend as Flask<br/>Backend Tools
    participant DB as PostgreSQL
    participant Pinecone as Pinecone<br/>Vector Search

    User->>Frontend: "add 2 iPhone 15 Pro to cart"
    Frontend->>Frontend: Detect chatSessionId & cart_session_id
    Frontend->>Backend: POST /api/chat/message
    
    Backend->>Agent: Invoke ChatGroq with System Prompt & Tools
    Agent->>Agent: Analyzes intent:<br/>Needs product ID to add to cart
    Agent-->>Backend: ToolCall: search_products("iPhone 15 Pro")
    
    Backend->>Pinecone: Vector search: "iPhone 15 Pro"
    Pinecone-->>Backend: Matches
    Backend->>DB: Fetch details
    DB-->>Backend: [ID: uuid-xxx, Stock: 15]
    Backend-->>Agent: ToolResponse: Found product [ID: uuid-xxx]
    
    Agent->>Agent: Prepares to add to cart
    Agent-->>Backend: ToolCall: add_to_cart(product_id="uuid-xxx", qty=2)
    
    Backend->>DB: cart_items INSERT (cart_session_id, qty=2)
    DB-->>Backend: Success
    Backend-->>Agent: ToolResponse: Added successfully
    
    Agent-->>Backend: Final Answer: "J'ai ajouté 2 iPhone 15 Pro à votre panier."
    Backend-->>Frontend: {success: true, content: "J'ai ajouté...", products: [...]}
    
    Frontend->>Frontend: Update CartSummary badge
    User->>User: Sees response & cart updated
```

---

## 4. Checkout Workflow

```mermaid
graph TD
    A["User in Chat/<br/>Product View"] -->|"Adds Items"| B["Items in Cart<br/>cart_session_id linked"]
    
    B -->|"Clicks Cart Icon"| C["Cart Panel Opens<br/>Shows items + total"]
    
    C -->|"Review items OK"| D["Click Checkout"]
    
    D -->|"Route to"| E["Checkout Page<br/>checkout.tsx"]
    
    E -->|"Enter"| F["Shipping Address<br/>Form"]
    
    F -->|"Select"| G["Shipping Method<br/>Standard/Express/Overnight"]
    
    G -->|"Validate"| H["CheckoutService<br/>validate()"]
    
    H -->|"Checks"| I["✓ Cart not empty?<br/>✓ Address valid?<br/>✓ Method selected?"]
    
    I -->|"All Valid"| J["Click 'Place Order'"]
    
    J -->|"Submit"| K["CheckoutService<br/>place_order()"]
    
    K -->|"Creates"| L["Order Record<br/>ORD-XXXXXXXX"]
    
    L -->|"Moves items"| M["Order → OrderItems"]
    
    M -->|"Clears"| N["Cart for session"]
    
    N -->|"Success"| O["Show Confirmation<br/>Order #, Total, ETA"]
    
    O -->|"User home"| P["Redirect to Chat<br/>Fresh cart_session_id"]
    
    style A fill:#e8f5e9
    style E fill:#fff3e0
    style K fill:#ffebee
    style O fill:#c8e6c9
```

---

## 5. Database Schema Relationships

```mermaid
erDiagram
    CHAT_SESSION ||--o{ MESSAGE : contains
    MESSAGE }o--|| PRODUCT : references
    PRODUCT ||--o{ CART_ITEM : "added to"
    CART ||--o{ CART_ITEM : contains
    
    PRODUCT {
        uuid id PK
        string name
        text description
        float price
        string category
        string image_url
        float rating
        boolean in_stock
        timestamp created_at
    }
    
    CART {
        uuid id PK
        string session_id UK "guest cart link"
        uuid user_id FK "optional"
        timestamp created_at
        timestamp updated_at
    }
    
    CART_ITEM {
        uuid id PK
        uuid cart_id FK
        uuid product_id FK
        integer quantity
        timestamp created_at
    }
    
    CHAT_SESSION {
        uuid id PK
        uuid user_id FK "nullable"
        timestamp created_at
    }
    
    MESSAGE {
        uuid id PK
        uuid session_id FK
        text content
        boolean is_bot
        string type "text,product"
        json metadata
        timestamp created_at
    }
    
    ORDER {
        uuid id PK
        string order_number UK "ORD-XXXXXXXX"
        string status "pending,processing,shipped,delivered"
        float total_amount
        string shipping_address
        string shipping_method
        uuid user_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    ORDER_ITEM {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        integer quantity
        float price_at_purchase
    }
    
    CHAT_SESSION ||--o{ ORDER : "user places"
    ORDER ||--o{ ORDER_ITEM : contains
```

---

## 6. API Request/Response Flow

```mermaid
graph LR
    subgraph Request["Request"]
        Req1["POST /api/chat/message"]
        Req2["Body: {<br/>message: string,<br/>session_id: string,<br/>cart_session_id: string<br/>}"]
    end
    
    subgraph Processing["Processing"]
        Proc1["1. Validate input"]
        Proc2["2. Route to ChatService"]
        Proc3["3. Agent Tool Call<br/>(LangChain)"]
        Proc4["4. Execute tool action"]
        Proc5["5. Query external<br/>services if needed"]
        Proc6["6. Persist to DB"]
    end
    
    subgraph Response["Response"]
        Resp1["Status: 200 OK"]
        Resp2["Body: {<br/>success: bool,<br/>session_id: string,<br/>response: {<br/>  id: uuid,<br/>  content: string,<br/>  type: text|product,<br/>  products: [],<br/>  metadata: {...}<br/>}<br/>}"]
    end
    
    Req1 --> Proc1
    Req2 --> Proc1
    Proc1 --> Proc2
    Proc2 --> Proc3
    Proc3 --> Proc4
    Proc4 --> Proc5
    Proc5 --> Proc6
    Proc6 --> Resp1
    Proc6 --> Resp2
    
    style Request fill:#bbdefb
    style Processing fill:#fff9c4
    style Response fill:#c8e6c9
```

---

## 7. User Journey: From Chat to Order

```mermaid
journey
    title User Journey: Chat to Purchase
    section Discovery
      User opens chat: 5: User, System
      Asks about products: 5: User
      Chat recommends iPhone: 5: System
    section Add to Cart
      User says "add iPhone": 5: User
      System detects intent: 5: System
      Item added to cart: 5: System
      User sees confirmation: 5: User
    section Checkout
      User opens cart: 5: User
      Reviews items: 4: User
      Fills address: 4: User
      Selects shipping: 4: User
      Places order: 5: User
    section Confirmation
      Order created: 5: System
      Confirmation shown: 5: User
      Order tracking ready: 5: System
```

---

## 8. Docker Compose Services

```mermaid
graph TB
    subgraph Docker["Docker Compose - Production"]
        Frontend["Frontend Service<br/>Node:20-Alpine<br/>Port 3000"]
        Backend["Backend Service<br/>Python:3.12-slim<br/>Port 5001"]
        DB["PostgreSQL Service<br/>Port 5432"]
    end
    
    Frontend -->|"HTTP REST"| Backend
    Backend -->|"SQL Queries"| DB
    
    ExtFunc["External Functions"]
    
    Backend -->|"Vector Search"| PineconeAPI["Pinecone API"]
    Backend -->|"LLM Calls"| GroqAPI["Groq API"]
    
    User["User Browser"]
    User -->|"http://localhost:3000"| Frontend
    
    style Frontend fill:#e1f5ff
    style Backend fill:#fff3e0
    style DB fill:#f3e5f5
    style PineconeAPI fill:#e8f5e9
    style GroqAPI fill:#e8f5e9
```

---

## 9. Order Status State Machine

```mermaid
stateDiagram-v2
    [*] --> Pending: Order Created
    
    Pending --> Processing: Payment Confirmed
    Pending --> Cancelled: User Cancels
    
    Processing --> Shipped: Items Packed<br/>Label Generated
    Processing --> Cancelled: Inventory Issue
    
    Shipped --> InTransit: Carrier<br/>Picked Up
    
    InTransit --> Delivered: Delivered<br/>Signature Required
    InTransit --> DeliveryFailed: Address Issue<br/>Return to Sender
    
    Delivered --> [*]: Order Complete
    Cancelled --> [*]: Order Ended
    DeliveryFailed --> Pending: Re-attempt
    
    note right of Pending
        Awaiting payment confirmation
        or fulfillment start
    end note
    
    note right of Shipped
        In warehouse or
        transit to carrier
    end note
    
    note right of Delivered
        Signature obtained
        or left at location
    end note
```

---

## 10. Integration Test Layers

```mermaid
graph BT
    subgraph L4["Layer 4: Behavioral Comparison"]
        Comparison["Pre-Migration vs<br/>Post-Migration<br/>Behavior Verification"]
    end
    
    subgraph L3["Layer 3: Azure Integration"]
        AzureIntegration["Azure Services<br/>Connectivity Test"]
    end
    
    subgraph L2["Layer 2: Smoke Tests"]
        Smoke1["Chat API<br/>Health Check"]
        Smoke2["Cart Operations<br/>CRUD"]
        Smoke3["Order Placement"]
    end
    
    subgraph L1["Layer 1: TestContainers"]
        TC1["PostgreSQL<br/>Container"]
        TC2["Redis Cache<br/>Container"]
        TC3["Mock Services<br/>Container"]
    end
    
    L1 --> L2
    L2 --> L3
    L3 --> L4
    
    style L1 fill:#bbdefb
    style L2 fill:#fff9c4
    style L3 fill:#ffe0b2
    style L4 fill:#c8e6c9
```

---

## 11. Feature flags & A/B Testing

```mermaid
graph TD
    Feature["Feature<br/>LLM Model Selection"]
    
    Feature --> Flag1["Flag: groq_model<br/>Default: llama-3.1-8b"]
    
    Flag1 -->|"User A<br/>50%"| V1["Control:<br/>llama-3.1-8b-instant"]
    Flag1 -->|"User B<br/>50%"| V2["Treatment:<br/>llama-3.3-70b-versatile"]
    
    V1 --> Metric1["Metrics:<br/>- Tool calling accuracy<br/>- Latency (ms)<br/>- Chat conversion rate"]
    V2 --> Metric1
    
    Metric1 --> Decision["Compare & Decide<br/>Promote faster/cheaper model"]
    
    style Feature fill:#e1f5ff
    style V1 fill:#ffebee
    style V2 fill:#c8e6c9
```

---

## 12. Message Flow with Session Linking

```mermaid
sequenceDiagram
    participant Browser as Browser<br/>localStorage
    participant Frontend as Next.js<br/>Frontend
    participant Backend as Flask<br/>Backend
    participant DB as PostgreSQL
    
    Note over Browser,DB: Initial Setup
    Browser->>Frontend: Load page
    Frontend->>Frontend: If no chatSessionId<br/>Generate new UUID
    Frontend->>Browser: Store chatSessionId
    Browser->>Frontend: Retrieve chatSessionId
    
    Frontend->>Frontend: If no cart_session_id<br/>Generate new UUID
    Frontend->>Browser: Store cart_session_id
    Browser->>Frontend: On every message
    
    Note over Browser,DB: User Sends Message
    User->>Frontend: "add iPhone to cart"
    
    Frontend->>Frontend: Gather context:<br/>- Message text<br/>- chatSessionId<br/>- cart_session_id
    
    Frontend->>Backend: POST /api/chat/message<br/>{message, session_id, cart_session_id}
    
    Backend->>DB: Lookup chat_session<br/>by session_id
    Backend->>DB: Save message<br/>to chat_session
    Backend->>DB: Add item to cart<br/>using cart_session_id
    
    DB-->>Backend: ItemAdded ✓
    Backend-->>Frontend: {success: true, cart_session_id}
    
    Frontend->>Browser: Verify cart_session_id<br/>matches (persist)
    Frontend->>Frontend: Render message in chat
    Frontend->>Frontend: Update CartSummary<br/>via GET /api/cart
    
    Browser->>Frontend: On next page load<br/>Restore both IDs from localStorage
    
    Note over Frontend: Even if browser closes<br/>and reopens, cart<br/>is restored via cart_session_id
```

---

## How to Use These Diagrams

### Option 1: Copy to Markdown
Paste any diagram code block into a `.md` file and render using:
- GitHub (native Mermaid support)
- GitLab
- Confluence
- Notion

### Option 2: Online Editor
Paste code into: https://mermaid.live

### Option 3: VS Code Extension
Install "Markdown Preview Mermaid Support" extension

### Option 4: Generate PNG/SVG
```bash
npm install -g mermaid-cli
mmdc -i diagram.mmd -o diagram.png
```

---

**Created:** April 18, 2026
