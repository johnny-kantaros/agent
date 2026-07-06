import asyncio
import os
from functools import partial

from serpapi import GoogleSearch


class FlightService:
    def __init__(self):
        self.api_key = os.environ.get("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY is not set")

    def search(
        self,
        origin: str,
        destination: str,
        outbound_date: str,
        return_date: str | None = None,
        adults: int = 1,
        children: int = 0,
        cabin_class: int = 1,
        currency: str = "USD",
    ) -> list[dict]:
        params = {
            "engine": "google_flights",
            "departure_id": origin.upper(),
            "arrival_id": destination.upper(),
            "outbound_date": outbound_date,
            "type": 1 if return_date else 2,
            "adults": adults,
            "children": children,
            "travel_class": cabin_class,
            "currency": currency,
            "hl": "en",
            "deep_search": "true",
            "api_key": self.api_key,
        }

        if return_date:
            params["return_date"] = return_date

        return self._format(GoogleSearch(params).get_dict(), outbound_date)

    async def search_async(self, **kwargs) -> list[dict]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, partial(self.search, **kwargs))

    def _format(self, raw: dict, outbound_date: str) -> list[dict]:
        flights = []

        for section in ("best_flights", "other_flights"):
            for flight in raw.get(section, []):
                legs = flight.get("flights", [])
                flights.append(
                    {
                        "outbound_date": outbound_date,
                        "price": flight.get("price"),
                        "total_duration_min": flight.get("total_duration"),
                        "stops": len(legs) - 1,
                        "booking_token": flight.get("booking_token"),
                        "legs": [
                            {
                                "airline": leg.get("airline"),
                                "flight_number": leg.get("flight_number"),
                                "origin": leg.get("departure_airport", {}).get("id"),
                                "destination": leg.get("arrival_airport", {}).get("id"),
                                "departure": leg.get("departure_airport", {}).get("time"),
                                "arrival": leg.get("arrival_airport", {}).get("time"),
                                "duration_min": leg.get("duration"),
                                "cabin_class": leg.get("travel_class"),
                            }
                            for leg in legs
                        ],
                        "is_best": section == "best_flights",
                    }
                )

        return flights


flight_service = FlightService()
