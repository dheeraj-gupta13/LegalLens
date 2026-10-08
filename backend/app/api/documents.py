import os
import uuid

from flask import current_app, request, url_for
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import Analysis, ChatSession, Document
from ..services.ingest import ALLOWED, delete_vectors, ingest_document
from . import api_v1
from .helpers import current_user_id, get_document_or_404


@api_v1.get("/documents")
@jwt_required()
def list_documents():
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = min(max(request.args.get("per_page", 20, type=int), 1), 50)
    q = Document.query.filter_by(user_id=current_user_id()).order_by(Document.id.desc())
    p = q.paginate(page=page, per_page=per_page, error_out=False)
    return {"items": [d.to_dict() for d in p.items],
            "meta": {"page": p.page, "per_page": p.per_page, "total": p.total, "pages": p.pages}}


@api_v1.post("/documents")
@jwt_required()
@limiter.limit("20 per hour")
def create_document():
    f = request.files.get("file")
    if not f or not f.filename:
        raise ApiError(422, "VALIDATION_ERROR", "Some fields are invalid.",
                       [{"field": "file", "message": "Choose a file to upload."}])
    name = secure_filename(f.filename)
    if os.path.splitext(name)[1].lower() not in ALLOWED:
        raise ApiError(415, "UNSUPPORTED_FILE_TYPE", "Only PDF, DOCX and TXT files are supported.")

    path = os.path.join(current_app.config["UPLOAD_DIR"], f"{uuid.uuid4().hex}_{name}")
    f.save(path)
    doc = Document(user_id=current_user_id(), filename=name, path=path)
    db.session.add(doc)
    db.session.commit()
    try:  # synchronous for now; move to a task queue (Celery/RQ) for large files
        ingest_document(doc)
        doc.status = "ready"
        db.session.commit()
    except Exception as e:
        current_app.logger.exception("Ingestion failed")
        delete_vectors(doc.id)
        os.remove(path)
        db.session.delete(doc)
        db.session.commit()
        raise ApiError(422, "INGESTION_FAILED", f"Could not process the document: {e}")
    return doc.to_dict(), 201, {"Location": url_for("api_v1.get_document", doc_id=doc.id)}


@api_v1.get("/documents/<int:doc_id>")
@jwt_required()
def get_document(doc_id):
    return get_document_or_404(doc_id).to_dict()


@api_v1.delete("/documents/<int:doc_id>")
@jwt_required()
def delete_document(doc_id):
    doc = get_document_or_404(doc_id)
    delete_vectors(doc.id)
    Analysis.query.filter_by(document_id=doc.id).delete()
    for s in ChatSession.query.filter_by(document_id=doc.id).all():
        db.session.delete(s)
    if os.path.exists(doc.path):
        os.remove(doc.path)
    db.session.delete(doc)
    db.session.commit()
    return "", 204
