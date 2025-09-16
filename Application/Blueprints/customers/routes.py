from .schemas import customer_schema, customers_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Customers, Service_Tickets, db
from Application.extensions import limiter, cache
from Application.utils.cache_utils import cache_response

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

# GET /customers - Get all customers 
@customers_bp.route('', methods=['GET'])
@limiter.limit("10 per minute")
@cache_response(timeout=300)
def get_customers():
    query = select(Customers)
    customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers)
    
# GET /customers/<id> - Get a specific customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
@limiter.limit("20 per minute")
@cache_response(timeout=600)
def get_customer(customer_id):
    customer = db.session.get(Customers, customer_id)

    if customer:
        return customer_schema.jsonify(customer), 200
    return jsonify({"error": "Customer not found."}), 404
    pass

# POST /customers - Create a new customer
@customers_bp.route('', methods=['POST'])
@limiter.limit("5 per minute")
def create_customer():
    try:
        customer_data = customer_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    query = select(Customers).where(Customers.email == customer_data.email) # Checking the db for a customer with this email
    existing_customer = db.session.execute(query).scalars().all()
    if existing_customer:
        return jsonify({"error": "Email already associated with an account"}), 400
    
    # new_customer = Customers(**customer_data)
    db.session.add(customer_data)
    db.session.commit()

    cache.delete_memoized(get_customers)

    return customer_schema.jsonify(customer_data), 201

# PUT /customers/<id> - Update an existing customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@limiter
def update_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    try:
        updated_customer = customer_schema.load(request.json, instance=customer)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()

    cache.delete_memoized(get_customers)
    cache.delete_memoized(get_customer, customer_id)

    return customer_schema.jsonify(update_customer), 200

# DELETE /customers/<id> - Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
@limiter.limit("3 per minute")
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()

    cache.delete_memoized(get_customers)
    cache.delete_memoized(get_customer, customer_id)

    return jsonify({"message": f'Customer id: {customer_id}, successfully deleted'}), 200

@customers_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429
