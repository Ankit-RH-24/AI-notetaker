#!/bin/bash

echo "✅ Writing Firebase credential JSON to file..."

if [ -z "$FIREBASE_CREDENTIAL_JSON" ]; then
  echo "❌ FIREBASE_CREDENTIAL_JSON is not set!"
  exit 1
fi

echo "$FIREBASE_CREDENTIAL_JSON" > firebase-credentials.json

# Optional: Add newline to make sure it's parsed properly
echo "" >> firebase-credentials.json

echo "✅ Firebase credentials written to firebase-credentials.json"

# Start your Flask app using Gunicorn
exec gunicorn app:app --bind 0.0.0.0:$PORT
