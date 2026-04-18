import json
import uuid
from datetime import datetime

from models import db


class Cart(db.Model):
    __tablename__ = "carts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, index=True)
    session_id = db.Column(db.String(100), nullable=True, index=True)  # For guest carts
    status = db.Column(db.String(20), nullable=False, default="active")  # active, abandoned, converted
    subtotal = db.Column(db.Float, nullable=False, default=0.0)
    tax = db.Column(db.Float, nullable=False, default=0.0)
    shipping = db.Column(db.Float, nullable=False, default=0.0)
    discount = db.Column(db.Float, nullable=False, default=0.0)
    total = db.Column(db.Float, nullable=False, default=0.0)
    metadata_json = db.Column(db.Text, nullable=False, default="{}")  # Custom fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    abandoned_at = db.Column(db.DateTime, nullable=True)

    items = db.relationship("CartItem", backref="cart", lazy=True, cascade="all, delete-orphan")

    def get_metadata(self):
        try:
            return json.loads(self.metadata_json or "{}")
        except json.JSONDecodeError:
            return {}

    def set_metadata(self, data: dict):
        self.metadata_json = json.dumps(data)

    def recalculate_totals(self):
        """Recalculate cart totals from items"""
        self.subtotal = sum(item.line_total for item in self.items)
        # Tax: 8% on subtotal
        self.tax = round(self.subtotal * 0.08, 2)
        # Shipping: free over $100, else $10
        self.shipping = 0.0 if self.subtotal >= 100 else 10.0
        # Discount: stored separately
        self.total = round(self.subtotal + self.tax + self.shipping - self.discount, 2)

    def to_dict(self, include_items: bool = True):
        data = {
            "id": self.id,
            "userId": self.user_id,
            "sessionId": self.session_id,
            "status": self.status,
            "subtotal": self.subtotal,
            "tax": self.tax,
            "shipping": self.shipping,
            "discount": self.discount,
            "total": self.total,
            "itemCount": len(self.items),
            "createdAt": self.created_at.isoformat(),
            "updatedAt": self.updated_at.isoformat(),
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class CartItem(db.Model):
    __tablename__ = "cart_items"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    cart_id = db.Column(db.String(36), db.ForeignKey("carts.id"), nullable=False, index=True)
    product_id = db.Column(db.String(36), db.ForeignKey("products.id"), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    line_total = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = db.relationship("Product", backref="cart_items")

    def to_dict(self):
        return {
            "id": self.id,
            "cartId": self.cart_id,
            "productId": self.product_id,
            "productName": self.product_name,
            "unitPrice": self.unit_price,
            "quantity": self.quantity,
            "lineTotal": self.line_total,
            "createdAt": self.created_at.isoformat(),
        }
