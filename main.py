from flask import Flask, request
import requests
from config import META_ACCESS_TOKEN, VERIFY_TOKEN, PHONE_NUMBER_ID
from utils import transcribe_audio, ask_gpt
import json

app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge')
        return 'Token mismatch', 403

    data = request.get_json()
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
        print("Errore:", e)

    return 'ok', 200

if __name__ == '__main__':
    app.run(port=5000)