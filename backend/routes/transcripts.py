import os
import certifi
import json # Import the json library
from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from groq import Groq
from dotenv import load_dotenv
from firebase_auth import verify_firebase_token
from google.cloud import vision 
from google.oauth2 import service_account # Import the service_account module

# --- Initialize Clients ---
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

ca = certifi.where()
client = MongoClient(MONGO_URI, tlsCAFile=ca)
db = client.get_database("Mednote")
collection = db["transcripts"]
groq_client = Groq(api_key=GROQ_API_KEY)


# --- SECURE VISION CLIENT INITIALIZATION ---
creds_json_str = os.getenv("FIREBASE_CREDENTIAL_JSON")

if creds_json_str:
    # In production (Render), load credentials from the environment variable
    creds_info = json.loads(creds_json_str)
    credentials = service_account.Credentials.from_service_account_info(creds_info)
else:
    # In local development, load credentials from the file
    SERVICE_ACCOUNT_FILE = 'serviceAccountKey.json'
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

vision_client = vision.ImageAnnotatorClient(credentials=credentials)


bp = Blueprint("transcripts", __name__)

# --- NEW: Extract Text from Image Route ---
@bp.route("/extract-from-image", methods=["POST"])
@verify_firebase_token
def extract_from_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    
    try:
        content = image_file.read()
        image = vision.Image(content=content)
        response = vision_client.document_text_detection(image=image)
        
        if response.error.message:
            raise Exception(response.error.message)

        return jsonify({"text": response.full_text_annotation.text})

    except Exception as e:
        print(f"❌ OCR Error: {e}")
        return jsonify({"error": "Failed to extract text from image."}), 500


# --- Save Transcript ---
@bp.route("/save", methods=["POST"])
@verify_firebase_token
def save_transcript():
    user = request.user
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    result = collection.insert_one({
        "name": data.get("name"),
        "content": data.get("content"),
        "timestamp": data.get("timestamp"),
        "summary": "",
        "user_id": user.get("uid"),
        "phone": user.get("phone_number")
    })
    return jsonify({"status": "Saved", "id": str(result.inserted_id)}), 200


# --- List Transcripts ---
@bp.route("/list", methods=["GET"])
@verify_firebase_token
def list_transcripts():
    user = request.user
    docs = []
    try:
        # Sort by timestamp descending to get newest first
        cursor = collection.find({"user_id": user.get("uid")})
        for doc in cursor:
            docs.append({
                "id": str(doc["_id"]),
                "name": doc.get("name"),
                "content": doc.get("content"),
                "summary": doc.get("summary", ""),
                "timestamp": doc.get("timestamp")
            })
        return jsonify(docs)
    except Exception as e:
        print(f"❌ Error listing transcripts: {e}")
        return jsonify({"error": "Could not retrieve transcripts"}), 500


# --- Summarize Transcript ---
@bp.route("/summarize", methods=["POST"])
@verify_firebase_token
def summarize():
    user = request.user
    data = request.json
    content = data.get("content", "")
    doc_id = data.get("id", "")

    if not content or not doc_id:
        return jsonify({"error": "Missing content or transcript ID"}), 400

    existing = collection.find_one({"_id": ObjectId(doc_id), "user_id": user["uid"]})
    if not existing:
        return jsonify({"error": "Transcript not found or access denied"}), 403

    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are MedNote, an expert assistant trained in psychotherapy session summarization..."
                },
                {
                    "role": "user",
                    "content": f"Here is the full transcript:\n\n{content}\n\nGenerate a structured summary."
                }
            ],
            model="llama3-8b-8192",
            temperature=0.7,
        )
        summary = chat_completion.choices[0].message.content

        collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"summary": summary}}
        )
        return jsonify({"summary": summary})
    except Exception as e:
        print(f"❌ Summary generation failed: {e}")
        return jsonify({"error": "Failed to generate summary"}), 500


# --- Get Single Transcript ---
@bp.route("/get/<id>", methods=["GET"])
@verify_firebase_token
def get_transcript(id):
    user = request.user
    try:
        doc = collection.find_one({"_id": ObjectId(id), "user_id": user["uid"]})
        if doc:
            doc["_id"] = str(doc["_id"])
            return jsonify(doc)
        else:
            return jsonify({"error": "Transcript not found or access denied"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Update Transcript Content ---
@bp.route("/update/<id>", methods=["POST"])
@verify_firebase_token
def update_transcript(id):
    user = request.user
    data = request.json
    new_content = data.get("content")

    if new_content is None:
        return jsonify({"error": "No content provided"}), 400

    try:
        result = collection.update_one(
            {"_id": ObjectId(id), "user_id": user["uid"]},
            {"$set": {"content": new_content}}
        )
        if result.matched_count == 1:
            return jsonify({"success": True, "message": "Transcript updated."})
        else:
            return jsonify({"error": "Transcript not found or access denied"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Delete Transcript ---
@bp.route("/delete/<id>", methods=["DELETE"])
@verify_firebase_token
def delete_transcript(id):
    user = request.user
    try:
        result = collection.delete_one({"_id": ObjectId(id), "user_id": user["uid"]})
        if result.deleted_count == 1:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Transcript not found or access denied"}), 404
    except Exception as e:
        print(f"❌ Error deleting transcript: {e}")
        return jsonify({"success": False, "error": "Could not delete transcript"}), 500
