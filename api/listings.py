from datetime import datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from extenstions import db
from models import Listing, User, Purchase
from utils import validate_request

listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/create', methods=['POST'])
@jwt_required() # make sure only signed in users can create listings
def create_listing():
    request_data = request.get_json()

    validation_error = validate_request(request_data, ['title', 'description', 'price'])
    if validation_error:
        return jsonify({
            "status": "error",
            "message": validation_error
        }), 400

    title = request_data['title']
    description = request_data['description']
    price = request_data['price']

    try:
        price = Decimal(price)
        if price <= 0:
            raise ValueError("Price must be a positive number.")
    except (ValueError, TypeError):
        return jsonify({
            "status": "error",
            "message": "Price must be a positive number."
        }), 400

    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    new_listing = Listing(
        user_id=user.id,
        title=title,
        description=description,
        price=price,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    try:
        db.session.add(new_listing)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": "error",
            "message": f"An error occurred while creating the listing: {str(e)}"
        }), 500

    return jsonify({
        "status": "success",
        "message": "Listing created successfully.",
        "listing": {
            "id": new_listing.id,
            "user_id": new_listing.user_id,
            "title": new_listing.title,
            "description": new_listing.description,
            "price": new_listing.price,
            "created_at": new_listing.created_at.isoformat(),
            "updated_at": new_listing.updated_at.isoformat()
        }
    }), 201

@listings_bp.route('/', methods=['GET'])
def get_listings():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    paginated_listings = Listing.query.paginate(page=page, per_page=per_page, error_out=False)

    response = {
        "status": "success",
        "page": paginated_listings.page,
        "per_page": paginated_listings.per_page,
        "total_items": paginated_listings.total,
        "total_pages": paginated_listings.pages,
        "listings": [listing.to_dict() for listing in paginated_listings.items]
    }

    return jsonify(response), 200

@listings_bp.route('/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    listing = Listing.query.get(listing_id)

    if not listing:
        return jsonify({
            "status": "error",
            "message": f"Listing with ID {listing_id} not found."
        }), 404

    return jsonify({
        "status": "success",
        "listing": listing.to_dict()
    }), 200

@listings_bp.route('/<int:listing_id>/buy', methods=['POST'])
@jwt_required()
def buy_listing(listing_id):
    current_user_email = get_jwt_identity()
    buyer = User.query.filter_by(email=current_user_email).first()

    # this should never happen because the token would belong to the buyer
    if not buyer:
        return jsonify({
            "status": "error",
            "message": "User not found"
        }), 404

    listing = Listing.query.get(listing_id)
    if not listing:
        return jsonify({
            "status": "error",
            "message": "Listing not found"
        }), 404

    if listing.user_id == buyer.id:
        return jsonify({
            "status": "error",
            "message": "You cannot buy your own listing."
        }), 400

    if listing.status != 'active':
        return jsonify({
            "status": "error",
            "message": "Listing is not available for purchase"
        }), 400

    if buyer.balance < listing.price:
        return jsonify({
            "status": "error",
            "message": "Insufficient balance"
        }), 400

    buyer.balance -= listing.price
    listing.status = 'sold'

    purchase = Purchase(listing_id=listing.id, buyer_id=buyer.id)
    db.session.add(purchase)

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Purchase completed successfully.",
        "purchase": purchase.to_dict(),
        "listing": listing.to_dict()
    }), 200


@listings_bp.route('/delete/<int:listing_id>', methods=['DELETE'])
@jwt_required()
def delete_listing(listing_id):
    listing = Listing.query.get(listing_id)

    if not listing:
        return jsonify({
            "status": "error",
            "message": f"Listing with ID {listing_id} not found."
        }), 404

    email = get_jwt_identity()
    user = User.query.filter_by(email=email).first()

    if not user.id == listing.user_id and not user.has_permission('manage_listings'):
        return jsonify({
            "status": "error",
            "message": "You are not authorized to delete listings."
        }), 400

    try:
        db.session.delete(listing)
        db.session.commit()
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred while deleting the listing: {str(e)}"
        }), 500

    return jsonify({
        "status": "success",
        "message": f"Listing with ID {listing_id} deleted successfully."
    }), 200