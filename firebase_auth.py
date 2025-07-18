import firebase_admin
from firebase_admin import credentials, auth
from flask import request
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Load the path to Firebase credentials file
firebase_json_path = os.environ.get("FIREBASE_CREDENTIAL_JSON")

# ✅ Initialize Firebase app if not already initialized
if not firebase_admin._apps:
    if not firebase_json_path or not os.path.exists(firebase_json_path):
        raise Exception("❌ FIREBASE_CREDENTIAL_JSON is missing or file path is invalid.")

    try:
        cred = credentials.Certificate(firebase_json_path)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        raise Exception(f"❌ Failed to initialize Firebase app: {e}")

def verify_firebase_token(request):
    """
    Verifies Firebase ID token from Authorization header.
    Expected format: Authorization: Bearer <idToken>
    Returns decoded token dict if valid, else None.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        id_token = auth_header.split(" ")[1]
    else:
        return None

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print("❌ Firebase token verification failed:", e)
        return None
