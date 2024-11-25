from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt import ExpiredSignatureError, InvalidTokenError

from models import User


def validate_request(data, required_fields):
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return f"Missing fields: {', '.join(missing_fields)}"
    return None

def permission_required(permission_name):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            email = get_jwt_identity()
            user = User.query.filter_by(email=email).first()
            if not user or not user.has_permission(permission_name):
                return jsonify({
                    "status": "error",
                    "message": "You do not have permission to perform this action."
                }), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator

def register_error_handlers(app):
    @app.errorhandler(NoAuthorizationError)
    def handle_no_authorization_error(e):
        return jsonify({
            "status": "error",
            "message": "Authentication token is missing. Please provide a valid token."
        }), 401

    @app.errorhandler(ExpiredSignatureError)
    def handle_expired_signature_error(e):
        return jsonify({
            "status": "error",
            "message": "Your token has expired. Please log in again."
        }), 401

    @app.errorhandler(InvalidTokenError)
    def handle_invalid_token_error(e):
        return jsonify({
            "status": "error",
            "message": "Invalid token. Please provide a valid token."
        }), 401