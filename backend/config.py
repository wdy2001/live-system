"""应用配置"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get_int_env(name, default):
    val = os.getenv(name)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _build_db_uri(use_sqlite, db_user, db_password, db_host, db_port, db_name, sqlite_path=None):
    if use_sqlite:
        return f"sqlite:///{sqlite_path}" if sqlite_path else "sqlite:///life_system.db"
    return (
        f"mysql+pymysql://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}?charset=utf8mb4"
    )


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret")

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "life_system")
    USE_SQLITE = os.getenv("USE_SQLITE", "false").lower() == "true"
    DATABASE_URL = os.getenv("DATABASE_URL", None)

    SQLALCHEMY_DATABASE_URI = DATABASE_URL or _build_db_uri(
        USE_SQLITE, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True} if not USE_SQLITE else {}

    JWT_ACCESS_TOKEN_EXPIRES = _get_int_env("JWT_ACCESS_TOKEN_EXPIRES", 86400 * 7)


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    USE_SQLITE = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}


class ProductionConfig(Config):
    DEBUG = False


config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
