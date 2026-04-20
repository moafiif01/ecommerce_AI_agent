import json
import logging
import re
import uuid
from typing import Any, Dict, List, Optional

from flask import current_app
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from models.chat_session import ChatSession
from models.message import Message
from models.product import Product

from .cart_service import CartService
from .support_agent_service import SupportAgentService
from .vector_service import VectorService
from .rag_service import RAGService

logger = logging.getLogger(__name__)


class SimpleConversationMemory:
    def __init__(self):
        self.buffer = []


class SearchProductsInput(BaseModel):
    query: str = Field(description="Search query string")

class FilterProductsInput(BaseModel):
    filter_json: str = Field(description="JSON string with keys: category, subcategory, brand, min_price, max_price, min_rating, in_stock_only, features, search_query, limit")

class GetProductDetailsInput(BaseModel):
    product_id: str = Field(description="product ID string")

class GetRecommendationsInput(BaseModel):
    input_text: str = Field(description="product ID or preference description string")

class TrackOrderInput(BaseModel):
    order_number: str = Field(description="Order number in ORD-XXXXXXXX format")

class CancelOrderInput(BaseModel):
    order_number: str = Field(description="Order number to cancel in ORD-XXXXXXXX format")
    reason: str = Field(default="Annulation demandee par le client", description="Reason for cancellation")

class AddToCartInput(BaseModel):
    product_id: str = Field(description="Exact database product ID string")
    quantity: int = Field(default=1, description="Quantity to add")


