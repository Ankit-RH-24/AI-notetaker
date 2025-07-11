import firebase_admin
from firebase_admin import credentials, auth
from flask import request
import os
from dotenv import load_dotenv

load_dotenv()

# ✅ Load path to Firebase credentials from env
cred_path = os.environ.get("FIREBASE_CREDENTIAL_PATH")

# ✅ Initialize Firebase app (only if not already initialized)
if not firebase_admin._apps:
    if not cred_path or not os.path.exists(cred_path):
        raise Exception("❌ FIREBASE_CREDENTIAL_PATH is missing or invalid.")
    cred = credentials.Certificate(cred_path)
    firebase_admin.initialize_app(cred)

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
