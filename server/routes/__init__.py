from .auth_routes import auth_bp
from .chat_routes import chat_bp
from .order_routes import order_bp
from .product_routes import product_bp
from .support_routes import support_bp
from .cart_routes import cart_bp
from .checkout_routes import checkout_bp


def register_routes(app):
    """Register all route blueprints"""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(order_bp, url_prefix="/api/orders")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(support_bp, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api/cart")
    app.register_blueprint(checkout_bp, url_prefix="/api")
