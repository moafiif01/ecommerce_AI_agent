from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from services.cart_service import CartService

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("", methods=["GET"])
def get_cart():
    """Get user's active cart or create one"""
    try:
        user_id = None
        session_id = request.args.get("session_id")
        
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass

        if not user_id and not session_id:
            session_id = request.args.get("session_id") or request.headers.get("X-Session-ID")
            if not session_id:
                return jsonify({"success": False, "message": "session_id required"}), 400

        cart = CartService.get_or_create_cart(user_id=user_id, session_id=session_id)
        return jsonify({"success": True, "cart": cart.to_dict()}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@cart_bp.route("", methods=["POST"])
def create_cart():
    """Create new cart"""
    try:
        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass

        session_id = request.args.get("session_id")
        cart = CartService.get_or_create_cart(user_id=user_id, session_id=session_id)
        return jsonify({"success": True, "cart": cart.to_dict()}), 201

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400


@cart_bp.route("/<cart_id>/items", methods=["POST"])
def add_to_cart(cart_id):
    """Add item to cart"""
    try:
        data = request.get_json() or {}
        product_id = data.get("product_id")
        quantity = int(data.get("quantity", 1))

        if not product_id:
            return jsonify({"success": False, "message": "product_id required"}), 400

        item = CartService.add_item(
            cart_id=cart_id,
            product_id=product_id,
            quantity=quantity,
            unit_price=data.get("unit_price"),
        )
        cart = item.cart
        return jsonify({"success": True, "cart": cart.to_dict(), "item": item.to_dict()}), 201

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


@cart_bp.route("/<cart_id>/items/<item_id>", methods=["PUT"])
def update_cart_item(cart_id, item_id):
    """Update item quantity"""
    try:
        data = request.get_json() or {}
        quantity = int(data.get("quantity", 1))

        item = CartService.update_item_quantity(cart_id, item_id, quantity)
        cart = item.cart
        return jsonify({"success": True, "cart": cart.to_dict(), "item": item.to_dict()}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@cart_bp.route("/<cart_id>/items/<item_id>", methods=["DELETE"])
def remove_from_cart(cart_id, item_id):
    """Remove item from cart"""
    try:
        cart = CartService.remove_item(cart_id, item_id)
        return jsonify({"success": True, "cart": cart.to_dict()}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@cart_bp.route("/<cart_id>/clear", methods=["POST"])
def clear_cart(cart_id):
    """Clear all items from cart"""
    try:
        cart = CartService.clear_cart(cart_id)
        return jsonify({"success": True, "message": "Cart cleared", "cart": cart.to_dict()}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@cart_bp.route("/<cart_id>/discount", methods=["POST"])
def apply_discount(cart_id):
    """Apply discount to cart"""
    try:
        data = request.get_json() or {}
        discount = float(data.get("discount", 0))

        cart = CartService.apply_discount(cart_id, discount)
        return jsonify({"success": True, "cart": cart.to_dict()}), 200

    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
