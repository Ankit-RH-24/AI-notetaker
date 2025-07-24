import os
import json # Import the json library
from flask import Flask, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials

from backend.routes.transcripts import bp as transcripts_bp

# Load environment variables from .env
load_dotenv()

# --- SECURE CREDENTIALS INITIALIZATION ---
# This block will read from an environment variable in production (Render)
# and from a local file during development.
creds_json_str = os.getenv("FIREBASE_CREDENTIAL_JSON")

if creds_json_str:
    # In production (Render), load credentials from the environment variable
    creds_info = json.loads(creds_json_str)
    cred = credentials.Certificate(creds_info)
else:
    # In local development, load credentials from the file
    cred = credentials.Certificate("serviceAccountKey.json")

firebase_admin.initialize_app(cred)


# --- Create Flask App ---
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Register API blueprint
app.register_blueprint(transcripts_bp, url_prefix="/api/transcripts")


# --- Frontend Routes ---
@app.route("/")
def index():
    # This correctly serves the main application page.
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }
    return render_template("index.html", firebase_config=firebase_config)

@app.route("/login")
def login():
    # This correctly serves the login page.
    firebase_config = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }
    return render_template("login.html", firebase_config=firebase_config)


@app.route("/saved")
def saved():
    return render_template("saved.html")

# This route is not currently used but is kept for completeness
@app.route("/view")
def view():
    return render_template("view.html")


# --- Start the app ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
