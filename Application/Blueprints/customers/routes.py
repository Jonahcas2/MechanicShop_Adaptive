from .schemas import customer_schema, customers_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Customers, Service_Tickets, db

customers_bp = Blueprint('customers', __name__, url_prefix='/api/v1/customers')

# GET /api/v1/customers - Get all customers with optional filtering
@customers_bp.route('', methods=['GET'])
def get_customers():
    pass
    
# GET /api/v1/customers/<id> - Get a specific customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    pass

# POST /api/v1/customers - Create a new customer
@customers_bp.route('', methods=['POST'])
def create_customer():
    pass

# PUT /api/v1/customers/<id> - Update an existing customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    pass

# DELETE /api/v1/customers/<id> - Delete a customer
@customers_bp.route('/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    pass

# GET /api/v1/customers/<id>/service-tickets - Get customer's service tickets
@customers_bp.route('/<int:customer_id>/service-tickets', methods=['GET'])
def get_customer_service_tickets(customer_id):
    pass
