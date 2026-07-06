import asyncio
from collections.abc import AsyncGenerator
from datetime import date, timedelta
from itertools import product
from typing import cast

from src.models.interface import ToolCallResult, ToolEvent
from src.tools.base import Tool
from src.tools.flights.flight_service import flight_service


def _date_range(start: str, end: str) -> list[str]:
    d = date.fromisoformat(start)
    stop = date.fromisoformat(end)
    dates = []
    while d <= stop:
        dates.append(d.isoformat())
        d += timedelta(days=1)
    return dates


def _to_list(val: str | list[str]) -> list[str]:
    return [val] if isinstance(val, str) else val


class FlightSearchTool(Tool):
    name = "flight_search"
    description = """
    Search for flights using Google Flights data. Always economy class.
    For cities with multiple airports, pass all of them — searches run in parallel and
    results clearly show which airport each flight uses.
    Examples: New York = ["JFK", "LGA", "EWR"], Boston = ["BOS"], LA = ["LAX", "BUR", "LGB", "ONT", "SNA"].
    Supports a single outbound date or a date range (also searched in parallel).
    Results are sorted by price. Southwest Airlines is not included — direct users to southwest.com.
    """

    parameters = {
        "type": "object",
        "properties": {
            "origins": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Departure airport IATA codes. Pass all airports for the origin city (e.g. ['JFK', 'LGA', 'EWR'] for New York).",
            },
            "destinations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arrival airport IATA codes. Pass all airports for the destination city.",
            },
            "outbound_date": {
                "type": "string",
                "description": "Departure date in YYYY-MM-DD format. Use for a single date.",
            },
            "outbound_date_start": {
                "type": "string",
                "description": "Start of departure date range in YYYY-MM-DD format.",
            },
            "outbound_date_end": {
                "type": "string",
                "description": "End of departure date range in YYYY-MM-DD format.",
            },
            "return_date": {
                "type": "string",
                "description": "Return date in YYYY-MM-DD format. Omit for one-way flights.",
            },
            "adults": {
                "type": "integer",
                "description": "Number of adult passengers. Defaults to 1.",
            },
            "children": {
                "type": "integer",
                "description": "Number of child passengers. Defaults to 0.",
            },
            "currency": {
                "type": "string",
                "description": "Currency code for prices (e.g. USD, EUR). Defaults to USD.",
            },
        },
        "required": ["origins", "destinations"],
    }

    def __init__(self):
        self.service = flight_service

    async def run(self, tool_input: dict, user_context: dict) -> AsyncGenerator[ToolEvent, None]:
        try:
            origins = tool_input.get("origins")
            destinations = tool_input.get("destinations")

            if not origins or not destinations:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={"message": "Missing required fields: origins, destinations"},
                    ),
                )
                return

            # Support passing a plain string for either field
            origins = _to_list(origins)
            destinations = _to_list(destinations)

            # Resolve outbound dates
            outbound_date = tool_input.get("outbound_date")
            outbound_date_start = tool_input.get("outbound_date_start")
            outbound_date_end = tool_input.get("outbound_date_end")

            if outbound_date:
                outbound_dates = [outbound_date]
            elif outbound_date_start and outbound_date_end:
                outbound_dates = _date_range(outbound_date_start, outbound_date_end)
            else:
                yield ToolEvent(
                    type="result",
                    result=ToolCallResult(
                        status="failure",
                        data={
                            "message": "Provide either outbound_date or both outbound_date_start and outbound_date_end"
                        },
                    ),
                )
                return

            common = {
                "return_date": tool_input.get("return_date"),
                "adults": tool_input.get("adults", 1),
                "children": tool_input.get("children", 0),
                "cabin_class": 1,  # always economy
                "currency": tool_input.get("currency", "USD"),
            }

            # Fan out across all origin × destination × date combinations
            combos = list(product(origins, destinations, outbound_dates))
            tasks = [
                self.service.search_async(origin=orig, destination=dest, outbound_date=d, **common)
                for orig, dest, d in combos
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_flights: list[dict] = []
            errors = []
            for (orig, dest, d), result in zip(combos, results, strict=True):
                if isinstance(result, Exception):
                    errors.append(
                        {"origin": orig, "destination": dest, "date": d, "error": str(result)}
                    )
                else:
                    all_flights.extend(cast(list[dict], result))

            all_flights.sort(key=lambda f: f.get("price") or float("inf"))

            for flight in all_flights:
                flight.pop("booking_token", None)

            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="success",
                    data={
                        "flights": all_flights,
                        "total": len(all_flights),
                        "origins_searched": origins,
                        "destinations_searched": destinations,
                        "dates_searched": outbound_dates,
                        "errors": errors or None,
                        "note": "Southwest Airlines is not included — check southwest.com directly.",
                    },
                ),
            )

        except Exception as e:
            yield ToolEvent(
                type="result",
                result=ToolCallResult(
                    status="failure",
                    data={"error": str(e)},
                ),
            )
