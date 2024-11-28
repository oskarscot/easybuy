from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required

from extenstions import db
from models import User
from utils import validate_request, permission_required

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    request_data = request.get_json()

    validation_error = validate_request(request_data, ['email', 'password'])
    if validation_error:
        return jsonify({
            "status": "error",
            "message": validation_error
        }), 400

    email = request_data['email']
    password = request_data['password']

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({
            "status": "error",
            "message": "Invalid email or password."
        }), 401

    roles = [role.name for role in user.roles]
    token = create_access_token(identity=email, additional_claims={'roles': roles}, expires_delta=False)
    return jsonify({
        "status": "success",
        "message": "Logged in successfully.",
        "token": token
    }), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    request_data = request.get_json()

    validation_error = validate_request(request_data, ['username', 'email', 'password'])
    if validation_error:
        return jsonify({
            "status": "error",
            "message": validation_error
        }), 400

    username = request_data['username']
    email = request_data['email']
    password = request_data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({
            "status": "error",
            "message": "Username already registered."
        }), 409

    if User.query.filter_by(email=email).first():
        return jsonify({
            "status": "error",
            "message": "Email already registered."
        }), 409

    new_user = User(
        username=username,
        email=email,
        balance=0.0
    )
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Registered successfully."
    }), 201

@auth_bp.route('/manage_users', methods=['GET'])
@jwt_required()
@permission_required('manage_users')
def manage_users():
    return jsonify({
        "status": "success",
        "message": "You have access to manage users."
    })