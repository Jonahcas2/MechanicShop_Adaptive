from .schemas import customer_schema, customers_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Customers, Service_Tickets, db

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

# GET /customers - Get all customers 
@customers_bp.route('', methods=['GET'])
def get_customers():
    query = select(Customers)
    customers = db.session.execute(query).scalars().all()

    return customers_schema.jsonify(customers)
    
# GET /customers/<id> - Get a specific customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    customer = db.session.get(Customers, customer_id)

    if customer:
        return customer_schema.jsonify(customer), 200
    return jsonify({"error": "Customer not found."}), 404
    pass

# POST /customers - Create a new customer
@customers_bp.route('', methods=['POST'])
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
    return customer_schema.jsonify(customer_data), 201

# PUT /customers/<id> - Update an existing customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    customer = db.session.get(Customers, customer_id)
    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    try:
        updated_customer = customer_schema.load(request.json, instance=customer)
    except ValidationError as e:
        return jsonify(e.messages), 400

    db.session.commit()
    return customer_schema.jsonify(update_customer), 200

# DELETE /customers/<id> - Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customer = db.session.get(Customers, customer_id)

    if not customer:
        return jsonify({"error": "Customer not found"}), 404
    
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": f'Customer id: {customer_id}, successfully deleted'}), 200
