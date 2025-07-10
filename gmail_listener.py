from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from base64 import urlsafe_b64decode
from bs4 import BeautifulSoup
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

    def check_unread_emails(self, query, source):
        results = self.service.users().messages().list(
            userId='me',
            labelIds=['INBOX'],
            q=query
        ).execute()
        messages = results.get('messages', [])
        parsed_emails = []

        for msg in messages:
            msg_data = self.service.users().messages().get(
                userId='me',
                id=msg['id']
            ).execute()

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

    def extract_body(self, payload):
        """ ✅ FUNÇÃO AGORA GARANTIDA """
        if 'body' in payload and 'data' in payload['body']:
            raw_data = payload['body']['data']
            decoded = urlsafe_b64decode(raw_data).decode('utf-8')
            if payload.get('mimeType', '').startswith('text/html'):
                decoded = self.clean_html(decoded)
            return decoded

        if 'parts' in payload:
            for part in payload['parts']:
                result = self.extract_body(part)
                if result:
                    return result

        return ""

    def clean_html(self, raw_html):
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)

    def parse_shopify(self, body):
        parsed = {}

        produto_match = re.search(r'Resumo do pedido\s+([^\n\r]+)', body)
        if produto_match:
            parsed['produto'] = produto_match.group(1).strip()

        total_match = re.search(r'Total[\s\S]*?R\$ ([\d,]+)', body)
        if total_match:
            parsed['total'] = total_match.group(1).strip()

        nome_match = re.search(r'Endereço de entrega\s+([^\n\r]+)', body)
        if nome_match:
            parsed['nome'] = nome_match.group(1).strip()

        endereco_match = re.search(
            r'Endereço de entrega\s+[^\n\r]+\s+([\s\S]+?)\nBrasil',
            body
        )
        if endereco_match:
            parsed['endereco'] = endereco_match.group(1).strip()

        telefone_match = re.search(r'Brasil\s*\n([+\d]+)', body)
        if telefone_match:
            parsed['telefone'] = telefone_match.group(1).strip()

        return parsed

    def parse_hostinger(self, body):
        parsed = {}

        nome = re.search(r'Nome Completo\s*:\s*(.*)', body, re.IGNORECASE)
        if nome:
            parsed['nome_completo'] = nome.group(1).strip()

        whatsapp = re.search(r'Whats app\s*:\s*(.*)', body, re.IGNORECASE)
        if whatsapp:
            parsed['whatsapp'] = whatsapp.group(1).strip()

        rg = re.search(r'RG\s*:\s*(.*)', body, re.IGNORECASE)
        if rg:
            parsed['rg'] = rg.group(1).strip()

        cpf = re.search(r'CPF\s*:\s*(.*)', body, re.IGNORECASE)
        if cpf:
            parsed['cpf'] = cpf.group(1).strip()

        endereco = re.search(r'Endereço\s*:\s*(.*)', body, re.IGNORECASE)
        if endereco:
            parsed['endereco'] = endereco.group(1).strip()

        quantidade = re.search(r'Deseja automatizar quantas persianas\?\s*:\s*(.*)', body, re.IGNORECASE)
        if quantidade:
            parsed['quantidade_persianas'] = quantidade.group(1).strip()

        pagamento = re.search(r'Forma De Pagamento\?\s*:\s*(.*)', body, re.IGNORECASE)
        if pagamento:
            parsed['forma_pagamento'] = pagamento.group(1).strip()

        valor_manual = re.search(r'Instrução[^\n]*\n\s*:\s*([\d\.,]+)', body, re.IGNORECASE)
        if valor_manual:
            parsed['valor_unitario_manual'] = valor_manual.group(1).strip()

        return parsed







