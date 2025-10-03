from functools import wraps
from flask import request, make_response, current_app
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
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method != 'GET':
                return f(*args, **kwargs)

            cache_key = cache_key_generator(*args, **kwargs)
            cached = cache.get(cache_key)
            if cached:
                # cached is a JSON string that contains body and status
                payload = json.loads(cached)
                body = payload.get('body', '')
                status = payload.get('status', 200)
                content_type = payload.get('content_type', 'application/json')
                resp = make_response(body, status)
                resp.headers['Content-Type'] = content_type
                return resp

            # Call the view function
            rv = f(*args, **kwargs)

            # Normalize to (body_text, status, content_type)
            if isinstance(rv, tuple):
                # (response, status) or (response, status, headers)
                response_obj = rv[0]
                status = rv[1] if len(rv) > 1 else 200
            else:
                response_obj = rv
                status = 200

            # response_obj is a Flask Response (jsonify returns one)
            body_text = response_obj.get_data(as_text=True)
            content_type = response_obj.headers.get('Content-Type', 'application/json')

            # store a safe JSON string with the body and status
            cache_payload = json.dumps({
                'body': body_text,
                'status': status,
                'content_type': content_type
            })
            cache.set(cache_key, cache_payload, timeout=timeout)

            return rv
        return decorated_function
    return decorator

def invalidate_cache_pattern(pattern):
    pass