from datetime import datetime
from typing import Any, Dict, Optional

from models.cart import Cart
from models.order import Order, OrderItem
from models.user import User
from services.order_service import OrderService


class CheckoutService:
    @staticmethod
    def validate_checkout(cart: Cart, shipping_address: str) -> tuple[bool, str]:
        """Validate cart is ready for checkout"""
        if not cart or len(cart.items) == 0:
            return False, "Cart is empty"
        
        if not shipping_address or len(shipping_address) < 10:
            return False, "Invalid shipping address"
        
        if cart.total <= 0:
            return False, "Invalid cart total"
        
        return True, "Valid"

    @staticmethod
    def process_checkout(
        cart_id: str,
        shipping_address: str,
        shipping_method: str = "standard",
        customer_email: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Order:
        """Convert cart to order and process checkout"""
        from app import db
        
        cart = Cart.query.get(cart_id)
        if not cart:
            raise ValueError("Cart not found")

        # Validate
        is_valid, message = CheckoutService.validate_checkout(cart, shipping_address)
        if not is_valid:
            raise ValueError(message)

        resolved_email = customer_email
        if not resolved_email and (user_id or cart.user_id):
            user = User.query.get(user_id or cart.user_id)
            resolved_email = user.email if user else None

        # Prepare order data
        order_data = {
            "user_id": user_id or cart.user_id,
            "customer_email": resolved_email,
            "shipping_address": shipping_address,
            "shipping_method": shipping_method,
            "carrier": "DHL",
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                }
                for item in cart.items
            ],
        }

        if not order_data.get("customer_email"):
            raise ValueError("customer_email required")

        # Create order from cart
        order = OrderService.create_order(order_data)

        # Mark cart as converted
        cart.status = "converted"
        db.session.commit()

        return order

    @staticmethod
    def calculate_shipping(subtotal: float, shipping_method: str = "standard") -> float:
        """Calculate shipping cost based on method and subtotal"""
        shipping_rates = {
            "standard": 10.0,  # Free over $100
            "express": 25.0,   # 2-day delivery
            "overnight": 50.0, # Next-day delivery
        }
        
        base_rate = shipping_rates.get(shipping_method, 10.0)
        
        # Free shipping over $100
        if subtotal >= 100:
            return 0.0
        
        return base_rate

    @staticmethod
    def get_checkout_summary(cart: Cart) -> Dict[str, Any]:
        """Get full checkout summary with calculated totals"""
        return {
            "cartId": cart.id,
            "itemCount": len(cart.items),
            "subtotal": cart.subtotal,
            "tax": cart.tax,
            "shipping": cart.shipping,
            "discount": cart.discount,
            "total": cart.total,
            "items": [item.to_dict() for item in cart.items],
            "estimatedDelivery": "4-5 business days",
        }
