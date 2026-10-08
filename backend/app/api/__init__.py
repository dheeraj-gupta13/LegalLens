from flask import Blueprint

api_v1 = Blueprint("api_v1", __name__)


@api_v1.get("/health")
def health():
    return {"status": "ok"}


from . import analysis, auth, documents, messages  # noqa: E402,F401  (register routes)
