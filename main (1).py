
from flask import Flask, request
import requests
import json
from config import META_ACCESS_TOKEN, VERIFY_TOKEN, PHONE_NUMBER_ID
from utils import transcribe_audio, ask_gpt

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")

        print(f"GET /webhook called with token={verify_token}, mode={mode}")

        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token mismatch", 403

    if request.method == "POST":
        data = request.get_json()
        print("POST /webhook - Incoming data:")
        print(json.dumps(data, indent=2))

        try:
            msg_type = data['entry'][0]['changes'][0]['value']['messages'][0]['type']
            from_number = data['entry'][0]['changes'][0]['value']['messages'][0]['from']

            if msg_type == 'text':
                text = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
            elif msg_type == 'audio':
                media_id = data['entry'][0]['changes'][0]['value']['messages'][0]['audio']['id']
                media_url = f"https://graph.facebook.com/v17.0/{media_id}"
                headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
                media_response = requests.get(media_url, headers=headers)
                audio_url = media_response.json()['url']
                audio_data = requests.get(audio_url, headers=headers).content
                text = transcribe_audio(audio_data)
            else:
                text = "Tipo di messaggio non supportato."

            reply = ask_gpt(text)

            send_url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
            payload = {
                "messaging_product": "whatsapp",
                "to": from_number,
                "type": "text",
                "text": {"body": reply}
            }
            requests.post(send_url, headers={"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}, json=payload)

        except Exception as e:
            print("Errore nella gestione del messaggio:", e)

        return "ok", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