class ChatService:
    """Enhanced chat service with LangChain and Groq integration"""

    def __init__(self):
        self.llm = None
        self.vector_service = VectorService()
        self.support_agent_service = SupportAgentService()
        self.rag_service = RAGService()
        self.memory_sessions = {}
        self.initialized = False

    def initialize(self):
        """Initialize LangChain components"""
        try:
            self.llm = ChatGroq(
                model=current_app.config["GROQ_MODEL"],
                groq_api_key=current_app.config["GROQ_API_KEY"],
                temperature=0.3,
                max_tokens=1500,
            )

            self.vector_service.initialize()
            self.rag_service.initialize(self.vector_service)

            # Auto-index support KB — re-index if namespace is empty or chunk count changed
            try:
                stats = self.vector_service.index.describe_index_stats()
                ns_stats = stats.get("namespaces", {})
                existing_count = ns_stats.get("support-kb", {}).get("vector_count", 0)
                
                # Check expected count from current documents
                expected_chunks = self.rag_service._build_playbook_chunks() + self.rag_service._build_cgv_chunks()
                expected_count = len(expected_chunks)
                
                if existing_count != expected_count:
                    if existing_count > 0:
                        logger.info("Support KB chunk count changed (%d -> %d), re-indexing...", existing_count, expected_count)
                        self.vector_service.index.delete(delete_all=True, namespace="support-kb")
                    else:
                        logger.info("Support KB namespace empty, indexing documents...")
                    count = self.rag_service.index_all_documents()
                    logger.info("Indexed %d support KB chunks", count)
                else:
                    logger.info("Support KB already indexed (%d chunks), skipping", existing_count)
            except Exception as e:
                logger.warning("Could not auto-index support KB: %s", str(e))

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

    def create_tools(self, session_id: str = None, user_id: str = None, cart_session_id: str = None) -> List[StructuredTool]:
        """Create tools for the LangChain agent"""
        
        def _add_to_cart_tool(product_id: str, quantity: int = 1) -> str:
            """Tool function to add an item to the shopping cart."""
            from models.product import Product
            product = Product.query.get(product_id)
            if not product:
                return json.dumps({"message": f"Produit avec l'ID {product_id} introuvable.", "product_ids": []})
            
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
            return json.dumps({
                "message": f"Ajouté {quantity} x {product.name} au panier avec succès.", 
                "product_ids": [product.id]
            })

        tools = [
            StructuredTool.from_function(
                name="search_products",
                description="Find products using semantic search.",
                func=self._search_products_tool,
                args_schema=SearchProductsInput
            ),
            StructuredTool.from_function(
                name="filter_products",
                description="Filter products by constraints.",
                func=self._filter_products_tool,
                args_schema=FilterProductsInput
            ),
            StructuredTool.from_function(
                name="get_product_details",
                description="Get absolute details containing stock.",
                func=self._get_product_details_tool,
                args_schema=GetProductDetailsInput
            ),
            StructuredTool.from_function(
                name="get_recommendations",
                description="Get similar product recommendations.",
                func=self._get_recommendations_tool,
                args_schema=GetRecommendationsInput
            ),
            StructuredTool.from_function(
                name="track_order",
                description="Track an order by its order number (format ORD-XXXXXXXX). Returns order status, carrier, tracking number, items, and estimated delivery.",
                func=self._track_order_tool,
                args_schema=TrackOrderInput
            ),
            StructuredTool.from_function(
                name="cancel_order",
                description="Cancel an order that has not been shipped yet.",
                func=self._cancel_order_tool,
                args_schema=CancelOrderInput
            ),
            StructuredTool.from_function(
                name="add_to_cart",
                description="Add a specific product to the user's shopping cart using its ID.",
                func=_add_to_cart_tool,
                args_schema=AddToCartInput
            ),
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
                        "message": "No products found for the given query. The store does not carry this type of item.",
                        "product_ids": [],
                    }
                )

            product_ids = [p["id"] for p in similar_products]
            products = Product.query.filter(Product.id.in_(product_ids)).all()

            result = "Found the following products:\n"
            for product in products:
                features = product.get_features()
                features_str = ', '.join(features[:5]) if features else 'N/A'
                stock_status = f"{product.stock} in stock" if product.stock > 0 else "OUT OF STOCK"
                result += f"- [ID: {product.id}] {product.name} by {product.brand} - ${product.price} ({stock_status})\n"
                result += f"  Category: {product.category}/{product.subcategory}\n"
                result += f"  Rating: {product.rating}/5 ({product.review_count} reviews)\n"
                result += f"  Key features: {features_str}\n"
                result += f"  {product.description[:150]}\n"

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
            # Only pass known kwargs to prevent crashes from LLM-invented keys
            allowed_keys = {'category', 'subcategory', 'brand', 'min_price', 'max_price',
                            'min_rating', 'in_stock_only', 'search_query', 'limit'}
            safe_filters = {k: v for k, v in filters.items() if k in allowed_keys}
            products = Product.search_by_filters(**safe_filters)

            if not products:
                return json.dumps(
                    {
                        "message": "No products found matching the specified filters.",
                        "product_ids": [],
                    }
                )

            result = f"Found {len(products)} products matching your criteria:\n"
            for product in products[:5]:
                features = product.get_features()
                features_str = ', '.join(features[:5]) if features else 'N/A'
                stock_status = f"{product.stock} in stock" if product.stock > 0 else "OUT OF STOCK"
                result += f"- [ID: {product.id}] {product.name} by {product.brand} - ${product.price} ({stock_status})\n"
                result += f"  Key features: {features_str}\n"

            product_ids = [product.id for product in products[:5]]
            return json.dumps({"message": result, "product_ids": product_ids})

        except json.JSONDecodeError:
            return json.dumps({"message": "Invalid filter format. Please provide valid JSON.", "product_ids": []})
        except Exception as e:
            logger.error(f"Error in filter_products_tool: {str(e)}")
            return json.dumps(
                {
                    "message": "Error occurred while filtering products.",
                    "product_ids": [],
                }
            )

    def _get_product_details_tool(self, product_id: str) -> str:
        """Tool function for getting product details. Accepts a product ID or product name."""
        try:
            cleaned = product_id.strip()
            product = Product.query.get(cleaned)
            
            # Fallback: try matching by name if ID lookup fails
            if not product:
                product = Product.query.filter(
                    Product.name.ilike(f"%{cleaned}%")
                ).first()
            
            if not product:
                return json.dumps({
                    "message": f"Product '{cleaned}' was NOT FOUND in the database. Do NOT invent details. Tell the user this product is not available.",
                    "product_ids": []
                })

            result = "Product Details:\n"
            result += f"ID: {product.id}\n"
            result += f"Name: {product.name}\n"
            result += f"Brand: {product.brand}\n"
            result += f"Price: ${product.price}\n"
            result += f"Rating: {product.rating}/5 ({product.review_count} reviews)\n"
            result += f"Description: {product.description}\n"
            result += f"Features: {', '.join(product.get_features())}\n"
            result += f"Stock: {product.stock} available\n"

            return json.dumps({"message": result, "product_ids": [product.id]})

        except Exception as e:
            logger.error(f"Error in get_product_details_tool: {str(e)}")
            return json.dumps({"message": "Error occurred while getting product details.", "product_ids": []})

    def _get_recommendations_tool(self, input_text: str) -> str:
        """Tool function for getting product recommendations. Accepts product ID or name."""
        try:
            cleaned = input_text.strip()
            product = Product.query.get(cleaned)
            
            # Fallback: try matching by name
            if not product:
                product = Product.query.filter(
                    Product.name.ilike(f"%{cleaned}%")
                ).first()

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
                    cleaned, top_k=4
                )
                similar_ids = [p["id"] for p in similar_products]
                recommendations = Product.query.filter(
                    Product.id.in_(similar_ids)
                ).all()

            if not recommendations:
                return json.dumps({"message": "No recommendations found.", "product_ids": []})

            result = "Here are some recommendations:\n"
            for rec in recommendations:
                features = rec.get_features()
                features_str = ', '.join(features[:3]) if features else 'N/A'
                result += f"- [ID: {rec.id}] {rec.name} by {rec.brand} - ${rec.price}\n"
                result += f"  Key features: {features_str}\n"

            return json.dumps({"message": result, "product_ids": [rec.id for rec in recommendations]})

        except Exception as e:
            logger.error(f"Error in get_recommendations_tool: {str(e)}")
            return json.dumps({"message": "Error occurred while getting recommendations.", "product_ids": []})

    def _track_order_tool(self, order_number: str) -> str:
        """Tool function for tracking an order by its number."""
        try:
            from .order_service import OrderService
            cleaned = order_number.strip().upper()
            if cleaned.isdigit():
                cleaned = f"ORD-{cleaned}"
            order = OrderService.get_order_by_number(cleaned)

            if not order:
                return json.dumps({
                    "message": f"Commande '{cleaned}' introuvable dans notre systeme. Verifiez le numero (format ORD-XXXXXXXX).",
                    "product_ids": []
                })

            payload = order.to_dict(include_items=True)
            result = f"Commande {payload['orderNumber']}\n"
            result += f"Statut: {payload['status']}\n"
            result += f"Transporteur: {payload.get('carrier') or 'non assigne'}\n"
            result += f"Numero de suivi: {payload.get('trackingNumber') or 'non disponible'}\n"
            result += f"Livraison estimee: {payload.get('estimatedDeliveryAt') or 'non disponible'}\n"
            result += f"Email client: {payload.get('customerEmail', 'N/A')}\n"
            result += f"Adresse: {payload.get('shippingAddress', 'N/A')}\n"
            result += f"Montant total: {payload.get('totalAmount', 0)}€\n"
            result += "Articles:\n"
            for item in payload.get("items", []):
                result += f"- {item['productName']} x{item['quantity']} ({item['lineTotal']}€)\n"

            return json.dumps({"message": result, "product_ids": []})

        except Exception as e:
            logger.error(f"Error in track_order_tool: {str(e)}")
            return json.dumps({"message": "Erreur lors du suivi de commande.", "product_ids": []})

    def _cancel_order_tool(self, order_number: str, reason: str = "Annulation demandee par le client") -> str:
        """Tool function for cancelling an order."""
        try:
            from .order_service import OrderService
            cleaned = order_number.strip().upper()
            if cleaned.isdigit():
                cleaned = f"ORD-{cleaned}"
            order = OrderService.get_order_by_number(cleaned)

            if not order:
                return json.dumps({
                    "message": f"Commande '{cleaned}' introuvable. Impossible de proceder a l'annulation.",
                    "product_ids": []
                })

            try:
                OrderService.cancel_order(order, reason)
                return json.dumps({
                    "message": f"La commande {cleaned} a ete annulee avec succes. Le remboursement sera effectue sous 5 a 10 jours ouvrables.",
                    "product_ids": []
                })
            except ValueError as ve:
                return json.dumps({
                    "message": f"Impossible d'annuler la commande {cleaned}: {str(ve)}. La commande a deja ete expediee.",
                    "product_ids": []
                })

        except Exception as e:
            logger.error(f"Error in cancel_order_tool: {str(e)}")
            return json.dumps({"message": "Erreur lors de l'annulation.", "product_ids": []})

    def _extract_product_names_from_text(self, text: str) -> list:
        """Extract product names from the message text by matching against all product names in the database."""
        product_names = []
        all_products = Product.query.all()
        for product in all_products:
            if product.name in text:
                product_names.append(product.name)
        return product_names


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

            system_prompt = """Tu es Storey, l'assistant shopping IA de S-TORE, une boutique en ligne d'electronique.
Tu aides les clients avec le support client et l'assistance produit dans un ton professionnel, empathique et oriente solution.
Tu reponds dans la langue du client (francais par defaut, anglais si le client ecrit en anglais).

Regles et contraintes anti-hallucination :

[GENERAL]
- Sois concis, actionnable et oriente service client.
- Pour les sujets hors domaine, redirige poliment vers le perimetre du support e-commerce.
- N'affiche JAMAIS de syntaxe brute d'appel de fonction, de JSON ou de texte d'invocation d'outil. Tes reponses doivent etre en langage naturel uniquement.

[INVENTAIRE & SPECS]
- N'invente JAMAIS la disponibilite, les noms, les prix ou les specs des produits.
- Base-toi EXCLUSIVEMENT sur les donnees retournees par les outils. Si un outil retourne "non trouve", dis au client que le produit n'est pas disponible.
- Quand tu presentes des produits, mentionne leurs specs cles, prix, disponibilite et pourquoi ils correspondent a la demande.

[COMMANDES & SUIVI]
- N'invente JAMAIS un statut de commande, un lieu d'expedition ou une date de livraison.
- Utilise TOUJOURS l'outil track_order pour verifier le statut d'une commande. Ne reponds jamais sans avoir consulte l'outil.

[POLITIQUES & CGV]
- Base-toi sur le CONTEXTE DOCUMENTAIRE fourni ci-dessous pour repondre aux questions sur les politiques de retour, livraison, paiement et remboursement.
- Si l'information n'est pas dans le contexte, dis que tu n'as pas cette information specifique et suggere de contacter le service client.

[CAPACITES]
- Ne pretends JAMAIS effectuer des actions pour lesquelles tu n'as pas d'outil. Tu ne peux PAS appliquer de codes promo, traiter des paiements, gerer des listes de souhaits ou contacter le support humain directement.

[FORMAT DE REPONSE]
- Ton message ne doit JAMAIS etre vide. Quand tu presentes des produits, ecris un resume conversationnel avec les specs cles, le prix et pourquoi chaque produit correspond au besoin.
- CRITIQUE : A la fin de ton message, ajoute les IDs des produits que tu recommandes dans ce format exact : [RECOMMENDED_IDS: id1, id2, id3]. N'inclus QUE les IDs des produits PERTINENTS pour la demande du client.
- Si un outil a retourne des produits mais AUCUN n'est pertinent, n'inclus aucun ID et dis au client que tu n'as pas de produits correspondants.

[ACTIONS PANIER]
- Si le client demande d'ajouter un article au panier, et que tu as pu identifier de quel article il s'agit de facon non ambigue, utilise OBLIGATOIREMENT l'outil add_to_cart avec son ID.
- Si la demande n'est pas claire, demande des precisions avant. Ne pretends jamais avoir ajoute un article si tu n'as pas appele l'outil.
"""

            # Inject RAG context from FAQ + CGV
            rag_chunks = self.rag_service.retrieve_context(user_message, top_k=4, min_score=0.3)
            rag_context = self.rag_service.format_context_for_prompt(rag_chunks)
            if rag_context:
                system_prompt += "\n\n" + rag_context

            if support_context:
                system_prompt += (
                    "\n\nContexte additionnel du playbook support (a prioriser si pertinent) :\n"
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

            # Check if guardrail triggered (e.g. out of domain)
            if direct_support_result.get("source") == "guardrail":
                message_text = direct_support_result.get("answer")
                product_ids = []
                response_metadata["source"] = "guardrail"
                response_metadata["confidence"] = direct_support_result.get("confidence", 1.0)
                response_metadata["matched_category"] = direct_support_result.get("category")
                response_metadata["matched_intent"] = direct_support_result.get("intent")
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
                    chat_history_msgs = [msg for msg in memory.buffer if isinstance(msg, (HumanMessage, AIMessage, SystemMessage))]
                    
                    tools = self.create_tools(session_id=session_id, user_id=user_id, cart_session_id=cart_session_id)
                    prompt = ChatPromptTemplate.from_messages([
                        ("system", system_prompt),
                        MessagesPlaceholder(variable_name="chat_history"),
                        ("human", "{input}")
                    ])
                    chain = prompt | self.llm.bind_tools(tools)
                    
                    ai_message = chain.invoke({
                        "input": user_message,
                        "chat_history": chat_history_msgs
                    })
                    
                    product_ids = []
                    all_tool_product_ids = []  # Fallback: collect IDs from all tool outputs
                    
                    if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
                        messages = prompt.invoke({"input": user_message, "chat_history": chat_history_msgs}).to_messages()
                        messages.append(ai_message)
                        for tool_call in ai_message.tool_calls:
                            selected_tool = next((t for t in tools if t.name == tool_call["name"]), None)
                            if selected_tool:
                                try:
                                    tool_output = selected_tool.invoke(tool_call["args"])
                                    # Collect IDs from tool output as fallback
                                    try:
                                        obs_dict = json.loads(tool_output)
                                        if "product_ids" in obs_dict:
                                            all_tool_product_ids.extend(obs_dict["product_ids"])
                                    except:
                                        pass
                                    messages.append(ToolMessage(
                                        tool_call_id=tool_call["id"],
                                        content=str(tool_output),
                                        name=tool_call["name"]
                                    ))
                                except Exception as e:
                                    messages.append(ToolMessage(
                                        tool_call_id=tool_call["id"],
                                        content=json.dumps({"message": f"Error: {str(e)}", "product_ids": []}),
                                        name=tool_call["name"]
                                    ))
                        
                        final_ai_message = self.llm.bind_tools(tools).invoke(messages)
                        message_text = final_ai_message.content
                    else:
                        message_text = ai_message.content
                    
                    # Clean raw function-call artifacts from message text
                    message_text = re.sub(r'</?function[^>]*>', '', message_text)
                    message_text = re.sub(r'\{"name"\s*:\s*"\w+".*?\}', '', message_text)
                    message_text = re.sub(r'\s{2,}', ' ', message_text).strip()
                        
                    # Extract LLM-endorsed IDs; fall back to tool output IDs
                    rendered_ids_match = re.search(r'\[RECOMMENDED_IDS:\s*(.*?)\]', message_text)
                    if rendered_ids_match:
                        ids_raw = rendered_ids_match.group(1)
                        product_ids = [pid.strip() for pid in ids_raw.split(',') if pid.strip() and pid.strip() != 'None']
                        message_text = re.sub(r'\[RECOMMENDED_IDS:.*?\]', '', message_text).strip()
                    elif all_tool_product_ids:
                        # LLM didn't emit the tag; use tool-returned IDs as fallback
                        product_ids = all_tool_product_ids
                        
                    product_ids = list(dict.fromkeys(product_ids)) # Remove duplicates
                    
                    response_metadata["source"] = "llm"
                    response_metadata["confidence"] = 0.0  # LLM responses have no explicit score

            if direct_support_result.get("matched_question"):
                response_metadata["matched_question"] = direct_support_result.get(
                    "matched_question"
                )

            memory.buffer.append(HumanMessage(content=user_message))
            memory.buffer.append(AIMessage(content=message_text))

            # Cap memory buffer to prevent context window overflow
            max_memory = 20
            if len(memory.buffer) > max_memory:
                memory.buffer = memory.buffer[-max_memory:]

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
                for pid in product_ids:
                    if pid:
                        p = Product.query.get(pid)
                        if p:
                            products.append(p.to_dict())

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
