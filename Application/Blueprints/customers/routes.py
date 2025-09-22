from Application.Blueprints.customers.schemas import customer_schema, customers_schema, login_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Customers, Service_Tickets, db
from Application.extensions import limiter, cache
from Application.utils.cache_utils import cache_response
from Application.utils.token_utils import encode_token, token_required
from Application.Blueprints.service_tickets.schemas import tickets_schema
from werkzeug.security import generate_password_hash

customers_bp = Blueprint('customers', __name__, url_prefix='/customers')

# GET /customers - Get all customers 
@customers_bp.route('', methods=['GET'])
@limiter.limit("10 per minute")
@cache_response(timeout=300)
def get_customers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)

    # Limit per_page to prevent excessive data retrieval
    per_page = min(per_page, 100)

    # SQLAlchemy's paginate method
    paginated_customers = db.paginate(
        select(Customers), page=page,
        per_page=per_page, error_out=False
    )

    # Format response with pagination metadata
    response_data = {
        'customers': customers_schema.dump(paginated_customers.items),
        'pagination': {
            'page': paginated_customers.page,
            'pages': paginated_customers.pages,
            'per_page': paginated_customers.per_page,
            'total': paginated_customers.total,
            'has_next': paginated_customers.has_next,
            'has_prev': paginated_customers.has_prev,
            'next_num': paginated_customers.next_num if paginated_customers.has_next else None,
            'prev_num': paginated_customers.prev_num if paginated_customers.has_prev else None
        }
    }

    return jsonify(response_data), 200
    
# GET /customers/<id> - Get a specific customer by ID
@customers_bp.route('/<int:customer_id>', methods=['GET'])
@limiter.limit("20 per minute")
@cache_response(timeout=600)
@cache.memoize(timeout=60)
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
    
    # Hash password before saving
    if 'password' in request.json:
        customer_data.set_password(request.json['password'])
    
    # new_customer = Customers(**customer_data)
    db.session.add(customer_data)
    db.session.commit()

    cache.delete_memoized(get_customers)

    return customer_schema.jsonify(customer_data), 201

# PUT /customers/<id> - Update an existing customer
@customers_bp.route('/<int:customer_id>', methods=['PUT'])
@limiter.limit("10 per minute")
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

# POST /customers/login - Customer login
@customers_bp.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Check if request has JSON data
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    # Check if JSON body exists and is not empty
    if request.json is None:
        return jsonify({"error": "Empty request body"}), 400

    try:
        login_data = login_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    # Find customer by email
    query = select(Customers).where(Customers.email == login_data['email'])
    customer = db.session.execute(query).scalars().first()

    if not customer or not customer.check_password(login_data['password']):
        return jsonify({"error": "Invalid email or password"}), 401
    
    token = encode_token(customer.id)

    return jsonify({
        "message": "Login successful", 
        "token": token, 
        "customer_id": customer.id
    }), 200

# GET /customers/my-tickets - Get all service tickets for the logged-in customer (requires token)
@customers_bp.route('/my-tickets', methods=['GET'])
@token_required
@limiter.limit("10 per minute")
def get_my_tickets(customer_id):
    # Query service tickets for this customer
    query = select(Service_Tickets).where(Service_Tickets.customer_id == customer_id)
    tickets = db.session.execute(query).scalars().all()

    return tickets_schema.jsonify(tickets), 200


@customers_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429
