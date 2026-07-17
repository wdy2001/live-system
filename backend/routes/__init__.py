"""路由注册"""
from .auth import auth_bp
from .households import households_bp
from .bills import bills_bp
from .rules import rules_bp
from .repairs import repairs_bp
from .dashboard import dashboard_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(households_bp, url_prefix="/api/households")
    app.register_blueprint(bills_bp, url_prefix="/api/bills")
    app.register_blueprint(rules_bp, url_prefix="/api/rules")
    app.register_blueprint(repairs_bp, url_prefix="/api/repairs")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
