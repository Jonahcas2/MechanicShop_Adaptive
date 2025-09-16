from jose import jwt, JWTError
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from Application.models import Customers, db
import os

SECRET_KEY = os.getenv('SECRET', 'default_secret')

def encode_token(customer_id):
    """Create a JWT token for a customer"""
    payload = {
        'customer_id': customer_id,
        'exp': datetime.now() + timedelta(hours=24),
        'iat': datetime.now(),
        'type': 'customer'
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def decode_token(token):
    """Decode & validate JWT token"""
    try:
        payload = jwt.decode(payload, SECRET_KEY, algorithm='HS256')
        return payload
    except JWTError:
        return None

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Authorization header is missing'}), 402
        
        # Check if it's a Bearer token
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return jsonify({'error': 'Invalid token format. Use Bearer token'}), 401
        except ValueError:
            return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        # Decode the token
        payload = decode_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Get customer_id from payload
        customer_id = payload.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'Invalid token payload'}), 401
        
        # Verify customer exists
        customer = db.session.get(Customers, customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Pass customer_id to the decorated function
        return f(customer_id, *args, **kwargs)
    
    return decorated