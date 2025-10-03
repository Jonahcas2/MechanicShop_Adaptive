from .schemas import inventory_schema, inventories_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Inventory, db
from Application.extensions import limiter, cache
from Application.utils.cache_utils import cache_response
from Application.utils.cache_utils import cache_key_generator

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# POST '/' -Create a new inventory item
@inventory_bp.route('', methods=['POST'])
@limiter.limit("5 per minute")
def create_inventory():
    try:
        inventory_data = inventory_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    db.session.add(inventory_data)
    db.session.commit()

    cache.delete_memoized(get_all_inventory)

    return inventory_schema.jsonify(inventory_data), 201

# GET '/' - Get all inventory items
@inventory_bp.route('', methods=['GET'])
@limiter.limit("15 per minute")
@cache_response(timeout=300)
def get_all_inventory():
    query = select(Inventory)
    inventory_items = db.session.execute(query).scalars().all()

    return inventories_schema.jsonify(inventory_items), 200

# GET '/<int:id>' - Get a specific inventory item
@inventory_bp.route('/<int:inventory_id>', methods=['GET'])
@limiter.limit("20 per minute")
@cache_response(timeout=600)
@cache.memoize(timeout=60)
def get_inventory_item(inventory_id):
    inventory_item = db.session.get(Inventory, inventory_id)

    if inventory_item:
        return inventory_schema.jsonify(inventory_item), 200
    return jsonify({"error": "Inventory item not found"}), 404

# PUT '/<int:id>' - Update an inventory item
@inventory_bp.route('/<int:inventory_id>', methods=['PUT'])
@limiter.limit("5 per minute")
def update_inventory(inventory_id):
    inventory_item = db.session.get(Inventory, inventory_id)
    if not inventory_item:
        return jsonify({"error": "Inventory item not found"}), 404
    try:
        updated_inventory = inventory_schema.load(request.json, instance=inventory_item)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    db.session.commit()

    cache.delete_memoized(get_all_inventory)
    cache.delete_memoized(get_inventory_item, inventory_id)

    return inventory_schema.jsonify(updated_inventory), 200

# DELETE '/<int:id>' - Delete an inventory item
@inventory_bp.route('/<int:inventory_id>', methods=['DELETE'])
@limiter.limit("3 per minute")
def delete_inventory(inventory_id):
    inventory_item = db.session.get(Inventory, inventory_id)

    if not inventory_item:
        return jsonify({"error": "Inventory item not found"}), 404
    
    db.session.delete(inventory_item)
    db.session.commit()

    # Remove cached responses created by our custom cache_response decorator.
    # cache_response stores cached data under a key equal to the request path
    # (and query/hash for query params). Delete both the list and the item keys.
    try:
        # Delete the exact cache key used for this item (generated from the request)
        item_cache_key = cache_key_generator()
        cache.delete(item_cache_key)
        # Also delete the list cache key (no view args)
        cache.delete('/inventory')
    except Exception:
        # best-effort: continue even if cache backend doesn't support delete
        pass

    # Also attempt to clear any memoized entries (if used elsewhere)
    cache.delete_memoized(get_all_inventory)
    cache.delete_memoized(get_inventory_item, inventory_id)

    return jsonify({"message": f'Inventory item id:{inventory_id}, successfully deleted'}), 200

@inventory_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429