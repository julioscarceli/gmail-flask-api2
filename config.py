# Configurações (carrega variáveis de ambiente)


import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("REFRESH_TOKEN")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")