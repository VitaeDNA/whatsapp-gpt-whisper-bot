from flask import Flask, request
import requests
import json
import traceback
from config import META_ACCESS_TOKEN, VERIFY_TOKEN, PHONE_NUMBER_ID
from utils import transcribe_audio, ask_gpt
from openai import OpenAI

app = Flask(__name__)

# Inizializza il client OpenAI
openai_client = OpenAI(api_key='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')

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        verify_token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        mode = request.args.get("hub.mode")

        app.logger.info(f"GET /webhook chiamato con token={verify_token}, mode={mode}")

        if verify_token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return "Token non valido", 403

    if request.method == "POST":
        data = request.get_json()
        app.logger.info("POST /webhook - Dati in arrivo:")
        app.logger.info(json.dumps(data, indent=2))

        try:
            # Verifica che il payload contenga i dati attesi
            if 'entry' in data and data['entry']:
                changes = data['entry'][0].get('changes', [])
                if changes:
                    messages = changes[0]['value'].get('messages', [])
                    if messages:
                        msg = messages[0]
                        msg_type = msg.get('type')
                        from_number = msg.get('from')

                        if msg_type == 'text':
                            text = msg['text']['body']
                        elif msg_type == 'audio':
                            media_id = msg['audio']['id']
                            media_url = f"https://graph.facebook.com/v17.0/{media_id}"
                            headers = {"Authorization": f"Bearer {META_ACCESS_TOKEN}"}
                            media_response = requests.get(media_url, headers=headers)
                            audio_url = media_response.json().get('url')
                            audio_data = requests.get(audio_url, headers=headers).content
                            text = transcribe_audio(audio_data)
                        else:
                            text = "Tipo di messaggio non supportato."

                        # Utilizza il client OpenAI per ottenere la risposta
                        response = openai_client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": text}]
                        )
                        reply = response.choices[0].message.content.strip()

                        send_url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
                        payload = {
                            "messaging_product": "whatsapp",
                            "to": from_number,
                            "type": "text",
                            "text": {"body": reply}
                        }
                        response = requests.post(send_url, headers={"Authorization": f"Bearer {META_ACCESS_TOKEN}", "Content-Type": "application/json"}, json=payload)
                        app.logger.info(f"Risposta dall'API di WhatsApp: {response.status_code} - {response.text}")

        except Exception as e:
            app.logger.error("Errore nella gestione del messaggio:")
            app.logger.error(traceback.format_exc())

        return "ok", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
