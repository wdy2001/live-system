import pytest


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "life-payment"


def test_docs_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_protected_route_no_token(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
    body = resp.json()
    assert body.get("code") == 401


def test_register_invalid_body(client):
    resp = client.post("/api/auth/register", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body.get("code") == 422
    assert body.get("message") == "参数校验失败"
