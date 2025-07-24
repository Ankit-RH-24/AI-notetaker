from flask import request, jsonify
from functools import wraps
import firebase_admin
from firebase_admin import auth

def verify_firebase_token(f):
    """
    A decorator to protect routes by verifying the Firebase ID token.
    The token should be passed in the 'Authorization' header as 'Bearer <token>'.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the token from the Authorization header
        auth_header = request.headers.get("Authorization")
        id_token = None

        if auth_header and auth_header.startswith("Bearer "):
            id_token = auth_header.split("Bearer ")[1]

        if not id_token:
            return jsonify({"error": "Authorization token is missing or invalid"}), 401

        try:
            # Verify the token using the Firebase Admin SDK
            decoded_token = auth.verify_id_token(id_token)
            # Attach the decoded user info to the request object for use in the route
            request.user = decoded_token
        except Exception as e:
            # Handle various errors like expired, revoked, or malformed tokens
            print(f"❌ Firebase token verification failed: {e}")
            return jsonify({"error": "Unauthorized: Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated_function
