import urllib.request
import urllib.error
import json
import sys
from datetime import date, timedelta
from src.utils.constants import TENNIS_LOGIN_URL, TENNIS_BASE_API_URL, TENNIS_2FAC_SEND_URL, TENNIS_2FAC_VERIFY_URL
import requests
from src.utils.constants import COURTS
import os

from dotenv import load_dotenv

load_dotenv()


class TennisService:

    def __init__(self):
        self.API_BASE = "https://api.rec.us/v1/locations"
        self.API_KEY = os.getenv("TENNIS_API_KEY")
        self.PARTICIPANT_ID = os.getenv("TENNIS_PARTICIPANT_ID")
        self.token = None # Store auth token for session here, will need to store in redis eventually

    def init_reservation(
            self,
            court_number: str,
            court_name: str,
            date: str,
            start_time: str,
            end_time: str,
    ):
        self._login()
        url = f"{TENNIS_BASE_API_URL}/reservations"

        court_sport_id = COURTS[court_name]["courts"][court_number]["court_sport_id"]

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        payload = {
            "courtSportIds": [court_sport_id],
            "flow": "cart",
            "participantUserId": self.PARTICIPANT_ID,
            "from": {
                "date": date,
                "time": start_time
            },
            "to": {
                "date": date,
                "time": end_time
            }
        }

        r = requests.post(url, json=payload, headers=headers)
        r.raise_for_status()

        self._send_2fac_code()

        return r.json()

    def _send_2fac_code(self):

        url = TENNIS_2FAC_SEND_URL

        headers = {
            "Authorization": f"Bearer {self.token}",  # your auth token
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return None

    def _verify_2fac_code(self, code):
        url = TENNIS_2FAC_VERIFY_URL
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "code": code
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True


    def _login(self) -> str:

        url = f"{TENNIS_LOGIN_URL}{self.API_KEY}"

        payload = {
            "email": os.getenv("TENNIS_LOGIN_EMAIL"),
            "password": os.getenv("TENNIS_LOGIN_PASSWORD"),
            "returnSecureToken": True
        }

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.rec.us",
            "Referer": "https://www.rec.us/"
        }

        r = requests.post(url, json=payload, headers=headers)
        r.raise_for_status()

        data = r.json()

        self.token = data["idToken"]

    def _resolve_courts(self, court_query: str | None) -> dict:
        """
        Map an LLM-provided court name to COURTS entries.
        Supports:
        - "courts", "all", None -> all courts
        - partial matches like "marble"
        """
        if not court_query:
            return COURTS

        q = court_query.lower().strip()

        if q in {"courts", "all"}:
            return COURTS

        matched = {
            name: info
            for name, info in COURTS.items()
            if q in name.lower()
        }

        return matched

    def _fetch_schedule(self, location_id: str, day: date) -> dict:
        url = f"{self.API_BASE}/{location_id}/schedule?startDate={day.strftime('%Y-%m-%d')}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code}: {url}", file=sys.stderr)
            return {}
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)
            return {}

    def _parse_slots(self, schedule_data: dict, day: date) -> list[dict]:
        day_key = day.strftime("%Y%m%d")
        courts_data = schedule_data.get("dates", {}).get(day_key, [])
        slots = []
        for court in courts_data:
            court_number = court.get("courtNumber", "Court ?")
            for time_range, info in court.get("schedule", {}).items():
                if info.get("referenceType") == "RESERVABLE":
                    start_str, end_str = time_range.split(", ")
                    start_h, start_m = map(int, start_str.split(":"))
                    end_h, end_m = map(int, end_str.split(":"))
                    duration = (end_h * 60 + end_m) - (start_h * 60 + start_m)
                    slots.append({
                        "court_number": court_number,
                        "start": start_str,
                        "end": end_str,
                        "start_hour": start_h + start_m / 60,
                        "duration_min": duration,
                    })
        return sorted(slots, key=lambda s: s["start_hour"])

    def check_availability(
            self,
            courts: list[str],
            days: int = 7,
            after_hour: float = 0,
            before_hour: float = 24,
    ) -> dict:
        """
        Check availability for one or more courts.

        Args:
            courts: List of court names to check (e.g., ["Alice Marble", "Moscone"])
                    Use ["all"] to check all courts.
            days: Number of days ahead to check
            after_hour: Only include slots after this hour
            before_hour: Only include slots before this hour

        Returns:
            Structured availability results
        """

        selected_courts = {
            name: info
            for name, info in COURTS.items()
            if any(query.lower() in name.lower() for query in courts)
        }

        today = date.today()
        dates = [today + timedelta(days=i) for i in range(days)]

        results: dict = {}

        for name, info in selected_courts.items():
            court_results = []

            for day in dates:
                data = self._fetch_schedule(info["location_id"], day)
                slots = self._parse_slots(data, day)

                # Filter by time window
                slots = [
                    s for s in slots
                    if after_hour <= s["start_hour"] < before_hour
                ]

                if slots:
                    court_results.append({
                        "date": day.isoformat(),
                        "slots": slots
                    })

            if court_results:
                results[name] = {
                    "slug": info["slug"],
                    "availability": court_results
                }

        return results

