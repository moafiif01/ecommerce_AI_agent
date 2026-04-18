from flask import Blueprint, request, jsonify
from functools import wraps

from models.cart import Cart
from services.cart_service import CartService
from services.checkout_service import CheckoutService
from services.order_service import OrderService


checkout_bp = Blueprint("checkout", __name__)


def get_cart_or_error(f):
    """Decorator to get cart from request and validate"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        cart_id = data.get("cartId")
        
        if not cart_id:
            return jsonify({"success": False, "message": "cartId required"}), 400
        
        cart = Cart.query.get(cart_id)
        if not cart:
            return jsonify({"success": False, "message": "Cart not found"}), 404
        
        return f(cart, *args, **kwargs)
    return decorated_function


@checkout_bp.route("/checkout/summary", methods=["POST"])
@get_cart_or_error
def get_checkout_summary(cart):
    """Get checkout summary with totals"""
    try:
        summary = CheckoutService.get_checkout_summary(cart)
        return jsonify({"success": True, "summary": summary}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@checkout_bp.route("/checkout/shipping", methods=["POST"])
def calculate_shipping():
    """Calculate shipping cost for given method"""
    try:
        data = request.get_json()
        subtotal = data.get("subtotal", 0)
        method = data.get("method", "standard")
        
        if subtotal < 0:
            return jsonify({"success": False, "message": "Invalid subtotal"}), 400
        
        shipping_cost = CheckoutService.calculate_shipping(subtotal, method)
        
        return jsonify({
            "success": True,
            "shipping": shipping_cost,
            "method": method,
            "estimatedDays": {
                "standard": "4-5 business days",
                "express": "2 business days",
                "overnight": "Next business day"
            }.get(method, "Unknown")
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@checkout_bp.route("/checkout/validate", methods=["POST"])
@get_cart_or_error
def validate_checkout(cart):
    """Validate cart is ready for checkout"""
    try:
        data = request.get_json()
        shipping_address = data.get("shippingAddress", "")
        
        is_valid, message = CheckoutService.validate_checkout(cart, shipping_address)
        
        return jsonify({
            "success": is_valid,
            "valid": is_valid,
            "message": message
        }), 200 if is_valid else 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@checkout_bp.route("/checkout/process", methods=["POST"])
def process_checkout():
    """Process checkout: convert cart to order"""
    try:
        data = request.get_json()
        cart_id = data.get("cartId")
        shipping_address = data.get("shippingAddress")
        shipping_method = data.get("shippingMethod", "standard")
        customer_email = data.get("customerEmail")
        user_id = data.get("userId")
        
        if not cart_id:
            return jsonify({"success": False, "message": "cartId required"}), 400
        
        # Get cart for validation
        cart = Cart.query.get(cart_id)
        if not cart:
            return jsonify({"success": False, "message": "Cart not found"}), 404
        
        # Process checkout
        order = CheckoutService.process_checkout(
            cart_id=cart_id,
            shipping_address=shipping_address,
            shipping_method=shipping_method,
            customer_email=customer_email,
            user_id=user_id or cart.user_id,
        )
        
        return jsonify({
            "success": True,
            "message": "Order created successfully",
            "order": {
                "id": order.id,
                "status": order.status,
                "total": order.total_amount,
                "itemCount": len(order.items),
                "createdAt": order.created_at.isoformat(),
            }
        }), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@checkout_bp.route("/checkout/methods", methods=["GET"])
def get_shipping_methods():
    """Get available shipping methods and costs"""
    subtotal = request.args.get("subtotal", 0, type=float)
    
    methods = [
        {
            "id": "standard",
            "name": "Standard Delivery",
            "days": "4-5 business days",
            "cost": CheckoutService.calculate_shipping(subtotal, "standard"),
        },
        {
            "id": "express",
            "name": "Express Delivery",
            "days": "2 business days",
            "cost": CheckoutService.calculate_shipping(subtotal, "express"),
        },
        {
            "id": "overnight",
            "name": "Overnight Delivery",
            "days": "Next business day",
            "cost": CheckoutService.calculate_shipping(subtotal, "overnight"),
        },
    ]
    
    return jsonify({
        "success": True,
        "methods": methods,
        "note": "Free shipping on orders over $100"
    }), 200
