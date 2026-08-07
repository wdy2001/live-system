"""生活缴费系统 - Flask 应用入口"""
import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

from config import config_map
from extensions import db, jwt
from routes import register_routes


def create_app(config_name=None):
    app = Flask(__name__)
    config_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map[config_name])

    _BASE = os.path.dirname(os.path.abspath(__file__))
    _DIST = os.path.abspath(os.path.join(_BASE, "..", "dist"))
    _PUBLIC = os.path.abspath(os.path.join(_BASE, "..", "public"))

    app.config["PROPAGATE_EXCEPTIONS"] = False

    # 扩展初始化
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, supports_credentials=True)

    # 路由注册
    register_routes(app)

    # 健康检查
    @app.get("/api/health")
    def health():
        return jsonify(status="ok", service="life-system")

    # 全局错误处理
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(msg=str(e.description) if hasattr(e, "description") else "请求参数错误"), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(msg="资源不存在"), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify(msg="服务器内部错误"), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        traceback.print_exc()
        return jsonify(msg="服务器内部错误"), 500

    # 静态文件服务（前端构建产物）
    @app.get("/")
    def index():
        return send_from_directory(_DIST, "index.html")

    @app.get("/assets/<path:path>")
    def assets(path):
        return send_from_directory(os.path.join(_DIST, "assets"), path)

    @app.get("/favicon.svg")
    def favicon():
        return send_from_directory(_PUBLIC, "favicon.svg")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
