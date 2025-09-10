from __future__ import annotations

from datetime import datetime
from typing import List, Dict
from zoneinfo import ZoneInfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from .config import GOOGLE_CLIENT_SECRETS_FILE, GOOGLE_TOKEN_FILE, DEFAULT_TIMEZONE

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def _get_credentials() -> Credentials:
    creds = None
    try:
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN_FILE, SCOPES)
    except Exception:
        creds = None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                GOOGLE_CLIENT_SECRETS_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0, prompt="consent")
        with open(GOOGLE_TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return creds


def get_service():
    creds = _get_credentials()
    service = build("calendar", "v3", credentials=creds)
    return service


def list_events_between(
    start_dt: datetime, end_dt: datetime, tz_name: str | None = None
) -> List[Dict]:
    tz = tz_name or DEFAULT_TIMEZONE
    start_iso = start_dt.astimezone(ZoneInfo(tz)).isoformat()
    end_iso = end_dt.astimezone(ZoneInfo(tz)).isoformat()

    service = get_service()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    return events


def add_event(
    summary: str,
    start_dt: datetime,
    end_dt: datetime,
    description: str = "",
    tz_name: str | None = None,
) -> dict:
    tz = tz_name or DEFAULT_TIMEZONE
    body = {
        "summary": summary,
        "description": description,
        "start": {
            "dateTime": start_dt.astimezone(ZoneInfo(tz)).isoformat(),
            "timeZone": tz,
        },
        "end": {
            "dateTime": end_dt.astimezone(ZoneInfo(tz)).isoformat(),
            "timeZone": tz,
        },
    }
    service = get_service()
    created = service.events().insert(calendarId="primary", body=body).execute()
    return created
