from functools import wraps
from flask import request
from Application.extensions import cache
import json, hashlib

def cache_key_generator(*args, **kwargs):
    """Generate cache key from request args and kwargs"""
    key_parts = [request.path]

    # Add URL parameters
    if request.view_args:
        key_parts.extend(str(v) for v in request.view_args.values())

    # Add query parameters
    if request.args:
        sorted_args = sorted(request.args.items())
        key_parts.append(hashlib.md5(str(sorted_args).encode()).hexdigest()[:8])
    
    return ":".join(key_parts)

def cache_response(timeout=300):
    """Decorator to cache GET responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != 'GET':
                return f(*args, **kwargs)
            
            cache_key = cache_key_generator(*args, **kwargs)
            cached_response = cache.get(cache_key)

            if cached_response:
                return json.loads(cached_response)
            
            response = f(*args, **kwargs)
            cache.set(cache_key, response, timeout=timeout)
            return response
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
    pass