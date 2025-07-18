import os
import json
import firebase_admin
from firebase_admin import credentials, auth
from flask import request, jsonify
from functools import wraps

# --- Get FIREBASE credential from env ---
firebase_json_str = os.getenv("FIREBASE_CREDENTIAL_JSON")

if not firebase_json_str:
    raise Exception("❌ FIREBASE_CREDENTIAL_JSON is missing or file path is invalid.")

try:
    # Convert JSON string to dict
    firebase_cred_dict = json.loads(firebase_json_str)

    # Use dict to initialize credentials
    cred = credentials.Certificate(firebase_cred_dict)
    firebase_admin.initialize_app(cred)
    print("✅ Firebase initialized successfully.")
except Exception as e:
    raise Exception(f"❌ Failed to initialize Firebase app: {e}")

# --- Token verification decorator ---
def verify_firebase_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401

        id_token = auth_header.split("Bearer ")[1]

        try:
            decoded_token = auth.verify_id_token(id_token)
            request.user = decoded_token
        except Exception as e:
            print("❌ Firebase token verification failed:", e)
            return jsonify({"error": "Unauthorized"}), 401

        return f(*args, **kwargs)
    return decorated_function

def get_firebase_user(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    id_token = auth_header.split("Bearer ")[1]
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print("❌ Firebase token verification failed:", e)
        return None
