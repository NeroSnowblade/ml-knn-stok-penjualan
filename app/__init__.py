import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv


db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app():
    # Load environment variables from a .env file if present
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)
    # Do not use setdefault here because Flask sets SECRET_KEY to None by default;
    # setdefault would skip overriding an existing (None) key.
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "dev-secret-key"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URI") or "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    login_manager.init_app(app)

    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.products import products_bp
    from .routes.transactions import transactions_bp
    from .routes.users import users_bp
    from .routes.reports import reports_bp
    from .routes.admin_tools import admin_tools_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(admin_tools_bp)

    # Template filters
    def currency(value):
        try:
            # Convert Decimals/strings/None safely
            number = float(value or 0)
        except (TypeError, ValueError):
            number = 0.0
        # Format with thousands separator and 2 decimals, e.g., 1,234,567.89
        return f"{number:,.2f}"

    app.jinja_env.filters["currency"] = currency

    # Pagination tokens filter: build a compact page list with ellipses
    def pagination_tokens(total_pages: int, current_page: int) -> list:
        try:
            total_pages = int(total_pages)
            current_page = int(current_page)
        except (TypeError, ValueError):
            return []
        if total_pages <= 0:
            return []
        # Always include first 3, current, and last 3 pages
        candidates = [1, 2, 3, total_pages - 2, total_pages - 1, total_pages, current_page]
        pages = []
        for p in candidates:
            if 1 <= p <= total_pages and p not in pages:
                pages.append(p)
        pages.sort()
        tokens = []
        prev = None
        for p in pages:
            if prev is not None and (p - prev) > 1:
                tokens.append("...")
            tokens.append(p)
            prev = p
        return tokens

    app.jinja_env.filters["pagination_tokens"] = pagination_tokens

    with app.app_context():
        from . import models  # noqa: F401
        db.create_all()
        from .utils import seed_default_admin, ensure_tipe_barang_column

        seed_default_admin()
        # Ensure DB has the new column if upgrading existing DBs
        try:
            ensure_tipe_barang_column()
        except Exception:
            # Avoid hard failure on startup; the admin route can still be used
            pass

    return app


@login_manager.user_loader
def load_user(user_id):
    from .models import User

    return User.query.get(int(user_id))
