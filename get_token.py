from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import json

SCOPES = ['https://mail.google.com/']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

token_data = {
    "token": creds.token,
    "refresh_token": creds.refresh_token,
    "token_uri": creds.token_uri,
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "scopes": list(creds.scopes) if creds.scopes else list(SCOPES),
    "universe_domain": "googleapis.com",
    "account": "",
    "expiry": None
}

with open("token.json", "w") as f:
    json.dump(token_data, f, indent=2)

print("token.json créé avec succès !")
print("GMAIL_REFRESH_TOKEN =", creds.refresh_token)