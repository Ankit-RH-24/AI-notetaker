from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from bson import ObjectId
from firebase_auth import verify_firebase_token
import requests
import os
from dotenv import load_dotenv
from groq import Groq

# --- Setup ---
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

bp = Blueprint("transcripts", __name__)

# --- MongoDB Setup ---
MONGO_URI = "mongodb+srv://mednote_user:mednote_pass123@mednote.scgdktg.mongodb.net/mednote?retryWrites=true&w=majority&appName=MedNote"
client = MongoClient(MONGO_URI)
db = client["Mednote"]
collection = db["transcripts"]

# --- Save Transcript (requires auth) ---
@bp.route("/api/transcripts/save", methods=["POST"])
def save_transcript():
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

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

# --- List Transcripts for Logged-in User ---
@bp.route("/list", methods=["GET"])
def list_transcripts():
    user = verify_firebase_token(request)  # ✅ FIXED
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    docs = []
    for doc in collection.find({"user_id": user.get("uid")}):
        docs.append({
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "content": doc.get("content"),
            "summary": doc.get("summary", ""),
            "timestamp": doc.get("timestamp")
        })
    return jsonify(docs)
# --- Summarize Transcript ---
@bp.route("/summarize", methods=["POST"])
def summarize():
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    content = data.get("content", "")
    doc_id = data.get("id", "")

    if not content or not doc_id:
        return jsonify({"error": "Missing content or transcript ID"}), 400

    existing = collection.find_one({"_id": ObjectId(doc_id), "user_id": user["uid"]})
    if not existing:
        return jsonify({"error": "Transcript not found or access denied"}), 403

    try:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are MedNote, an expert assistant trained in psychotherapy session summarization.\n"
                        "Your role is to analyze conversations between a therapist and a client, and create a structured, professional summary for therapists.\n\n"
                        "Summarize the session using the following sections:\n"
                        "- **Client's Main Concern**\n"
                        "- **Session Highlights** (key topics discussed, emotional tone, important events)\n"
                        "- **Therapist's Observations** (insights, patterns, shifts in mood or behavior)\n"
                        "- **Plan / Follow-up** (what was agreed, goals, next steps)\n\n"
                        "Only include clinically relevant content. Use clear, empathetic, and professional language.\n"
                        "Avoid small talk or irrelevant chatter. Frame from the therapist's perspective."
                    )
                },
                {
                    "role": "user",
                    "content": f"Here is the full transcript of a therapy session:\n\n{content}\n\nPlease generate a structured summary."
                }
            ],
            "temperature": 0.7
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            print("❌ Groq API error:", response.text)
            return jsonify({"error": "Groq API failed"}), 500

        result = response.json()
        summary = result["choices"][0]["message"]["content"]

        collection.update_one(
            {"_id": ObjectId(doc_id)},
            {"$set": {"summary": summary}}
        )

        return jsonify({"summary": summary})
    except Exception as e:
        print("❌ Summary generation failed:", e)
        return jsonify({"error": str(e)}), 500

# --- Delete Transcript ---
@bp.route("/delete/<id>", methods=["DELETE"])
def delete_transcript(id):
    user = verify_firebase_token(request)
    if not user:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        result = collection.delete_one({"_id": ObjectId(id), "user_id": user["uid"]})
        if result.deleted_count == 1:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": "Transcript not found or access denied"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
