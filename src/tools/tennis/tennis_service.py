import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

from src.utils.constants import (
    COURTS,
    TENNIS_2FAC_SEND_URL,
    TENNIS_2FAC_VERIFY_URL,
    TENNIS_LOGIN_URL,
)

load_dotenv()


class TennisService:
    def __init__(self):
        self.API_BASE = "https://api.rec.us/v1"
        self.API_KEY = os.getenv("TENNIS_API_KEY")
        self.PARTICIPANT_ID = os.getenv("TENNIS_PARTICIPANT_ID")

        self.token = None
        self.order_id = None
        self.order_item_id = None
        self.amount_cents = None

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def init_reservation(
        self,
        court_number: str,
        court_name: str,
        date: str,
        start_time: str,
        end_time: str,
    ):

        self._login()

        url = f"{self.API_BASE}/reservations"

        court_sport_id: str = COURTS[court_name]["courts"][court_number]["court_sport_id"]

        payload = {
            "courtSportIds": [court_sport_id],
            "flow": "cart",
            "participantUserId": self.PARTICIPANT_ID,
            "from": {"date": date, "time": start_time},
            "to": {"date": date, "time": end_time},
        }

        r = requests.post(url, json=payload, headers=self._headers())
        r.raise_for_status()

        data = r.json()

        order = data["data"]
        item = order["items"][0]

        self.order_id = order["id"]
        self.order_item_id = item["id"]
        self.amount_cents = item["finalPrice"]

        reservation_id = item["details"]["reservationId"]

        self._send_2fac_code()

        return {"reservation_id": reservation_id, "order_id": self.order_id}

    def confirm_reservation(self, confirmation_code: str):

        self._verify_2fac_code(confirmation_code)

        payment_data = self._initialize_payment()

        # Load saved payment method from env
        payment_method_id = os.getenv("STRIPE_PAYMENT_METHOD_ID")
        if not payment_method_id:
            raise RuntimeError("Saved Stripe payment method ID not set in STRIPE_PAYMENT_METHOD_ID")

        result = self._confirm_payment_intent(payment_data, payment_method_id)
        return result

    def _initialize_payment(self):

        url = f"{self.API_BASE}/orders/{self.order_id}/pay"

        payload = {
            "payments": [
                {
                    "paymentMethodType": "card-online",
                    "amountCents": self.amount_cents,
                }
            ],
            "distributions": {self.order_item_id: self.amount_cents},
            "source": "retail",
        }

        r = requests.post(url, headers=self._headers(), json={"data": payload})

        r.raise_for_status()

        data = r.json()
        payment = data["included"]["payments"][0]

        return {
            "payment_intent_id": payment["gatewayData"]["paymentIntentId"],
            "client_secret": payment["gatewayData"]["clientSecret"],
        }

    def _confirm_payment_intent(self, payment_data, payment_method_id: str):

        url = (
            f"https://api.stripe.com/v1/payment_intents/{payment_data['payment_intent_id']}/confirm"
        )

        payload = {
            "payment_method": payment_method_id,
            "expected_payment_method_type": "card",
            "use_stripe_sdk": "true",
            "key": os.getenv("STRIPE_PK"),
            "client_secret": payment_data["client_secret"],
        }

        r = requests.post(
            url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data=payload,
        )

        r.raise_for_status()
        result = r.json()

        if result.get("status") not in ["succeeded", "processing"]:
            raise RuntimeError(f"Stripe payment failed: {result}")

        return result

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
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        payload = {"code": code}
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True

    def _login(self) -> None:

        url = f"{TENNIS_LOGIN_URL}{self.API_KEY}"

        payload = {
            "email": os.getenv("TENNIS_LOGIN_EMAIL"),
            "password": os.getenv("TENNIS_LOGIN_PASSWORD"),
            "returnSecureToken": True,
        }

        headers = {
            "Content-Type": "application/json",
            "Origin": "https://www.rec.us",
            "Referer": "https://www.rec.us/",
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

        matched = {name: info for name, info in COURTS.items() if q in name.lower()}

        return matched

    def _fetch_schedule(self, location_id: str, day: date) -> dict:
        url = (
            f"{self.API_BASE}/locations/{location_id}/schedule?startDate={day.strftime('%Y-%m-%d')}"
        )
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
                    slots.append(
                        {
                            "court_number": court_number,
                            "start": start_str,
                            "end": end_str,
                            "start_hour": start_h + start_m / 60,
                            "duration_min": duration,
                        }
                    )
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
                slots = [s for s in slots if after_hour <= s["start_hour"] < before_hour]

                if slots:
                    court_results.append({"date": day.isoformat(), "slots": slots})

            if court_results:
                results[name] = {"slug": info["slug"], "availability": court_results}

        return results


tennis_service = TennisService()  # Global
