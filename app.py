# app.py — kept for Heroku / gunicorn compatibility but the real web server
# is the aiohttp one started inside bot/__main__.py.
# This file is intentionally minimal.
import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET", "HEAD"])
def index():
    return jsonify({"status": "ok", "note": "Use /health for live bot status"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
