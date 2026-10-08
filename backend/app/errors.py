"""One error format everywhere: {"error": {"code", "message", "details"?}}"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class ApiError(Exception):
    def __init__(self, status, code, message, details=None):
        self.status, self.code, self.message, self.details = status, code, message, details


def error_response(status, code, message, details=None):
    body = {"error": {"code": code, "message": message}}
    if details:
        body["error"]["details"] = details
    return jsonify(body), status


def register_error_handlers(app, jwt):
    @app.errorhandler(ApiError)
    def api_error(e):
        return error_response(e.status, e.code, e.message, e.details)

    @app.errorhandler(HTTPException)
    def http_error(e):
        return error_response(e.code, e.name.upper().replace(" ", "_"), e.description)

    @app.errorhandler(Exception)
    def unexpected(e):
        log.exception("Unhandled error")
        return error_response(500, "INTERNAL_ERROR", "Something went wrong on our side.")

    @jwt.unauthorized_loader
    def missing_token(reason):
        return error_response(401, "UNAUTHENTICATED", "Log in to continue.")

    @jwt.invalid_token_loader
    def bad_token(reason):
        return error_response(401, "INVALID_TOKEN", "Your session is invalid. Log in again.")

    @jwt.expired_token_loader
    def expired_token(header, payload):
        return error_response(401, "TOKEN_EXPIRED", "Your session expired. Log in again.")
