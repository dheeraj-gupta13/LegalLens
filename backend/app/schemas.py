"""Request validation (pydantic). Invalid input -> 422 with per-field details."""
from typing import List

from flask import request
from pydantic import BaseModel, Field, ValidationError

from .errors import ApiError

EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class RegisterIn(BaseModel):
    email: str = Field(max_length=255, pattern=EMAIL)
    password: str = Field(min_length=8, max_length=128)


class LoginIn(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=1, max_length=128)


class MessageIn(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class ComparisonIn(BaseModel):
    document_ids: List[int] = Field(min_length=2, max_length=2)


def parse(model):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "INVALID_JSON", "Request body must be a JSON object.")
    try:
        return model.model_validate(data)
    except ValidationError as e:
        details = [{"field": ".".join(map(str, x["loc"])), "message": x["msg"]} for x in e.errors()]
        raise ApiError(422, "VALIDATION_ERROR", "Some fields are invalid.", details)
