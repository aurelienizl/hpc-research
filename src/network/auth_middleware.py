from functools import wraps
from flask import request, jsonify
from hmac import compare_digest

class AuthMiddleware:
    def __init__(self, api_key: str, trusted_ips: list[str]):
        self.api_key = api_key
        self.trusted_ips = trusted_ips

    def require_auth(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if request.remote_addr not in self.trusted_ips:
                return jsonify({"error": "Unauthorized IP"}), 403

            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"error": "Missing authorization"}), 401

            api_key = auth_header.split(' ')[1]
            if not compare_digest(api_key, self.api_key):
                return jsonify({"error": "Invalid authorization"}), 401

            return f(*args, **kwargs)
        return decorated
