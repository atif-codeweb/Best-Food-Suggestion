"""
Tool definitions and implementations for the Islamabad/Rawalpindi Food Guide Agent.

Each tool has:
  - A schema in TOOLS (OpenAI/Groq function-calling format)
  - A Python implementation function
  - Registration in TOOL_MAP for dispatch

All implementations call the local FastAPI service.
"""

import json
import requests
from typing import Optional

API_BASE_URL = "http://localhost:8000"

# ─── Tool Schemas (Anthropic tool_use format) ─────────────────────────────────

TOOLS = [
    {
        "name": "search_restaurants",
        "description": (
            "Search for restaurants in Islamabad/Rawalpindi. "
            "Optionally filter by cuisine type, area/sector, minimum rating, or vegetarian-friendly."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cuisine": {
                    "type": "string",
                    "description": "Cuisine type, e.g. 'Pakistani', 'Italian', 'Afghan', 'BBQ', 'Continental'",
                },
                "area": {
                    "type": "string",
                    "description": "Area or sector, e.g. 'F-7', 'F-6', 'G-6', 'Margalla Hills'",
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum star rating out of 5, e.g. 4.0",
                },
                "vegetarian": {
                    "type": "boolean",
                    "description": "If true, return only vegetarian-friendly restaurants",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_restaurant_details",
        "description": "Get full details of a specific restaurant by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {
                    "type": "string",
                    "description": "Restaurant ID, e.g. 'r001', 'r002'",
                }
            },
            "required": ["restaurant_id"],
        },
    },
    {
        "name": "search_picnic_spots",
        "description": (
            "Search for picnic spots and outdoor areas in Islamabad/Rawalpindi. "
            "Optionally filter by area, minimum rating, activity, or free entry."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "area": {
                    "type": "string",
                    "description": "Area, e.g. 'Margalla Hills', 'Rawal Lake', 'F-9', 'Shakarparian'",
                },
                "min_rating": {
                    "type": "number",
                    "description": "Minimum star rating out of 5",
                },
                "activity": {
                    "type": "string",
                    "description": "Activity to filter by, e.g. 'Hiking', 'Boating', 'Picnicking', 'Photography'",
                },
                "free_entry": {
                    "type": "boolean",
                    "description": "If true, return only spots with free entry",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_picnic_spot_details",
        "description": "Get full details of a specific picnic spot by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "spot_id": {
                    "type": "string",
                    "description": "Picnic spot ID, e.g. 'ps001', 'ps002'",
                }
            },
            "required": ["spot_id"],
        },
    },
    {
        "name": "create_booking",
        "description": (
            "Create a restaurant reservation. "
            "Use this only after confirming all details with the user."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string", "description": "Restaurant ID to book at"},
                "restaurant_name": {"type": "string", "description": "Restaurant name"},
                "orderer_name": {"type": "string", "description": "Full name of the person booking"},
                "orderer_contact": {"type": "string", "description": "Phone number of the person booking"},
                "party_size": {"type": "integer", "description": "Number of guests"},
                "reservation_date": {
                    "type": "string",
                    "description": "Reservation date in YYYY-MM-DD format",
                },
                "reservation_time": {
                    "type": "string",
                    "description": "Reservation time in HH:MM (24-hour) format",
                },
                "special_requests": {
                    "type": "string",
                    "description": "Any special requests or notes (optional)",
                },
            },
            "required": [
                "restaurant_id",
                "restaurant_name",
                "orderer_name",
                "orderer_contact",
                "party_size",
                "reservation_date",
                "reservation_time",
            ],
        },
    },
    {
        "name": "get_bookings",
        "description": "Look up existing bookings by name, status, or restaurant.",
        "input_schema": {
            "type": "object",
            "properties": {
                "orderer_name": {
                    "type": "string",
                    "description": "Name of the person who made the booking",
                },
                "status": {
                    "type": "string",
                    "description": "Booking status: 'confirmed', 'pending', 'cancelled', or 'completed'",
                },
                "restaurant_id": {
                    "type": "string",
                    "description": "Filter by restaurant ID",
                },
            },
            "required": [],
        },
    },
    {
        "name": "cancel_booking",
        "description": "Cancel an existing booking by its booking ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "booking_id": {
                    "type": "string",
                    "description": "The booking ID to cancel, e.g. 'BKG001'",
                }
            },
            "required": ["booking_id"],
        },
    },
]


def to_groq_tools(tools: list) -> list:
    """
    Convert tool schemas from Anthropic format to Groq/OpenAI function-calling format.

    Anthropic format:  { "name": ..., "description": ..., "input_schema": {...} }
    Groq/OpenAI format: { "type": "function", "function": { "name": ..., "description": ..., "parameters": {...} } }
    """
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"],
            },
        }
        for tool in tools
    ]


# ─── Tool Implementations ─────────────────────────────────────────────────────

