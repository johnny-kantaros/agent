import os
import uuid

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_API_URL = "https://connect-api.bayclubs.io"
SCOPE = "openid profile billing_api connectaccount_api connect_api messaging_api class_member_api childcare_member_api checkin_member_api membermanagement_member_api camps_member_api medicaldata_api payments_api event_notification_api calendar_api offline_access documents_member_api oms2_sales_api court_booking_member_api buddy_list_member_api package_management_member_api providers_member_api providers_calendar_member_api personal_training_member_api loyalty_programs_member_api payments_processor_member_api"


def minutes_to_time(minutes: int) -> str:
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"


class SquashService:
    CLUB_ID = "1f652dd9-805e-40d6-a7e5-1833f4dec942"
    CATEGORY_OPTIONS_ID = "9039b620-5243-4e71-9f5a-accb682a2c80"
    TIME_SLOT_ID = "584737a5-3484-4864-a6fb-ebe96b3ebe8c"
    AUTH_URL = "https://authentication2-api.bayclubs.io"

    def __init__(self):
        self.token = None
        self.username = os.getenv("BAYCLUB_USERNAME")
        self.password = os.getenv("BAYCLUB_PASSWORD")
        self.subscription_key = "bac44a2d04b04413b6aea6d4e3aad294"
        self.client = httpx.AsyncClient()

    def _headers(self):
        return {
            "Ocp-Apim-Subscription-Key": self.subscription_key,
            "User-Agent": "Mozilla/5.0",
            "Accept": "*/*",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://bayclubconnect.com/",
            "X-SessionId": str(uuid.uuid4()),
            "Request-Id": str(uuid.uuid4()),
        }

    async def _login(self) -> None:
        payload = (
            f"client_id=connect20"
            f"&client_secret=connectSecret"
            f"&grant_type=password"
            f"&username={self.username}"
            f"&password={self.password}"
            f"&scope={SCOPE}"
        )

        res = await self.client.post(
            f"{self.AUTH_URL}/connect/token",
            headers=self._headers(),
            content=payload,
        )

        print(res.status_code, res.text)  # keep for debugging

        res.raise_for_status()
        data = res.json()
        self.token = data["access_token"]

    async def get_availability(
        self,
        date: str,
        after_hour: int = 0,
        before_hour: int = 24,
    ):
        await self._login()
        res = await self.client.get(
            f"{BASE_API_URL}/court-booking/api/1.0/availability",
            headers={
                "Authorization": f"Bearer {self.token}",
                "Ocp-Apim-Subscription-Key": self.subscription_key,
            },
            params={
                "clubId": self.CLUB_ID,
                "date": date,
                "categoryCode": "squash",
                "categoryOptionsId": self.CATEGORY_OPTIONS_ID,
                "timeSlotId": self.TIME_SLOT_ID,
            },
        )

        res.raise_for_status()
        data = res.json()

        club_data = data["clubsAvailabilities"][0]

        # map courtId -> name
        court_map = {c["courtId"]: c["courtName"] for c in club_data["courts"]}

        slots = []

        for slot in club_data["availableTimeSlots"]:
            start_min = slot["fromInMinutes"]
            hour = start_min / 60

            if hour < after_hour or hour > before_hour:
                continue

            slots.append(
                {
                    "time": minutes_to_time(start_min),
                    "end_time": minutes_to_time(slot["toInMinutes"]),
                    "court_id": slot["courtId"],
                    "court": court_map.get(slot["courtId"], "Unknown"),
                    "time_of_day": slot["timeOfDay"],
                }
            )

        # sort by time (important for agent reasoning)
        slots.sort(key=lambda x: x["time"])
        return slots

    async def book_court(
        self,
        date: str,
        time_from: int,
        time_to: int,
        court_id: str,
        category_options_id: str,
        time_slot_id: str,
    ):
        await self._login()

        booking = await self._create_booking(
            date=date,
            time_from=time_from,
            time_to=time_to,
            court_id=court_id,
            category_options_id=category_options_id,
            time_slot_id=time_slot_id,
        )
        print("Booking created:", booking)

        temp_bookings = await self._get_temporary_bookings()
        print("Temporary bookings:", temp_bookings)

        if not temp_bookings.get("courtBookings"):
            raise ValueError("No temporary bookings found after creation")

        booking_id = temp_bookings["courtBookings"][0]["id"]

        confirmed = await self._confirm_booking(booking_id)
        print("Booking confirmed:", confirmed)

        return confirmed

    async def _create_booking(
        self,
        date: str,
        time_from: int,
        time_to: int,
        court_id: str,
        category_options_id: str,
        time_slot_id: str,
    ):

        payload = {
            "clubId": self.CLUB_ID,
            "date": {"value": date, "date": date},
            "timeFromInMinutes": time_from,
            "timeToInMinutes": time_to,
            "courtId": court_id,
            "categoryOptionsId": category_options_id,
            "timeSlotId": time_slot_id,
        }

        res = await self.client.post(
            f"{BASE_API_URL}/court-booking/api/1.0/courtbookings",
            headers=self._headers(),
            json=payload,
        )

        res.raise_for_status()
        return res.json()

    async def _get_temporary_bookings(self):
        res = await self.client.get(
            f"{BASE_API_URL}/court-booking/api/1.0/courtbookings/temporary",
            headers=self._headers(),
        )

        res.raise_for_status()
        return res.json()

    async def _confirm_booking(self, booking_id: str):

        res = await self.client.post(
            f"{BASE_API_URL}/court-booking/api/1.0/courtbookings/{booking_id}",
            headers=self._headers(),
        )

        res.raise_for_status()
        return res.json()


squash_service = SquashService()  # Global
