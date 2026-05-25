"""
Islamabad/Rawalpindi Food & Picnic Guide - FastAPI Backend Service

Provides REST API endpoints for restaurants, picnic spots, and bookings.

Run from the project root with:
    uvicorn data.service:app --host 0.0.0.0 --port 8000 --reload
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path
from datetime import datetime

# ─── Paths ────────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent
RESTAURANTS_FILE = DATA_DIR / "restaurants.json"
PICNIC_SPOTS_FILE = DATA_DIR / "picnic_spots.json"
BOOKINGS_FILE = DATA_DIR / "bookings_list.json"

# ─── App ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Islamabad/Rawalpindi Food & Picnic Guide API",
    description="REST API for restaurants, picnic spots, and bookings in Islamabad & Rawalpindi",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Data Helpers ─────────────────────────────────────────────────────────────

def load_json(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ─── Pydantic Models ──────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    restaurant_id: str
    restaurant_name: str
    orderer_name: str
    orderer_contact: str
    party_size: int
    reservation_date: str   # YYYY-MM-DD
    reservation_time: str   # HH:MM
    special_requests: Optional[str] = ""


class BookingStatusUpdate(BaseModel):
    status: str  # confirmed | pending | cancelled | completed

# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Health"])
def health_check():
    """Return service status and record counts."""
    return {
        "status": "healthy",
        "restaurants": len(load_json(RESTAURANTS_FILE)),
        "picnic_spots": len(load_json(PICNIC_SPOTS_FILE)),
        "bookings": len(load_json(BOOKINGS_FILE)),
    }

# ─── Restaurants ──────────────────────────────────────────────────────────────

@app.get("/api/restaurants", tags=["Restaurants"])
def get_restaurants(
    cuisine: Optional[str] = Query(None, description="Filter by cuisine type"),
    area: Optional[str] = Query(None, description="Filter by area/sector"),
    min_rating: Optional[float] = Query(None, description="Minimum rating (0-5)"),
    vegetarian: Optional[bool] = Query(None, description="Vegetarian-friendly only"),
):
    """Return all restaurants with optional filters."""
    restaurants = load_json(RESTAURANTS_FILE)

    if cuisine:
        restaurants = [
            r for r in restaurants
            if any(cuisine.lower() in c.lower() for c in r.get("cuisine", []))
        ]
    if area:
        restaurants = [
            r for r in restaurants
            if area.lower() in r.get("area", "").lower()
        ]
    if min_rating is not None:
        restaurants = [r for r in restaurants if r.get("rating", 0) >= min_rating]
    if vegetarian is not None:
        restaurants = [r for r in restaurants if r.get("serves_vegetarian") == vegetarian]

    return restaurants


@app.get("/api/restaurants/{restaurant_id}", tags=["Restaurants"])
def get_restaurant(restaurant_id: str):
    """Return a single restaurant by ID."""
    for r in load_json(RESTAURANTS_FILE):
        if r["id"] == restaurant_id:
            return r
    raise HTTPException(status_code=404, detail="Restaurant not found")

# ─── Picnic Spots ─────────────────────────────────────────────────────────────

@app.get("/api/picnic-spots", tags=["Picnic Spots"])
def get_picnic_spots(
    area: Optional[str] = Query(None, description="Filter by area"),
    min_rating: Optional[float] = Query(None, description="Minimum rating (0-5)"),
    activity: Optional[str] = Query(None, description="Filter by available activity"),
    free_entry: Optional[bool] = Query(None, description="Free entry spots only"),
):
    """Return all picnic spots with optional filters."""
    spots = load_json(PICNIC_SPOTS_FILE)

    if area:
        spots = [s for s in spots if area.lower() in s.get("area", "").lower()]
    if min_rating is not None:
        spots = [s for s in spots if s.get("rating", 0) >= min_rating]
    if activity:
        spots = [
            s for s in spots
            if any(activity.lower() in a.lower() for a in s.get("activities", []))
        ]
    if free_entry:
        spots = [s for s in spots if "free" in s.get("entry_fee", "").lower()]

    return spots


@app.get("/api/picnic-spots/{spot_id}", tags=["Picnic Spots"])
def get_picnic_spot(spot_id: str):
    """Return a single picnic spot by ID."""
    for s in load_json(PICNIC_SPOTS_FILE):
        if s["id"] == spot_id:
            return s
    raise HTTPException(status_code=404, detail="Picnic spot not found")

# ─── Bookings ─────────────────────────────────────────────────────────────────

@app.get("/api/bookings", tags=["Bookings"])
def get_bookings(
    status: Optional[str] = Query(None, description="Filter by status"),
    restaurant_id: Optional[str] = Query(None, description="Filter by restaurant ID"),
    orderer_name: Optional[str] = Query(None, description="Search by orderer name"),
):
    """Return all bookings with optional filters."""
    bookings = load_json(BOOKINGS_FILE)

    if status:
        bookings = [b for b in bookings if b.get("status", "").lower() == status.lower()]
    if restaurant_id:
        bookings = [b for b in bookings if b.get("restaurant_id") == restaurant_id]
    if orderer_name:
        bookings = [
            b for b in bookings
            if orderer_name.lower() in b.get("orderer_name", "").lower()
        ]

    return bookings


@app.get("/api/bookings/{booking_id}", tags=["Bookings"])
def get_booking(booking_id: str):
    """Return a single booking by ID."""
    for b in load_json(BOOKINGS_FILE):
        if b["booking_id"] == booking_id:
            return b
    raise HTTPException(status_code=404, detail="Booking not found")


@app.post("/api/bookings", status_code=201, tags=["Bookings"])
def create_booking(booking: BookingCreate):
    """Create a new restaurant reservation."""
    restaurants = load_json(RESTAURANTS_FILE)
    valid_ids = {r["id"] for r in restaurants}
    if booking.restaurant_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    bookings = load_json(BOOKINGS_FILE)
    booking_number = len(bookings) + 1

    new_booking = {
        "booking_id": f"BKG{booking_number:03d}",
        "restaurant_id": booking.restaurant_id,
        "restaurant_name": booking.restaurant_name,
        "orderer_name": booking.orderer_name,
        "orderer_contact": booking.orderer_contact,
        "party_size": booking.party_size,
        "reservation_date": booking.reservation_date,
        "reservation_time": booking.reservation_time,
        "status": "confirmed",
        "special_requests": booking.special_requests or "",
        "created_at": datetime.now().isoformat(),
    }

    bookings.append(new_booking)
    save_json(BOOKINGS_FILE, bookings)
    return new_booking


@app.patch("/api/bookings/{booking_id}", tags=["Bookings"])
def update_booking_status(booking_id: str, update: BookingStatusUpdate):
    """Update the status of an existing booking."""
    valid_statuses = {"confirmed", "pending", "cancelled", "completed"}
    if update.status.lower() not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {sorted(valid_statuses)}",
        )

    bookings = load_json(BOOKINGS_FILE)
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = update.status.lower()
            save_json(BOOKINGS_FILE, bookings)
            return b

    raise HTTPException(status_code=404, detail="Booking not found")


@app.delete("/api/bookings/{booking_id}", tags=["Bookings"])
def cancel_booking(booking_id: str):
    """Cancel a booking by setting its status to 'cancelled'."""
    bookings = load_json(BOOKINGS_FILE)
    for b in bookings:
        if b["booking_id"] == booking_id:
            b["status"] = "cancelled"
            save_json(BOOKINGS_FILE, bookings)
            return {"message": f"Booking {booking_id} has been cancelled.", "booking": b}

    raise HTTPException(status_code=404, detail="Booking not found")
