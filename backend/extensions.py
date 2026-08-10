"""Flask 扩展实例（避免循环导入）"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
import werkzeug.security

_original_check_password_hash = werkzeug.security.check_password_hash


def _patched_check_password_hash(pwhash, password):
    if pwhash and pwhash.startswith("$pbkdf2$"):
        pwhash = pwhash[len("$pbkdf2$"):]
    return _original_check_password_hash(pwhash, password)


werkzeug.security.check_password_hash = _patched_check_password_hash

db = SQLAlchemy()
jwt = JWTManager()
