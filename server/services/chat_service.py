import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from flask import current_app
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from models.chat_session import ChatSession
from models.message import Message
from models.product import Product

from .cart_service import CartService
from .product_service import ProductService
from .support_agent_service import SupportAgentService
from .vector_service import VectorService

logger = logging.getLogger(__name__)


class SimpleConversationMemory:
    def __init__(self):
        self.buffer = []


class ChatService:
    """Enhanced chat service with LangChain and Groq integration"""

    def __init__(self):
        self.llm = None
        self.vector_service = VectorService()
        self.product_service = ProductService()
        self.support_agent_service = SupportAgentService()
        self.memory_sessions = {}
        self.initialized = False

    def initialize(self):
        """Initialize LangChain components"""
        try:
            self.llm = ChatGroq(
                model=current_app.config["GROQ_MODEL"],
                groq_api_key=current_app.config["GROQ_API_KEY"],
                temperature=0.7,
                max_tokens=1000,
            )

            self.vector_service.initialize()

            self.initialized = True
            logger.info("Chat service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize chat service: {str(e)}")
            raise

    def get_or_create_memory(self, session_id: str) -> SimpleConversationMemory:
        """Get or create memory for a chat session"""
        if session_id not in self.memory_sessions:
            self.memory_sessions[session_id] = SimpleConversationMemory()
        return self.memory_sessions[session_id]

    def create_tools(self) -> List[Dict[str, Any]]:
        """Create tools for the LangChain agent"""
        tools = [
            {
                "name": "search_products",
                "description": "Find products using semantic search. Input: search query (str).",
                "func": self._search_products_tool,
            },
            {
                "name": "filter_products",
                "description": "Filter products. Input: JSON string with keys: category, subcategory, brand, min_price, max_price, min_rating, in_stock_only, features (list), search_query, limit.",
                "func": self._filter_products_tool,
            },
            {
                "name": "get_product_details",
                "description": "Get product details. Input: product ID (str).",
                "func": self._get_product_details_tool,
            },
            {
                "name": "get_recommendations",
                "description": "Get recommendations. Input: product ID (str) or preference description (str).",
                "func": self._get_recommendations_tool,
            },
        ]
        return tools

    def _search_products_tool(self, query: str) -> str:
        """Tool function for semantic product search"""
        try:
            similar_products = self.vector_service.search_similar_products(
                query, top_k=6
            )

            if not similar_products:
                return json.dumps(
                    {
                        "message": "No products found for the given query.",
                        "product_ids": [],
                    }
                )

            product_ids = [p["id"] for p in similar_products]
            products = Product.query.filter(Product.id.in_(product_ids)).all()

            result = "Found the following products:\n"
            for product in products:
                result += f"- {product.name} by {product.brand} - ${product.price}\n"
                result += f"  {product.description[:100]}...\n"

            return json.dumps({"message": result, "product_ids": product_ids})

        except Exception as e:
            logger.error(f"Error in search_products_tool: {str(e)}")
            return json.dumps(
                {
                    "message": "Error occurred while searching for products.",
                    "product_ids": [],
                }
            )

    def _filter_products_tool(self, filter_json: str) -> str:
        """Tool function for filtering products"""
        try:
            filters = json.loads(filter_json)
            products = Product.search_by_filters(**filters)

            if not products:
                return json.dumps(
                    {
                        "message": "No products found matching the specified filters.",
                        "product_ids": [],
                    }
                )

            result = f"Found {len(products)} products matching your criteria:\n"
            for product in products[:5]:
                result += f"- {product.name} by {product.brand} - ${product.price}\n"

            product_ids = [product.id for product in products[:5]]
            return json.dumps({"message": result, "product_ids": product_ids})

        except Exception as e:
            logger.error(f"Error in filter_products_tool: {str(e)}")
            return json.dumps(
                {
                    "message": "Error occurred while filtering products.",
                    "product_ids": [],
                }
            )

    def _get_product_details_tool(self, product_id: str) -> str:
        """Tool function for getting product details"""
        try:
            product = Product.query.get(product_id.strip())
            if not product:
                return "Product not found."

            result = "Product Details:\n"
            result += f"Name: {product.name}\n"
            result += f"Brand: {product.brand}\n"
            result += f"Price: ${product.price}\n"
            result += f"Rating: {product.rating}/5 ({product.review_count} reviews)\n"
            result += f"Description: {product.description}\n"
            result += f"Features: {', '.join(product.get_features())}\n"
            result += f"Stock: {product.stock} available\n"

            return result

        except Exception as e:
            logger.error(f"Error in get_product_details_tool: {str(e)}")
            return "Error occurred while getting product details."

    def _get_recommendations_tool(self, input_text: str) -> str:
        """Tool function for getting product recommendations"""
        try:
            product = Product.query.get(input_text.strip())

            if product:
                similar_products = self.vector_service.search_similar_products(
                    product.get_search_text(), top_k=4
                )
                similar_ids = [
                    p["id"] for p in similar_products if p["id"] != product.id
                ]
                recommendations = Product.query.filter(
                    Product.id.in_(similar_ids)
                ).all()
            else:
                similar_products = self.vector_service.search_similar_products(
                    input_text, top_k=4
                )
                similar_ids = [p["id"] for p in similar_products]
                recommendations = Product.query.filter(
                    Product.id.in_(similar_ids)
                ).all()

            if not recommendations:
                return "No recommendations found."

            result = "Here are some recommendations:\n"
            for rec in recommendations:
                result += f"- {rec.name} by {rec.brand} - ${rec.price}\n"

            return result

        except Exception as e:
            logger.error(f"Error in get_recommendations_tool: {str(e)}")
            return "Error occurred while getting recommendations."

    def _extract_product_names_from_text(self, text: str) -> list:
        """Extract product names from the message text by matching against all product names in the database."""
        product_names = []
        all_products = Product.query.all()
        for product in all_products:
            if product.name in text:
                product_names.append(product.name)
        return product_names

    def _is_add_to_cart_request(self, text: str) -> bool:
        lowered = (text or "").lower()
        add_keywords = [
            "add to cart",
            "add this",
            "add",
            "ajoute",
            "ajouter",
            "ajout",
            "panier",
            "mettre au panier",
        ]
        return any(keyword in lowered for keyword in add_keywords)

    def _extract_quantity(self, text: str) -> int:
        match = re.search(r"\b(\d{1,2})\b", text or "")
        if not match:
            return 1
        quantity = int(match.group(1))
        return max(1, min(quantity, 20))

    def _find_product_for_cart_action(self, user_message: str) -> Optional[Product]:
        lowered = (user_message or "").lower()

        products = Product.query.filter_by(is_active=True).all()
        products_sorted = sorted(products, key=lambda p: len(p.name), reverse=True)
        for product in products_sorted:
            if product.name.lower() in lowered:
                return product

        # Fallback to semantic match when product name is approximate.
        similar_products = self.vector_service.search_similar_products(user_message, top_k=1)
        if not similar_products:
            return None

        return Product.query.get(similar_products[0]["id"])

    def _handle_cart_action(
        self,
        user_message: str,
        session_id: str,
        user_id: Optional[str],
        cart_session_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if not self._is_add_to_cart_request(user_message):
            return None

        product = self._find_product_for_cart_action(user_message)
        if not product:
            return {
                "message": "I could not identify which product to add. Please use the Add to Cart button on a product card or provide the exact product name.",
                "product_ids": [],
                "metadata": {
                    "source": "cart_action",
                    "confidence": 1.0,
                    "matched_category": "cart",
                    "matched_intent": "add_to_cart",
                    "required_data": ["exact_product_name"],
                },
            }

        quantity = self._extract_quantity(user_message)
        cart = CartService.get_or_create_cart(
            user_id=user_id,
            session_id=cart_session_id or session_id,
        )
        CartService.add_item(
            cart_id=cart.id,
            product_id=product.id,
            quantity=quantity,
            unit_price=product.price,
        )

        return {
            "message": f"Added {quantity} x {product.name} to your cart.",
            "product_ids": [product.id],
            "metadata": {
                "source": "cart_action",
                "confidence": 1.0,
                "matched_category": "cart",
                "matched_intent": "add_to_cart",
                "required_data": [],
            },
        }

    def process_message(
        self,
        session_id: str,
        user_message: str,
        user_id: str = None,
        cart_session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process user message and generate AI response"""
        if not self.initialized:
            self.initialize()

        try:
            chat_session = ChatSession.query.get(session_id)
            if not chat_session:
                chat_session = ChatSession(id=session_id, user_id=user_id)
                from app import db

                db.session.add(chat_session)
                db.session.commit()

            user_msg = Message(
                id=str(uuid.uuid4()),
                chat_session_id=session_id,
                content=user_message,
                is_bot=False,
            )
            from app import db

            db.session.add(user_msg)

            memory = self.get_or_create_memory(session_id)
            chat_history = []
            if hasattr(memory, "buffer"):
                for msg in memory.buffer:
                    if hasattr(msg, "content"):
                        chat_history.append(msg.content)
                    elif isinstance(msg, str):
                        chat_history.append(msg)

            support_context = self.support_agent_service.get_support_context(
                user_message, top_k=3
            )
            detected_order_number = self.support_agent_service.extract_order_number(
                user_message
            )

            system_prompt = """You are Storey, an AI shopping assistant for an electronics e-commerce store.
            You help customers with customer support and product assistance in a professional and friendly tone.

            Guidelines:
            - Prioritize support topics in this order: order tracking, delivery, payment, returns.
            - Keep responses concise, actionable, and customer-service oriented.
            - If data is missing, clearly ask for required fields (order number, email, shipping info, etc.).
            - Never invent policy, order status, or billing outcomes.
            - For out-of-domain topics, politely redirect to e-commerce support scope.
            - For product help, provide specific and practical recommendations.
            - When customer wants to place an order, guide them: ask for email, confirm product IDs and quantities, then confirm with the order endpoint.
            - Never claim that an item was added to cart unless the backend actually performed the add action.
            - If you are not sure a cart action happened, ask the user to use the Add to Cart button.

            Available tools:
            - search_products: Find products using semantic search. Input: search query (str).
            - filter_products: Filter products. Input: JSON string with keys: category, subcategory, brand, min_price, max_price, min_rating, in_stock_only, features (list), search_query, limit.
            - get_product_details: Get product details. Input: product ID (str).
            - get_recommendations: Get recommendations. Input: product ID (str) or preference description (str).
            """

            if support_context:
                system_prompt += (
                    "\n\nCustomer support playbook context (prioritize this when relevant):\n"
                    + support_context
                )

            # Initialize metadata tracking
            response_metadata = {
                "source": "llm",  # llm, order_tracking, or direct_support
                "confidence": 0.0,
                "matched_category": None,
                "matched_intent": None,
                "required_data": [],
            }

            direct_support_result = self.support_agent_service.get_direct_support_answer_with_metadata(
                user_message
            )
            direct_support_answer = direct_support_result.get("answer")
            support_meets_threshold = direct_support_result.get("meets_threshold", False)
            allow_llm_for_support = current_app.config.get(
                "ALLOW_LLM_FOR_SUPPORT_QUERIES", True
            )

            direct_order_answer = None
            if detected_order_number:
                direct_order_answer = self.support_agent_service.build_order_tracking_answer(
                    detected_order_number
                )

            cart_action = self._handle_cart_action(
                user_message=user_message,
                session_id=session_id,
                user_id=user_id,
                cart_session_id=cart_session_id,
            )

            if cart_action:
                message_text = cart_action["message"]
                product_ids = cart_action["product_ids"]
                response_metadata = cart_action["metadata"]
            elif direct_order_answer:
                message_text = direct_order_answer
                product_ids = []
                response_metadata["source"] = "order_tracking"
                response_metadata["confidence"] = 1.0
                response_metadata["matched_category"] = "Commandes et suivi"
            elif direct_support_answer and support_meets_threshold:
                # Non-hallucination policy: only use KB answer if meets threshold
                message_text = direct_support_answer
                product_ids = []
                response_metadata["source"] = direct_support_result.get("source", "direct_support")
                response_metadata["confidence"] = direct_support_result.get("confidence", 0.0)
                response_metadata["matched_category"] = direct_support_result.get("category")
                response_metadata["matched_intent"] = direct_support_result.get("intent")
                response_metadata["required_data"] = direct_support_result.get("required_data", [])
            else:
                response_metadata["matched_category"] = direct_support_result.get("category")
                response_metadata["matched_intent"] = direct_support_result.get("intent")
                response_metadata["required_data"] = direct_support_result.get("required_data", [])

                if not allow_llm_for_support and direct_support_result.get("category"):
                    needed = direct_support_result.get("required_data", [])
                    needed_text = (
                        ", ".join(needed) if needed else "les informations de votre dossier"
                    )
                    message_text = (
                        "Je ne peux pas fournir de reponse non verifiee sur ce sujet pour le moment. "
                        f"Merci de partager {needed_text} afin que je vous aide correctement."
                    )
                    product_ids = []
                    response_metadata["source"] = "guardrail"
                    response_metadata["confidence"] = direct_support_result.get("confidence", 0.0)
                else:
                # KB answer below threshold or not matched - use LLM with support context
                    messages = [SystemMessage(content=system_prompt)]
                    if chat_history:
                        messages.append(SystemMessage(content="Conversation history:\n" + "\n".join(chat_history)))
                    messages.append(HumanMessage(content=user_message))

                    ai_message = self.llm.invoke(messages)
                    message_text = getattr(ai_message, "content", str(ai_message))
                    product_ids = self._extract_product_ids_from_response(message_text)
                    response_metadata["source"] = "llm"
                    response_metadata["confidence"] = 0.0  # LLM responses have no explicit score

            if direct_support_result.get("matched_question"):
                response_metadata["matched_question"] = direct_support_result.get(
                    "matched_question"
                )

            memory.buffer.append(HumanMessage(content=user_message))
            memory.buffer.append(AIMessage(content=message_text))

            if not product_ids:
                product_names = self._extract_product_names_from_text(message_text)
                if product_names:
                    product_ids = [
                        p.id
                        for p in Product.query.filter(
                            Product.name.in_(product_names)
                        ).all()
                    ]

            ai_msg = Message(
                id=str(uuid.uuid4()),
                chat_session_id=session_id,
                content=message_text,
                is_bot=True,
                message_type="product" if product_ids else "text",
                products=product_ids,
            )
            db.session.add(ai_msg)
            db.session.commit()

            products = []
            if product_ids:
                products = [
                    Product.query.get(pid).to_dict()
                    for pid in product_ids
                    if Product.query.get(pid)
                ]

            return {
                "id": ai_msg.id,
                "content": message_text,
                "isBot": True,
                "timestamp": ai_msg.created_at.isoformat(),
                "products": products,
                "type": ai_msg.message_type,
                "metadata": response_metadata,
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            error_msg = Message(
                id=str(uuid.uuid4()),
                chat_session_id=session_id,
                content="I'm sorry, I encountered an error. Please try again.",
                is_bot=True,
            )
            from app import db

            db.session.add(error_msg)
            db.session.commit()
            return {
                "id": error_msg.id,
                "content": error_msg.content,
                "isBot": True,
                "timestamp": error_msg.created_at.isoformat(),
                "products": [],
                "type": "text",
            }

    def _extract_product_ids_from_response(self, response: str) -> List[str]:
        """Extract product IDs from AI response (basic implementation)"""

        product_ids = []

        return product_ids

    def get_chat_history(
        self, session_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get chat history for a session"""
        try:
            messages = (
                Message.query.filter_by(chat_session_id=session_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
                .all()
            )

            return [msg.to_dict(include_product_details=True) for msg in messages]

        except Exception as e:
            logger.error(f"Error getting chat history: {str(e)}")
            return []

    def clear_session_memory(self, session_id: str):
        """Clear memory for a specific session"""
        if session_id in self.memory_sessions:
            del self.memory_sessions[session_id]
