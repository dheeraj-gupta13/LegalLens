from flask import request
from flask_jwt_extended import create_access_token, jwt_required

from ..errors import ApiError
from ..extensions import db, limiter
from ..models import User
from ..schemas import LoginIn, RegisterIn, parse
from . import api_v1
from .helpers import current_user_id


def _session(user, status):
    token = create_access_token(identity=str(user.id))
    return {"user": user.to_dict(), "access_token": token, "token_type": "Bearer"}, status


@api_v1.post("/auth/register")
@limiter.limit("10 per hour")
def register():
    data = parse(RegisterIn)
    email = data.email.strip().lower()
    if User.query.filter_by(email=email).first():
        raise ApiError(409, "EMAIL_TAKEN", "That email is already registered.")
    user = User(email=email)
    user.set_password(data.password)
    db.session.add(user)
    db.session.commit()
    return _session(user, 201)


@api_v1.post("/auth/login")
@limiter.limit("10 per minute")
def login():
    data = parse(LoginIn)
    user = User.query.filter_by(email=data.email.strip().lower()).first()
    if not user or not user.check_password(data.password):
        raise ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")
    return _session(user, 200)


@api_v1.get("/auth/me")
@jwt_required()
def me():
    return {"user": db.session.get(User, current_user_id()).to_dict()}
