import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from models.order import Order, OrderItem
from models.product import Product


class OrderService:
    @staticmethod
    def _generate_order_number() -> str:
        suffix = "".join(random.choices(string.digits, k=8))
        return f"ORD-{suffix}"

    @staticmethod
    def create_order(order_data: Dict[str, Any]) -> Order:
        from app import db

        customer_email = order_data.get("customer_email")
        shipping_address = order_data.get("shipping_address")
        items_payload = order_data.get("items", [])

        if not customer_email:
            raise ValueError("customer_email is required")
        if not shipping_address:
            raise ValueError("shipping_address is required")
        if not items_payload:
            raise ValueError("At least one item is required")

        order = Order(
            order_number=OrderService._generate_order_number(),
            user_id=order_data.get("user_id"),
            customer_email=customer_email,
            status="processing",
            shipping_method=order_data.get("shipping_method", "standard"),
            carrier=order_data.get("carrier", "DHL"),
            shipping_address=shipping_address,
            estimated_delivery_at=datetime.utcnow() + timedelta(days=4),
            shipping_fee=float(order_data.get("shipping_fee", 0.0)),
        )

        subtotal = 0.0
        for item_payload in items_payload:
            product_id = item_payload.get("product_id")
            quantity = int(item_payload.get("quantity", 1))

            product = Product.query.get(product_id)
            if not product:
                raise ValueError(f"Product not found: {product_id}")

            line_total = float(product.price) * quantity
            subtotal += line_total

            order.items.append(
                OrderItem(
                    product_id=product.id,
                    product_name=product.name,
                    unit_price=float(product.price),
                    quantity=quantity,
                    line_total=line_total,
                )
            )

        order.subtotal = subtotal
        order.total_amount = subtotal + order.shipping_fee
        order.add_timeline_event("processing", "Order created")

        db.session.add(order)
        db.session.commit()
        return order

    @staticmethod
    def get_order_by_number(order_number: str, customer_email: Optional[str] = None) -> Optional[Order]:
        query = Order.query.filter_by(order_number=order_number)
        if customer_email:
            query = query.filter_by(customer_email=customer_email)
        return query.first()

    @staticmethod
    def list_orders(user_id: Optional[str] = None, customer_email: Optional[str] = None, limit: int = 20) -> List[Order]:
        query = Order.query
        if user_id:
            query = query.filter_by(user_id=user_id)
        elif customer_email:
            query = query.filter_by(customer_email=customer_email)

        return query.order_by(Order.created_at.desc()).limit(limit).all()

    @staticmethod
    def cancel_order(order: Order, reason: str = "Canceled by customer") -> Order:
        if order.status in ["shipped", "delivered"]:
            raise ValueError("Order cannot be canceled after shipment")

        from app import db

        order.status = "canceled"
        order.canceled_at = datetime.utcnow()
        order.cancel_reason = reason
        order.add_timeline_event("canceled", reason)

        db.session.commit()
        return order

    @staticmethod
    def seed_sample_orders() -> int:
        from app import db

        if Order.query.count() > 0:
            return 0

        products = Product.query.limit(4).all()
        if len(products) < 2:
            return 0

        payloads = [
            {
                "customer_email": "client1@example.com",
                "shipping_address": "12 Rue Victor Hugo, Paris, 75015",
                "shipping_method": "standard",
                "carrier": "Colissimo",
                "shipping_fee": 6.99,
                "items": [
                    {"product_id": products[0].id, "quantity": 1},
                    {"product_id": products[1].id, "quantity": 1},
                ],
            },
            {
                "customer_email": "client2@example.com",
                "shipping_address": "8 Avenue de la Republique, Lyon, 69003",
                "shipping_method": "express",
                "carrier": "DHL",
                "shipping_fee": 12.5,
                "items": [
                    {"product_id": products[2].id, "quantity": 2},
                ],
            },
        ]

        created = 0
        for payload in payloads:
            order = OrderService.create_order(payload)
            created += 1

            if created == 2:
                order.status = "shipped"
                order.tracking_number = "TRK-902001-XYZ"
                order.shipped_at = datetime.utcnow() - timedelta(days=1)
                order.estimated_delivery_at = datetime.utcnow() + timedelta(days=2)
                order.add_timeline_event("shipped", "Package handed to carrier")

        db.session.commit()
        return created
