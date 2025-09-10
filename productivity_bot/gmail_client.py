from __future__ import annotations
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from googleapiclient.discovery import build
from .google_calendar import _get_credentials

def send_report_email(to_email: str, subject: str, body: str, attachments: list[str] = None):
    """
    Send an email with optional file attachments using Gmail API.
    """
    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEMultipart()
    message["to"] = to_email
    message["subject"] = subject

    # Email body
    message.attach(MIMEText(body, "plain"))

    # Attach files (Excel, PNG)
    if attachments:
        for filepath in attachments:
            with open(filepath, "rb") as f:
                part = MIMEApplication(f.read(), Name=filepath.split("/")[-1])
                part["Content-Disposition"] = f'attachment; filename="{filepath.split("/")[-1]}"'
                message.attach(part)

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

    sent = (
        service.users()
        .messages()
        .send(userId="me", body={"raw": raw})
        .execute()
    )
    return sent
