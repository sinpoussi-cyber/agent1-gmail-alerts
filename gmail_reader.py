import os
import json
import base64
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from bs4 import BeautifulSoup

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_FILE = "token.json"


def _get_service():
    import json
    TOKEN_FILE = "token.json"
    SCOPES = ["https://mail.google.com/"]

    if not os.path.exists(TOKEN_FILE):
        raise FileNotFoundError("token.json introuvable. Lancez d'abord get_token.py")

    with open(TOKEN_FILE, "r") as f:
        token_data = json.load(f)

    creds = Credentials(
        token=token_data.get("token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=token_data.get("client_id"),
        client_secret=token_data.get("client_secret"),
        scopes=SCOPES
    )

    if creds.expired:
        creds.refresh(Request())
        token_data["token"] = creds.token
        with open(TOKEN_FILE, "w") as f:
            json.dump(token_data, f, indent=2)

    return build("gmail", "v1", credentials=creds)


def _extract_body_html(payload):
    """Recursively extract HTML body from a Gmail message payload."""
    if payload.get("mimeType") == "text/html":
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _extract_body_html(part)
        if result:
            return result

    return ""


def _extract_links(html):
    """Extract all http/https URLs from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for tag in soup.find_all("a", href=True):
        href = tag["href"]
        if href.startswith("http"):
            links.append(href)
    return links


def get_google_alerts():
    service = _get_service()

    result = service.users().messages().list(
        userId="me",
        q="from:googlealerts-noreply@google.com is:unread",
        maxResults=50,
    ).execute()

    messages = result.get("messages", [])
    alerts = []

    for msg_ref in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_ref["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        subject = headers.get("Subject", "")
        date = headers.get("Date", "")
        body_html = _extract_body_html(msg["payload"])
        links = _extract_links(body_html)

        alerts.append(
            {
                "id": msg["id"],
                "subject": subject,
                "date": date,
                "body_html": body_html,
                "links": links,
            }
        )

    return alerts


def delete_mail(mail_id):
    service = _get_service()
    service.users().messages().delete(userId="me", id=mail_id).execute()
