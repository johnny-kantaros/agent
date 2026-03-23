import base64
import json
import os
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

load_dotenv()


SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarService:
    def __init__(self):
        cred_b64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON_B64")
        if not cred_b64:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS_JSON_B64 not set")

        creds_dict = json.loads(base64.b64decode(cred_b64).decode("utf-8"))
        credentials = Credentials.from_service_account_info(creds_dict)
        self.service = build("calendar", "v3", credentials=credentials)

        self.calendar_id = os.getenv("CALENDAR_ID")
        if not self.calendar_id:
            raise ValueError("CALENDAR_ID not set")

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

    def list_events(
        self,
        time_min: str | None = None,
        time_max: str | None = None,
        query: str | None = None,
        max_results: int = 50,
    ) -> list[dict]:

        # defaults to today → 7 days ahead
        if not time_min:
            time_min_dt = datetime.now(UTC)
            time_min = time_min_dt.isoformat() + "Z"

        if not time_max:
            time_max_dt = datetime.now(UTC) + timedelta(days=7)
            time_max = time_max_dt.isoformat() + "Z"

        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                q=query,
                singleEvents=True,
                orderBy="startTime",
                maxResults=max_results,
            )
            .execute()
        )

        return events_result.get("items", [])

    def check_availability(
        self,
        start_time: str,
        end_time: str,
    ) -> dict:

        events = self.list_events(
            time_min=start_time,
            time_max=end_time,
        )

        if events:
            conflicts = [
                {
                    "title": ev.get("summary"),
                    "start": ev["start"].get("dateTime") or ev["start"].get("date"),
                    "end": ev["end"].get("dateTime") or ev["end"].get("date"),
                }
                for ev in events
            ]
            return {"available": False, "conflicts": conflicts}

        return {"available": True, "conflicts": []}

    def find_time_slot(
        self,
        duration_minutes: int,
        start_range: str,
        end_range: str,
        step_minutes: int = 15,
    ) -> dict:
        """
        Suggests the next available time slot of given duration
        within a time range.
        """
        start_dt = datetime.fromisoformat(start_range)
        end_dt = datetime.fromisoformat(end_range)
        delta = timedelta(minutes=step_minutes)
        duration = timedelta(minutes=duration_minutes)

        current_start = start_dt
        while current_start + duration <= end_dt:
            current_end = current_start + duration
            avail = self.check_availability(
                start_time=current_start.isoformat(),
                end_time=current_end.isoformat(),
            )
            if avail["available"]:
                return {
                    "start_time": current_start.isoformat(),
                    "end_time": current_end.isoformat(),
                }
            current_start += delta

        return {"available": False, "message": "No slot available in range"}


calendar_service = CalendarService()  # Global
