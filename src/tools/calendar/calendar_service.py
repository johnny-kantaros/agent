import os
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()


SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self):
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not cred_path:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set")

        self.credentials = Credentials.from_service_account_file(
            cred_path,
            scopes=SCOPES,
        )
        self.service = build("calendar", "v3", credentials=self.credentials)
        self.calendar_id = os.getenv("CALENDAR_ID")

    def create_event(
        self,
        title: str,
        start_time: str,
        end_time: str | None = None,
        duration_minutes: int | None = None,
        location: str | None = None,
        description: str | None = None,
        attendees: list[str] | None = None,
        timezone: str = "America/Los_Angeles",
    ) -> dict:

        tz = ZoneInfo(timezone)
        start_dt = datetime.fromisoformat(start_time).replace(tzinfo=tz)

        if end_time:
            end_dt = datetime.fromisoformat(end_time).replace(tzinfo=tz)
        elif duration_minutes is not None:
            end_dt = start_dt + timedelta(minutes=duration_minutes)
        else:
            raise ValueError("Provide end_time or duration_minutes")

        event: dict[str, Any] = {
            "summary": title,
            "start": {
                "dateTime": start_dt.isoformat(),
                "timeZone": timezone,
            },
            "end": {
                "dateTime": end_dt.isoformat(),
                "timeZone": timezone,
            },
        }

        if location:
            event["location"] = location

        if description:
            event["description"] = description

        if attendees:
            event["attendees"] = [{"email": email} for email in attendees]

        try:
            created_event = (
                self.service.events().insert(calendarId=self.calendar_id, body=event).execute()
            )
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

        start = created_event["start"].get("dateTime") or created_event["start"].get("date")
        end = created_event["end"].get("dateTime") or created_event["end"].get("date")

        return {
            "status": "confirmed",
            "event_id": created_event.get("id"),
            "html_link": created_event.get("htmlLink"),
            "start_time": start,
            "end_time": end,
        }


calendar_service = CalendarService()  # Global
