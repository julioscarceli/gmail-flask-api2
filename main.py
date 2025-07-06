from flask import Flask, jsonify
from gmail_listener import GmailListener
import os

app = Flask(__name__)
gmail_listener = GmailListener()

@app.route("/listen-emails", methods=["GET"])
def listen_emails():
    emails = gmail_listener.check_unread_emails()
    return jsonify(emails)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))