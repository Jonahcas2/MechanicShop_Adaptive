from .schemas import mechanic_schema, mechanics_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select, func
from Application.models import db, Mechanics
from Application.models import Service_Mechanics
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

# GET '/ranking' - Get mechanics order by most tickets worked on
@mechanics_bp.route('/ranking', methods=['GET'])
@limiter.limit("10 per minute")
@cache_response(timeout=600)
def get_mechanic_ranking():
    # Query mechanics with ticket count, ordered by ticket count descending
    query = (
        select(
            Mechanics, func.count(Service_Mechanics.mechanic_id).label('ticket_count')
        )
        .outerjoin(Service_Mechanics, Mechanics.id == Service_Mechanics.mechanic_id)
        .group_by(Mechanics.id)
        .order_by(func.count(Service_Mechanics.mechanic_id).desc())
    )

    results = db.session.execute(query).all()

    # Format the response to include ticket count
    ranking_data = []
    for mechanic, ticket_count in results:
        mechanic_data = mechanic_schema.dump(mechanic)
        mechanic_data['tickets_worked_on'] = ticket_count
        ranking_data.append(mechanic_data)
    return jsonify(ranking_data), 200


@mechanics_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429