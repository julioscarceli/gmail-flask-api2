import os
import threading
import time
import requests
import json
from flask import Flask, jsonify
from gmail_listener import GmailListener

app = Flask(__name__)

WEBHOOK_A = os.getenv("N8N_WEBHOOK_URL_A")
WEBHOOK_B = os.getenv("N8N_WEBHOOK_URL_B")

QUERY_A = 'is:unread from:store+69351243823@t.shopifyemail.com'
QUERY_B = 'is:unread from:automatikpersianas-com@notifications.hostinger.com'

def loop_checker(query, webhook_url, source):
    gmail_listener = GmailListener()

    while True:
        try:
            emails = gmail_listener.check_unread_emails(query, source)
            print(f"\n📬 Verificando [{source}]... Emails encontrados: {len(emails)}\n")

            for email in emails:
                print(f"🚀 Enviando para o n8n [{source}] → {webhook_url}")
                print(json.dumps(email, indent=4, ensure_ascii=False))
                try:
                    res = requests.post(webhook_url, json=email)
                    print(f"✅ n8n respondeu: {res.status_code} - {res.text}")

                    if res.status_code == 200:
                        gmail_listener.service.users().messages().modify(
                            userId='me',
                            id=email['message_id'],
                            body={'removeLabelIds': ['UNREAD']}
                        ).execute()
                        print(f"📌 Marcado como lido: {email['message_id']}\n")
                    else:
                        print("⚠️ n8n respondeu com erro, não marcado como lido\n")

                except Exception as e:
                    print(f"❌ Erro ao enviar para n8n: {e}\n")

        except Exception as e:
            print(f"⚠️ Falha geral no loop: {e}")
            print("⏳ Aguardando 30s antes de tentar de novo...")
            time.sleep(30)

        time.sleep(30)


@app.route("/listen-emails", methods=["GET"])
def listen_emails():
    return jsonify({"status": "running"})

if __name__ == "__main__":
    threading.Thread(target=loop_checker, args=(QUERY_A, WEBHOOK_A, "shopify"), daemon=True).start()
    threading.Thread(target=loop_checker, args=(QUERY_B, WEBHOOK_B, "hostinger"), daemon=True).start()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