def _get(endpoint: str, params: dict = None) -> dict:
    """Helper: GET request to the local API."""
    try:
        resp = requests.get(f"{API_BASE_URL}{endpoint}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Cannot connect to the API server. Is the backend running?"}
    except requests.HTTPError as e:
        return {"error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


def _post(endpoint: str, payload: dict) -> dict:
    """Helper: POST request to the local API."""
    try:
        resp = requests.post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Cannot connect to the API server. Is the backend running?"}
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        return {"error": f"API error: {detail}"}
    except Exception as e:
        return {"error": str(e)}


def _delete(endpoint: str) -> dict:
    """Helper: DELETE request to the local API."""
    try:
        resp = requests.delete(f"{API_BASE_URL}{endpoint}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except requests.ConnectionError:
        return {"error": "Cannot connect to the API server. Is the backend running?"}
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        return {"error": f"API error: {detail}"}
    except Exception as e:
        return {"error": str(e)}


def search_restaurants(
    cuisine: Optional[str] = None,
    area: Optional[str] = None,
    min_rating: Optional[float] = None,
    vegetarian: Optional[bool] = None,
) -> dict:
    params = {}
    if cuisine:
        params["cuisine"] = cuisine
    if area:
        params["area"] = area
    if min_rating is not None:
        params["min_rating"] = min_rating
    if vegetarian is not None:
        params["vegetarian"] = str(vegetarian).lower()

    result = _get("/api/restaurants", params)
    if "error" in result:
        return result

    if not result:
        return {"result": "No restaurants found matching your criteria.", "restaurants": []}
    return {"result": f"Found {len(result)} restaurant(s).", "restaurants": result}


def get_restaurant_details(restaurant_id: str) -> dict:
    return _get(f"/api/restaurants/{restaurant_id}")


def search_picnic_spots(
    area: Optional[str] = None,
    min_rating: Optional[float] = None,
    activity: Optional[str] = None,
    free_entry: Optional[bool] = None,
) -> dict:
    params = {}
    if area:
        params["area"] = area
    if min_rating is not None:
        params["min_rating"] = min_rating
    if activity:
        params["activity"] = activity
    if free_entry is not None:
        params["free_entry"] = str(free_entry).lower()

    result = _get("/api/picnic-spots", params)
    if "error" in result:
        return result

    if not result:
        return {"result": "No picnic spots found matching your criteria.", "spots": []}
    return {"result": f"Found {len(result)} picnic spot(s).", "spots": result}


def get_picnic_spot_details(spot_id: str) -> dict:
    return _get(f"/api/picnic-spots/{spot_id}")


def create_booking(
    restaurant_id: str,
    restaurant_name: str,
    orderer_name: str,
    orderer_contact: str,
    party_size: int,
    reservation_date: str,
    reservation_time: str,
    special_requests: str = "",
) -> dict:
    payload = {
        "restaurant_id": restaurant_id,
        "restaurant_name": restaurant_name,
        "orderer_name": orderer_name,
        "orderer_contact": orderer_contact,
        "party_size": party_size,
        "reservation_date": reservation_date,
        "reservation_time": reservation_time,
        "special_requests": special_requests,
    }
    result = _post("/api/bookings", payload)
    if "error" in result:
        return result
    return {"result": "Booking created successfully!", "booking": result}


def get_bookings(
    orderer_name: Optional[str] = None,
    status: Optional[str] = None,
    restaurant_id: Optional[str] = None,
) -> dict:
    params = {}
    if orderer_name:
        params["orderer_name"] = orderer_name
    if status:
        params["status"] = status
    if restaurant_id:
        params["restaurant_id"] = restaurant_id

    result = _get("/api/bookings", params)
    if "error" in result:
        return result

    if not result:
        return {"result": "No bookings found.", "bookings": []}
    return {"result": f"Found {len(result)} booking(s).", "bookings": result}


def cancel_booking(booking_id: str) -> dict:
    return _delete(f"/api/bookings/{booking_id}")


# ─── Dispatcher ───────────────────────────────────────────────────────────────

TOOL_MAP = {
    "search_restaurants": search_restaurants,
    "get_restaurant_details": get_restaurant_details,
    "search_picnic_spots": search_picnic_spots,
    "get_picnic_spot_details": get_picnic_spot_details,
    "create_booking": create_booking,
    "get_bookings": get_bookings,
    "cancel_booking": cancel_booking,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Dispatch a tool call by name and return a JSON string result."""
    if tool_name not in TOOL_MAP:
        return json.dumps({"error": f"Unknown tool: '{tool_name}'"})

    try:
        result = TOOL_MAP[tool_name](**tool_input)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except TypeError as e:
        return json.dumps({"error": f"Invalid tool arguments: {e}"})
    except Exception as e:
        return json.dumps({"error": f"Tool execution failed: {e}"})
