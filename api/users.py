from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extenstions import db
from models import User, Listing, Purchase
from utils import validate_request, permission_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()
    return jsonify(user.to_dict()), 200

@users_bp.route('/me/listings', methods=['GET'])
@jwt_required()
def me_listings():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    listings = Listing.query.filter_by(user_id=user.id).all()

    return jsonify({
        "status": "success",
        "listings": [listing.to_dict() for listing in listings]
    }), 200

@users_bp.route('/wallet/deposit', methods=['POST'])
@jwt_required()
def wallet_deposit():
    email = get_jwt_identity()

    request_data = request.get_json()
    validation_error = validate_request(request_data, ['amount'])
    if validation_error:
        return jsonify({
            "status": "error",
            "message": validation_error
        }), 400

    # should never happen
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found."
        }), 404

    try:
        amount = Decimal(request_data['amount'])
        if amount <= 0:
            return jsonify({
                "status": "error",
                "message": "Deposit amount must be greater than zero."
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid amount provided."
        }), 400

    user.balance += amount
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Successfully deposited {amount:.2f}.",
        "new_balance": str(user.balance)
    }), 200

@users_bp.route('/wallet/withdraw', methods=['POST'])
@jwt_required()
def wallet_withdraw():
    email = get_jwt_identity()

    request_data = request.get_json()
    validation_error = validate_request(request_data, ['amount'])
    if validation_error:
        return jsonify({
            "status": "error",
            "message": validation_error
        }), 400

    # should never happen
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({
            "status": "error",
            "message": "User not found."
        }), 404

    try:
        amount = Decimal(request_data['amount'])
        if amount <= 0:
            return jsonify({
                "status": "error",
                "message": "Withdrawal amount must be greater than zero."
            }), 400
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Invalid amount provided."
        }), 400

    user.balance -= amount
    db.session.commit()

    return jsonify({
        "status": "success",
        "message": f"Successfully withdrawn {amount:.2f}.",
        "new_balance": str(user.balance)
    }), 200

@users_bp.route('/delete/<int:user_id>', methods=['DELETE'])
@jwt_required()
@permission_required('manage_users')
def delete_user(user_id):
    to_delete = User.query.filter_by(id=user_id).first()
    if not to_delete:
        return jsonify({
            "status": "error",
            "message": "User not found."
        }), 404

    try:
        db.session.delete(to_delete)
        db.session.commit()
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred while deleting the user: {str(e)}"
        }), 500

    return jsonify({
        "status": "success",
        "message": f"User with ID {user_id} deleted successfully."
    }), 200

@users_bp.route('/me/purchases', methods=['GET'])
@jwt_required()
def me_purchases():
    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    purchases = Purchase.query.filter_by(buyer_id=user.id).all()

    return jsonify({
        "status": "success",
        "purchases": [
            {
                **purchase.to_dict(),
                "listing": Listing.query.filter_by(id=purchase.listing_id).first().to_dict()
            }
            for purchase in purchases
        ]
    })