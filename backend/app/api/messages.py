from flask import url_for
from flask_jwt_extended import jwt_required

from ..extensions import db, limiter
from ..models import ChatSession, Message
from ..schemas import MessageIn, parse
from ..services import rag
from . import api_v1
from .helpers import ai_failure, current_user_id, get_document_or_404


def _session(doc):
    s = ChatSession.query.filter_by(user_id=current_user_id(), document_id=doc.id).first()
    if not s:
        s = ChatSession(user_id=current_user_id(), document_id=doc.id)
        db.session.add(s)
        db.session.commit()
    return s


@api_v1.get("/documents/<int:doc_id>/messages")
@jwt_required()
def list_messages(doc_id):
    doc = get_document_or_404(doc_id)
    return {"items": [m.to_dict() for m in _session(doc).messages]}


@api_v1.post("/documents/<int:doc_id>/messages")
@jwt_required()
@limiter.limit("30 per minute")
def create_message(doc_id):
    """Ask a question. Creates the user message and the AI answer; returns the answer (201)."""
    doc = get_document_or_404(doc_id, require_ready=True)
    question = parse(MessageIn).question.strip()
    s = _session(doc)
    history = [(m.role, m.content) for m in s.messages]
    try:
        answer, sources = rag.answer_question(doc.id, question, history)
    except Exception as e:
        raise ai_failure(e)
    user_msg = Message(session_id=s.id, role="user", content=question)
    ai_msg = Message(session_id=s.id, role="assistant", content=answer, sources=sources)
    db.session.add_all([user_msg, ai_msg])
    db.session.commit()
    return ai_msg.to_dict(), 201
