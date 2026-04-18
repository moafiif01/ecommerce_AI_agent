from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from models.order import Order
from services.order_service import OrderService

order_bp = Blueprint("orders", __name__)


@order_bp.route("/", methods=["POST"])
def create_order():
    try:
        data = request.get_json() or {}

        user_id = None
        try:
            verify_jwt_in_request(optional=True)
            user_id = get_jwt_identity()
        except Exception:
            pass

        data["user_id"] = user_id or data.get("user_id")
        order = OrderService.create_order(data)
        return jsonify({"success": True, "order": order.to_dict()}), 201
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Failed to create order"}), 500


@order_bp.route("/track", methods=["GET"])
def track_order():
    order_number = request.args.get("order_number")
    customer_email = request.args.get("email")

    if not order_number:
        return jsonify({"success": False, "message": "order_number is required"}), 400

    order = OrderService.get_order_by_number(order_number, customer_email)
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404

    return jsonify({"success": True, "order": order.to_dict()}), 200


@order_bp.route("/", methods=["GET"])
def list_orders():
    customer_email = request.args.get("email")
    limit = request.args.get("limit", 20, type=int)

    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass

    orders = OrderService.list_orders(user_id=user_id, customer_email=customer_email, limit=limit)
    return jsonify({"success": True, "count": len(orders), "orders": [o.to_dict() for o in orders]}), 200


@order_bp.route("/<order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404

    return jsonify({"success": True, "order": order.to_dict()}), 200


@order_bp.route("/<order_id>/cancel", methods=["POST"])
def cancel_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "message": "Order not found"}), 404

    reason = (request.get_json() or {}).get("reason", "Canceled by customer")

    try:
        updated = OrderService.cancel_order(order, reason=reason)
        return jsonify({"success": True, "order": updated.to_dict()}), 200
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Failed to cancel order"}), 500
