from flask_jwt_extended import get_jwt_identity

from ..errors import ApiError
from ..extensions import db
from ..models import Document


def current_user_id():
    return int(get_jwt_identity())


def get_document_or_404(doc_id, require_ready=False):
    """Return the caller's document. Other users' documents also give 404, so ids can't be probed."""
    doc = db.session.get(Document, doc_id)
    if not doc or doc.user_id != current_user_id():
        raise ApiError(404, "DOCUMENT_NOT_FOUND", "Document not found.")
    if require_ready and doc.status != "ready":
        raise ApiError(409, "DOCUMENT_NOT_READY", "This document is not ready yet.")
    return doc


def ai_failure(exc):
    import logging
    logging.getLogger(__name__).exception("AI provider call failed")
    return ApiError(502, "AI_SERVICE_ERROR", "The AI service failed. Try again in a moment.")
