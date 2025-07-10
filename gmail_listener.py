from tenacity import retry, stop_after_attempt, wait_exponential
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
import re

from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN


class GmailListener:
    def __init__(self):
        self.refresh_service()

    def refresh_service(self):
        """Cria nova instância da API — isso força revalidação do token"""
        self.creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token'
        )
        self.service = build('gmail', 'v1', credentials=self.creds)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=2, max=30))
    def check_unread_emails(self, query, source):
        try:
            results = self.service.users().messages().list(
                userId='me',
                labelIds=['INBOX'],
                q=query
            ).execute()
        except Exception as e:
            print(f"❌ Erro na API, tentando recriar serviço → {e}")
            self.refresh_service()
            raise  # força retry do tenacity

        messages = results.get('messages', [])
        parsed_emails = []

        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

            body = self.extract_body(msg_data['payload'])

            if source == "shopify":
                parsed = self.parse_shopify(body)
            elif source == "hostinger":
                parsed = self.parse_hostinger(body)
            else:
                parsed = {}

            parsed.update({
                'from': from_email,
                'subject': subject,
                'message_id': msg['id']
            })

            parsed_emails.append(parsed)

        return parsed_emails

    # ⚙️ Restante do código continua IGUAL






