import urllib.request
import urllib.error
import json
import sys
from datetime import date, timedelta

from src.utils.constants import COURTS


class TennisService:

    def __init__(self):
        self.API_BASE = "https://api.rec.us/v1/locations"

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
                data = self._fetch_schedule(info["id"], day)
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

