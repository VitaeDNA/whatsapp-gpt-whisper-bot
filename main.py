from flask import Flask, request, jsonify
import requests
import os
from utils import transcribe_audio, ask_gpt

app = Flask(__name__)

# Carica le variabili d'ambiente
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token non valido", 403

    if request.method == "POST":
        data = request.get_json()
        # Gestisci il messaggio ricevuto
        # ...
        return "ok", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
