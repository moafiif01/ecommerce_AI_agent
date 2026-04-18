from typing import Any, Dict, List, Optional
from models.cart import Cart, CartItem
from models.product import Product


class CartService:
    @staticmethod
    def get_or_create_cart(user_id: Optional[str] = None, session_id: Optional[str] = None) -> Cart:
        """Get existing cart or create new one"""
        from app import db
        
        if user_id:
            cart = Cart.query.filter_by(user_id=user_id, status="active").first()
            if cart:
                return cart
            cart = Cart(user_id=user_id)
        elif session_id:
            cart = Cart.query.filter_by(session_id=session_id, status="active").first()
            if cart:
                return cart
            cart = Cart(session_id=session_id)
        else:
            raise ValueError("Either user_id or session_id required")

        db.session.add(cart)
        db.session.commit()
        return cart

    @staticmethod
    def add_item(
        cart_id: str,
        product_id: str,
        quantity: int = 1,
        unit_price: Optional[float] = None,
    ) -> CartItem:
        """Add item to cart or increment quantity if exists"""
        from app import db
        
        cart = Cart.query.get(cart_id)
        if not cart:
            raise ValueError("Cart not found")

        product = Product.query.get(product_id)
        if not product:
            raise ValueError(f"Product {product_id} not found")

        if unit_price is None:
            unit_price = product.price

        # Check if item already in cart
        existing_item = CartItem.query.filter_by(
            cart_id=cart_id, product_id=product_id
        ).first()

        if existing_item:
            existing_item.quantity += quantity
            existing_item.line_total = round(existing_item.unit_price * existing_item.quantity, 2)
            db.session.commit()
            cart.recalculate_totals()
            db.session.commit()
            return existing_item

        # New item
        item = CartItem(
            cart_id=cart_id,
            product_id=product_id,
            product_name=product.name,
            unit_price=unit_price,
            quantity=quantity,
            line_total=round(unit_price * quantity, 2),
        )
        db.session.add(item)
        db.session.commit()

        cart.recalculate_totals()
        db.session.commit()
        return item

    @staticmethod
    def remove_item(cart_id: str, item_id: str) -> Cart:
        """Remove item from cart"""
        from app import db
        
        item = CartItem.query.filter_by(id=item_id, cart_id=cart_id).first()
        if not item:
            raise ValueError("Item not found in cart")

        cart = item.cart
        db.session.delete(item)
        db.session.commit()

        cart.recalculate_totals()
        db.session.commit()
        return cart

    @staticmethod
    def update_item_quantity(cart_id: str, item_id: str, quantity: int) -> CartItem:
        """Update item quantity"""
        from app import db
        
        if quantity <= 0:
            return CartService.remove_item(cart_id, item_id)

        item = CartItem.query.filter_by(id=item_id, cart_id=cart_id).first()
        if not item:
            raise ValueError("Item not found in cart")

        product = Product.query.get(item.product_id)
        if quantity > product.stock:
            raise ValueError(f"Only {product.stock} in stock")

        item.quantity = quantity
        item.line_total = round(item.unit_price * quantity, 2)
        db.session.commit()

        cart = item.cart
        cart.recalculate_totals()
        db.session.commit()
        return item

    @staticmethod
    def clear_cart(cart_id: str) -> Cart:
        """Clear all items from cart"""
        from app import db
        
        cart = Cart.query.get(cart_id)
        if not cart:
            raise ValueError("Cart not found")

        CartItem.query.filter_by(cart_id=cart_id).delete()
        db.session.commit()

        cart.recalculate_totals()
        db.session.commit()
        return cart

    @staticmethod
    def apply_discount(cart_id: str, discount_amount: float) -> Cart:
        """Apply discount code or manual discount"""
        from app import db
        
        cart = Cart.query.get(cart_id)
        if not cart:
            raise ValueError("Cart not found")

        if discount_amount < 0:
            raise ValueError("Discount cannot be negative")

        if discount_amount > cart.subtotal:
            raise ValueError("Discount exceeds subtotal")

        cart.discount = round(discount_amount, 2)
        cart.total = round(cart.subtotal + cart.tax + cart.shipping - cart.discount, 2)
        db.session.commit()
        return cart

    @staticmethod
    def convert_to_order(cart_id: str) -> str:
        """Mark cart as converted (order created from this cart)"""
        from app import db
        
        cart = Cart.query.get(cart_id)
        if not cart:
            raise ValueError("Cart not found")

        cart.status = "converted"
        db.session.commit()
        return cart_id
