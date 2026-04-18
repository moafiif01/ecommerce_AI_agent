import json
import uuid
from datetime import datetime

from models import db


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_number = db.Column(db.String(32), unique=True, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    customer_email = db.Column(db.String(120), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, default="processing", index=True)
    shipping_method = db.Column(db.String(60), nullable=False, default="standard")
    carrier = db.Column(db.String(60), nullable=True)
    tracking_number = db.Column(db.String(80), nullable=True)
    shipping_address = db.Column(db.Text, nullable=False)
    estimated_delivery_at = db.Column(db.DateTime, nullable=True)
    shipped_at = db.Column(db.DateTime, nullable=True)
    delivered_at = db.Column(db.DateTime, nullable=True)
    canceled_at = db.Column(db.DateTime, nullable=True)
    cancel_reason = db.Column(db.String(255), nullable=True)
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    shipping_fee = db.Column(db.Float, nullable=False, default=0.0)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    timeline = db.Column(db.Text, nullable=False, default="[]")
    created_at = db.Column(db.DateTime, default=datetime.now())
    updated_at = db.Column(db.DateTime, default=datetime.now(), onupdate=datetime.now())

    items = db.relationship("OrderItem", backref="order", lazy=True, cascade="all, delete-orphan")

    def get_timeline(self):
        try:
            return json.loads(self.timeline or "[]")
        except json.JSONDecodeError:
            return []

    def add_timeline_event(self, status: str, note: str):
        events = self.get_timeline()
        events.append(
            {
                "status": status,
                "note": note,
                "at": datetime.utcnow().isoformat(),
            }
        )
        self.timeline = json.dumps(events)

    def to_dict(self, include_items: bool = True):
        data = {
            "id": self.id,
            "orderNumber": self.order_number,
            "userId": self.user_id,
            "customerEmail": self.customer_email,
            "status": self.status,
            "shippingMethod": self.shipping_method,
            "carrier": self.carrier,
            "trackingNumber": self.tracking_number,
            "shippingAddress": self.shipping_address,
            "estimatedDeliveryAt": self.estimated_delivery_at.isoformat() if self.estimated_delivery_at else None,
            "shippedAt": self.shipped_at.isoformat() if self.shipped_at else None,
            "deliveredAt": self.delivered_at.isoformat() if self.delivered_at else None,
            "canceledAt": self.canceled_at.isoformat() if self.canceled_at else None,
            "cancelReason": self.cancel_reason,
            "subtotal": self.subtotal,
            "shippingFee": self.shipping_fee,
            "totalAmount": self.total_amount,
            "timeline": self.get_timeline(),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }

        if include_items:
            data["items"] = [item.to_dict() for item in self.items]

        return data


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey("orders.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    line_total = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "orderId": self.order_id,
            "productId": self.product_id,
            "productName": self.product_name,
            "unitPrice": self.unit_price,
            "quantity": self.quantity,
            "lineTotal": self.line_total,
        }
