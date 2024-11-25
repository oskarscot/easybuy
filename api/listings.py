from datetime import datetime
from flask import Blueprint, jsonify, request

from extenstions import db
from models import Listing
from utils import validate_request

listings_bp = Blueprint('listings', __name__)

@listings_bp.route('/create', methods=['POST'])
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

    if not isinstance(price, (int, float)) or price <= 0:
        return jsonify({
            "status": "error",
            "message": "Price must be a positive number."
        }), 400

    new_listing = Listing(
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
            "title": new_listing.title,
            "description": new_listing.description,
            "price": new_listing.price,
            "created_at": new_listing.created_at.isoformat(),
            "updated_at": new_listing.updated_at.isoformat()
        }
    }), 201

@listings_bp.route('/listings', methods=['GET'])
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


@listings_bp.route('/delete/<int:listing_id>', methods=['DELETE'])
def delete_listing(listing_id):
    listing = Listing.query.get(listing_id)

    if not listing:
        return jsonify({
            "status": "error",
            "message": f"Listing with ID {listing_id} not found."
        }), 404

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