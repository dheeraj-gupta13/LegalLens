from flask_jwt_extended import jwt_required

from ..extensions import db, limiter
from ..models import Analysis
from ..schemas import ComparisonIn, parse
from ..errors import ApiError
from ..services import rag
from . import api_v1
from .helpers import ai_failure, get_document_or_404


def _analysis_for(doc):
    row = Analysis.query.filter_by(document_id=doc.id).first()
    if not row:  # generated once, then cached
        row = Analysis(document_id=doc.id, result=rag.analyze_document(doc.id))
        db.session.add(row)
        db.session.commit()
    return row.result


@api_v1.get("/documents/<int:doc_id>/analysis")
@jwt_required()
@limiter.limit("10 per minute")
def get_analysis(doc_id):
    doc = get_document_or_404(doc_id, require_ready=True)
    try:
        return _analysis_for(doc)
    except Exception as e:
        raise ai_failure(e)


@api_v1.post("/comparisons")
@jwt_required()
@limiter.limit("10 per minute")
def create_comparison():
    ids = parse(ComparisonIn).document_ids
    if ids[0] == ids[1]:
        raise ApiError(422, "VALIDATION_ERROR", "Some fields are invalid.",
                       [{"field": "document_ids", "message": "Pick two different documents."}])
    a, b = (get_document_or_404(i, require_ready=True) for i in ids)
    try:
        text = rag.compare_documents(a.filename, _analysis_for(a), b.filename, _analysis_for(b))
    except Exception as e:
        raise ai_failure(e)
    return {"document_ids": ids, "comparison": text}
