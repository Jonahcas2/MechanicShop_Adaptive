from .schemas import mechanic_schema, mechanics_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import db, Mechanics
from Application.extensions import limiter, cache
from Application.utils.cache_utils import cache_response

mechanics_bp = Blueprint('mechanics', __name__, url_prefix='/mechanics')

# POST'/' - Create a new Mechanic
@mechanics_bp.route('', methods=['POST'])
@limiter.limit("5 per minute")
def create_mechanic():
    try:
        mechanic_data = mechanic_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    query = select(Mechanics).where(Mechanics.email == mechanic_data.email)
    existing_mechanic = db.session.execute(query).scalars().all()
    if existing_mechanic:
        return jsonify({"error": "Email already associated with an account"}), 400
    
    db.session.add(mechanic_data)
    db.session.commit()

    cache.delete_memoized(getAll_mechanics)

    return mechanic_schema.jsonify(mechanic_data), 201

# GET'/' - Retrieve all Mechanics
@mechanics_bp.route('', methods=['GET'])
@limiter.limit("10 per minute")
@cache_response(timeout=300)
def getAll_mechanics():
    query = select(Mechanics)
    mechanics = db.session.execute(query).scalars().all()

    return mechanics_schema.jsonify(mechanics)

# PUT'/<int:id>' - Updates a specific mechanic
@mechanics_bp.route('/<int:mechanic_id>', methods=['PUT'])
@limiter.limit("5 per minute")
def update_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanics, mechanic_id)
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    
    try:
        updated_mechanic = mechanic_schema.load(request.json, instance=mechanic)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()

    cache.delete_memoized(getAll_mechanics)

    return jsonify(mechanic_schema.dump(updated_mechanic)), 200


# DELETE'/<int:id>' - Deletes a specific mechanic based on ID passed
@mechanics_bp.route('/<int:mechanic_id>', methods=['DELETE'])
@limiter.limit("3 per minute")
def delete_mechanic(mechanic_id):
    mechanic = db.session.get(Mechanics, mechanic_id)

    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404
    
    db.session.delete(mechanic)
    db.session.commit()

    cache.delete_memoized(getAll_mechanics)
    return jsonify({"message": f'Mechanic id: {mechanic_id}, successfully deleted'}), 200


@mechanics_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429