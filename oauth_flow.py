# Script para gerar o refresh_token

from google_auth_oauthlib.flow import InstalledAppFlow

def main():
    # 1️⃣ Inicia o fluxo
    flow = InstalledAppFlow.from_client_secrets_file(
        'client_secret.json',  # Caminho do seu JSON
        scopes=['https://mail.google.com/']
    )

    # 2️⃣ Executa o servidor local FORÇANDO a porta 8000
    creds = flow.run_local_server(port=8000)

    # 3️⃣ Mostra o refresh_token gerado
    print('ACCESS TOKEN:', creds.token)
    print('REFRESH TOKEN:', creds.refresh_token)

if __name__ == '__main__':
    main()
