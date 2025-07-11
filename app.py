from flask import Flask, render_template
from flask_cors import CORS
from backend.routes.transcripts import bp as transcripts_bp
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Register API routes
app.register_blueprint(transcripts_bp, url_prefix="/api/transcripts")

# UI routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/saved")
def saved():
    return render_template("saved.html")

@app.route("/view")
def view():
    return render_template("view.html")

@app.route("/login")
def login():
    return render_template("login.html")

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=True)
