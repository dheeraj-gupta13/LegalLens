"""Run with: pytest   (tests avoid any LLM calls)"""
import pytest

from app import create_app
from app.config import TestingConfig
from app.extensions import db


@pytest.fixture()
def client():
    app = create_app(TestingConfig)
    with app.test_client() as c:
        yield c
    with app.app_context():
        db.drop_all()


def register(client, email="a@b.com", password="longenough1"):
    return client.post("/api/v1/auth/register", json={"email": email, "password": password})


def auth(client):
    token = register(client).get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    assert client.get("/api/v1/health").get_json() == {"status": "ok"}


def test_register_validation_returns_422_with_details(client):
    r = register(client, email="nope", password="short")
    assert r.status_code == 422
    assert {d["field"] for d in r.get_json()["error"]["details"]} == {"email", "password"}


def test_register_login_me_flow(client):
    assert register(client).status_code == 201
    assert register(client).status_code == 409
    bad = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "wrong-pass"})
    assert bad.status_code == 401
    ok = client.post("/api/v1/auth/login", json={"email": "a@b.com", "password": "longenough1"})
    headers = {"Authorization": "Bearer " + ok.get_json()["access_token"]}
    assert client.get("/api/v1/auth/me", headers=headers).get_json()["user"]["email"] == "a@b.com"


def test_documents_require_auth(client):
    r = client.get("/api/v1/documents")
    assert r.status_code == 401 and r.get_json()["error"]["code"] == "UNAUTHENTICATED"


def test_empty_list_and_missing_document(client):
    h = auth(client)
    assert client.get("/api/v1/documents", headers=h).get_json()["meta"]["total"] == 0
    r = client.get("/api/v1/documents/999", headers=h)
    assert r.status_code == 404 and r.get_json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_upload_rejects_unsupported_type(client):
    from io import BytesIO
    r = client.post("/api/v1/documents", headers=auth(client),
                    data={"file": (BytesIO(b"x"), "evil.exe")}, content_type="multipart/form-data")
    assert r.status_code == 415
