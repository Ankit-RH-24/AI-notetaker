import firebase_admin
from firebase_admin import credentials, auth
from flask import request
import os
from dotenv import load_dotenv
import json
import tempfile

load_dotenv()

# ✅ Load Firebase credentials JSON from env
firebase_json = os.environ.get("FIREBASE_CREDENTIAL_JSON")

# ✅ Initialize Firebase app (only if not already initialized)
if not firebase_admin._apps:
    if not firebase_json:
        raise Exception("❌ FIREBASE_CREDENTIAL_JSON is missing.")

    try:
        # Create a temporary file to hold the JSON
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".json") as tmp_file:
            tmp_file.write(firebase_json)
            tmp_file.flush()
            tmp_path = tmp_file.name

        cred = credentials.Certificate(tmp_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise Exception(f"❌ Failed to initialize Firebase app: {e}")

def verify_firebase_token(request):
    """
    Extracts and verifies Firebase token from the Authorization header.
    Expected format: Authorization: Bearer <idToken>
    Returns the decoded token (dict) if valid, else None.
    """
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        id_token = auth_header.split(" ")[1]
    else:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token  # Contains uid, phone_number, etc.
    except Exception as e:
        print("❌ Firebase token verification failed:", e)
        return None
