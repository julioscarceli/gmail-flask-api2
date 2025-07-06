from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode
import re

from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN

class GmailListener:
    def __init__(self):
        self.creds = Credentials(
            None,
            refresh_token=REFRESH_TOKEN,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            token_uri='https://oauth2.googleapis.com/token'
        )
        self.service = build('gmail', 'v1', credentials=self.creds)

    def check_unread_emails(self):
        # ⚡ Filtra só emails do remetente Shopify
        query = 'is:unread from:store+69351243823@t.shopifyemail.com'
        results = self.service.users().messages().list(userId='me', labelIds=['INBOX'], q=query).execute()
        messages = results.get('messages', [])
        parsed_emails = []

        for msg in messages:
            msg_data = self.service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')

            # 📌 Lê o body em texto puro (partes 'text/plain')
            body = ""
            payload = msg_data['payload']
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        data = part['body']['data']
                        body = urlsafe_b64decode(data).decode('utf-8')
            else:
                # fallback se não tiver partes
                data = payload['body']['data']
                body = urlsafe_b64decode(data).decode('utf-8')

            # 🔍 Parser para extrair dados estruturados
            parsed = self.parse_email_content(body)
            parsed.update({
                'from': from_email,
                'subject': subject
            })

            parsed_emails.append(parsed)

        return parsed_emails

    def parse_email_content(self, body):
        """
        Extrai produto, total, nome, endereço e telefone.
        """
        parsed = {}

        # Produto
        produto_match = re.search(r'Resumo do pedido\s+([^\n\r]+)', body)
        if produto_match:
            parsed['produto'] = produto_match.group(1).strip()

        # Total final
        total_match = re.search(r'Total[\s\S]*?R\$ ([\d,]+)', body)
        if total_match:
            parsed['total'] = total_match.group(1).strip()

        # Nome do cliente
        nome_match = re.search(r'Endereço de entrega\s+([^\n\r]+)', body)
        if nome_match:
            parsed['nome'] = nome_match.group(1).strip()

        # Endereço (do nome até Brasil)
        endereco_match = re.search(
            r'Endereço de entrega\s+[^\n\r]+\s+([\s\S]+?)\nBrasil',
            body
        )
        if endereco_match:
            endereco = endereco_match.group(1).strip()
            parsed['endereco'] = endereco

        # Telefone — logo após Brasil
        telefone_match = re.search(r'Brasil\s*\n([+\d]+)', body)
        if telefone_match:
            parsed['telefone'] = telefone_match.group(1).strip()

        return parsed
