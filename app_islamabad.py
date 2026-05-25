"""
Islamabad/Rawalpindi Restaurant & Picnic Guide
Streamlit Frontend Application
"""

import sys
from pathlib import Path
from datetime import date

import requests
import streamlit as st

# Ensure project root is on sys.path so agent imports work
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ─── Page Config ──────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Islamabad Food & Picnic Guide",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ────────────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

# ─── API Helpers ──────────────────────────────────────────────────────────────

def api_get(endpoint: str, params: dict = None):
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", params=params, timeout=5)
        resp.raise_for_status()
        return resp.json(), None
    except requests.ConnectionError:
        return None, "⚠️ Cannot connect to the API server. Please ensure the backend is running."
    except requests.HTTPError as e:
        return None, f"API error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def api_post(endpoint: str, payload: dict):
    try:
        resp = requests.post(f"{API_BASE}{endpoint}", json=payload, timeout=5)
        resp.raise_for_status()
        return resp.json(), None
    except requests.ConnectionError:
        return None, "⚠️ Cannot connect to the API server."
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        return None, f"Error: {detail}"
    except Exception as e:
        return None, f"Unexpected error: {e}"


def api_delete(endpoint: str):
    try:
        resp = requests.delete(f"{API_BASE}{endpoint}", timeout=5)
        resp.raise_for_status()
        return resp.json(), None
    except requests.ConnectionError:
        return None, "⚠️ Cannot connect to the API server."
    except requests.HTTPError as e:
        try:
            detail = e.response.json().get("detail", e.response.text)
        except Exception:
            detail = e.response.text
        return None, f"Error: {detail}"
    except Exception as e:
        return None, f"Unexpected error: {e}"

# ─── Session State ────────────────────────────────────────────────────────────

if "page" not in st.session_state:
    st.session_state.page = "🏠 Home"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "agent" not in st.session_state:
    st.session_state.agent = None
if "agent_error" not in st.session_state:
    st.session_state.agent_error = None

# ─── Agent Loader ─────────────────────────────────────────────────────────────

def get_agent():
    """Lazily initialise the AI agent; cache error so we don't retry on every render."""
    if st.session_state.agent is None and st.session_state.agent_error is None:
        try:
            from agents.conversation import FoodGuideAgent
            st.session_state.agent = FoodGuideAgent()
        except ValueError as e:
            st.session_state.agent_error = str(e)
        except ImportError as e:
            st.session_state.agent_error = f"Import error: {e}"
        except Exception as e:
            st.session_state.agent_error = f"Unexpected error: {e}"
    return st.session_state.agent, st.session_state.agent_error

# ─── Custom CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
.restaurant-card {
    background: #fdf6f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #e8613c;
}
.spot-card {
    background: #f0f7f0;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 10px;
    border-left: 4px solid #2ecc71;
}
.stat-box {
    background: white;
    border-radius: 10px;
    padding: 18px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🌆 Islamabad Guide")
    st.markdown("*Your Twin Cities Food & Picnic Companion*")
    st.divider()

    PAGES = [
        "🏠 Home",
        "🍽️ Restaurants",
        "🌳 Picnic Spots",
        "📅 Make a Booking",
        "📋 My Bookings",
        "🤖 AI Assistant",
    ]
    current_index = PAGES.index(st.session_state.page) if st.session_state.page in PAGES else 0
    selected = st.radio("Navigate", PAGES, index=current_index, label_visibility="collapsed")
    st.session_state.page = selected

    st.divider()

    # Live API health badge
    health, _ = api_get("/api/health")
    if health:
        st.success("✅ API Online")
        st.caption(
            f"🍽️ {health.get('restaurants', 0)} restaurants  "
            f"🌳 {health.get('picnic_spots', 0)} spots  "
            f"📅 {health.get('bookings', 0)} bookings"
        )
    else:
        st.error("❌ API Offline")
        st.caption("Start the backend with `python start.py`")

    st.divider()
    st.caption("Built with Streamlit · FastAPI · Claude")

# ─── Page: Home ───────────────────────────────────────────────────────────────

if st.session_state.page == "🏠 Home":
    st.title("🍽️ Islamabad & Rawalpindi Guide")
    st.subheader("Discover the best food and picnic spots in the Twin Cities")
    st.divider()

    health, _ = api_get("/api/health")
    if health:
        bookings_data, _ = api_get("/api/bookings")
        bookings_data = bookings_data or []
        confirmed_count = sum(1 for b in bookings_data if b.get("status") == "confirmed")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("🍽️ Restaurants", health.get("restaurants", 0))
        c2.metric("🌳 Picnic Spots", health.get("picnic_spots", 0))
        c3.metric("📅 Total Bookings", len(bookings_data))
        c4.metric("✅ Confirmed", confirmed_count)

    st.divider()

    col_r, col_s = st.columns(2)

    with col_r:
        st.markdown("### 🍛 Top Restaurants")
        restaurants, _ = api_get("/api/restaurants")
        if restaurants:
            for r in sorted(restaurants, key=lambda x: x.get("rating", 0), reverse=True)[:3]:
                st.markdown(
                    f'<div class="restaurant-card">'
                    f'<strong>{r["name"]}</strong> ⭐ {r["rating"]}<br>'
                    f'<small>📍 {r["area"]} &nbsp;|&nbsp; 🍴 {", ".join(r["cuisine"][:2])} '
                    f'&nbsp;|&nbsp; 💰 {r["price_range"]}</small>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    with col_s:
        st.markdown("### 🌳 Top Picnic Spots")
        spots, _ = api_get("/api/picnic-spots")
        if spots:
            for s in sorted(spots, key=lambda x: x.get("rating", 0), reverse=True)[:3]:
                st.markdown(
                    f'<div class="spot-card">'
                    f'<strong>{s["name"]}</strong> ⭐ {s["rating"]}<br>'
                    f'<small>📍 {s["area"]} &nbsp;|&nbsp; 🎟️ {s["entry_fee"]}</small>'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.divider()
    st.info(
        "💡 **Tip:** Use the **AI Assistant** tab to get personalised recommendations "
        "and make bookings through a natural conversation!"
    )

# ─── Page: Restaurants ────────────────────────────────────────────────────────

elif st.session_state.page == "🍽️ Restaurants":
    st.title("🍽️ Restaurants")
    st.markdown("Explore the best dining spots in Islamabad & Rawalpindi")
    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        cuisine_filter = st.selectbox(
            "Cuisine", ["All", "Pakistani", "Italian", "Afghan", "Continental", "BBQ"]
        )
    with c2:
        area_filter = st.selectbox(
            "Area", ["All", "F-7", "F-6", "G-6", "Margalla Hills"]
        )
    with c3:
        min_rating = st.slider("Minimum Rating ⭐", 1.0, 5.0, 1.0, 0.5)

    params = {}
    if cuisine_filter != "All":
        params["cuisine"] = cuisine_filter
    if area_filter != "All":
        params["area"] = area_filter
    if min_rating > 1.0:
        params["min_rating"] = min_rating

    restaurants, error = api_get("/api/restaurants", params)

    if error:
        st.error(error)
    elif not restaurants:
        st.info("No restaurants match your filters.")
    else:
        st.markdown(f"**{len(restaurants)} restaurant(s) found**")
        for r in restaurants:
            with st.expander(f"**{r['name']}** — ⭐ {r['rating']} | 📍 {r['area']} | 💰 {r['price_range']}"):
                left, right = st.columns([2, 1])
                with left:
                    st.markdown(f"**About:** {r['description']}")
                    st.markdown(f"**Cuisines:** {', '.join(r['cuisine'])}")
                    st.markdown(f"**Location:** {r['location']}")
                    hours = r.get("opening_hours", {})
                    st.markdown(f"**Hours (weekday):** {hours.get('weekday', 'N/A')}")
                    st.markdown(f"**Hours (weekend):** {hours.get('weekend', 'N/A')}")
                    if r.get("signature_dishes"):
                        st.markdown(f"**Signature Dishes:** {', '.join(r['signature_dishes'])}")
                    if r.get("features"):
                        st.markdown(f"**Features:** {', '.join(r['features'])}")
                with right:
                    st.markdown(f"⭐ **Rating:** {r['rating']}/5 ({r.get('total_reviews', 0):,} reviews)")
                    st.markdown(f"📞 **Phone:** {r.get('phone', 'N/A')}")
                    st.markdown(f"🥗 **Vegetarian friendly:** {'Yes' if r.get('serves_vegetarian') else 'No'}")
                    st.markdown(f"🚗 **Parking:** {'Yes' if r.get('parking') else 'No'}")
                    st.markdown(f"🚚 **Delivery:** {'Yes' if r.get('delivery_available') else 'No'}")
                    st.markdown(f"📋 **Reservation required:** {'Yes' if r.get('reservation_required') else 'No'}")

                if st.button(f"📅 Book at {r['name']}", key=f"book_{r['id']}"):
                    st.session_state["preselect_restaurant"] = r["id"]
                    st.session_state.page = "📅 Make a Booking"
                    st.rerun()

# ─── Page: Picnic Spots ───────────────────────────────────────────────────────

elif st.session_state.page == "🌳 Picnic Spots":
    st.title("🌳 Picnic Spots")
    st.markdown("Discover the best outdoor and picnic spots in Islamabad & Rawalpindi")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        area_filter = st.selectbox(
            "Area", ["All", "Margalla Hills", "Rawal Lake", "F-9", "Shakarparian", "Rawalpindi"]
        )
    with c2:
        activity_filter = st.selectbox(
            "Activity", ["All", "Hiking", "Boating", "Picnicking", "Photography", "Bird watching"]
        )

    c3, c4 = st.columns(2)
    with c3:
        min_rating = st.slider("Minimum Rating ⭐", 1.0, 5.0, 1.0, 0.5)
    with c4:
        free_only = st.checkbox("Free Entry Only")

    params = {}
    if area_filter != "All":
        params["area"] = area_filter
    if activity_filter != "All":
        params["activity"] = activity_filter
    if min_rating > 1.0:
        params["min_rating"] = min_rating
    if free_only:
        params["free_entry"] = "true"

    spots, error = api_get("/api/picnic-spots", params)

    if error:
        st.error(error)
    elif not spots:
        st.info("No picnic spots match your filters.")
    else:
        st.markdown(f"**{len(spots)} spot(s) found**")
        for s in spots:
            with st.expander(f"🌳 **{s['name']}** — ⭐ {s['rating']} | 📍 {s['area']} | 🎟️ {s['entry_fee']}"):
                left, right = st.columns([2, 1])
                with left:
                    st.markdown(f"**About:** {s['description']}")
                    st.markdown(f"**Location:** {s['location']}")
                    st.markdown(f"**Best Time:** {s['best_time']}")
                    st.markdown(f"**Activities:** {', '.join(s.get('activities', []))}")
                    st.markdown(f"**Facilities:** {', '.join(s.get('facilities', []))}")
                    if s.get("best_season"):
                        st.markdown(f"**Best Season:** {', '.join(s['best_season'])}")
                with right:
                    st.markdown(f"⭐ **Rating:** {s['rating']}/5 ({s.get('total_reviews', 0):,} reviews)")
                    st.markdown(f"📏 **Distance:** {s.get('distance_from_center', 'N/A')}")
                    st.markdown(f"⏱️ **Visit Duration:** {s.get('estimated_visit_time', 'N/A')}")
                    st.markdown(f"♿ **Accessibility:** {s.get('accessibility', 'N/A')}")
                    st.markdown(f"👥 **Crowd Level:** {s.get('crowd_level', 'N/A')}")

# ─── Page: Make a Booking ─────────────────────────────────────────────────────

elif st.session_state.page == "📅 Make a Booking":
    st.title("📅 Make a Reservation")
    st.markdown("Book a table at your favourite restaurant")
    st.divider()

    restaurants, error = api_get("/api/restaurants")
    if error:
        st.error(error)
    elif restaurants:
        name_to_restaurant = {r["name"]: r for r in restaurants}
        options = list(name_to_restaurant.keys())

        preselect_id = st.session_state.pop("preselect_restaurant", None)
        preselect_name = next(
            (r["name"] for r in restaurants if r["id"] == preselect_id), None
        ) if preselect_id else None
        default_idx = options.index(preselect_name) if preselect_name in (options or []) else 0

        selected_name = st.selectbox("Select Restaurant", options, index=default_idx)
        selected = name_to_restaurant[selected_name]

        with st.expander(f"ℹ️ About {selected_name}", expanded=False):
            st.markdown(f"**Location:** {selected['location']}")
            st.markdown(f"**Hours (weekday):** {selected['opening_hours'].get('weekday', 'N/A')}")
            st.markdown(f"**Price Range:** {selected['price_range']}")
            st.markdown(f"**Phone:** {selected.get('phone', 'N/A')}")

        st.divider()

        c1, c2 = st.columns(2)
        with c1:
            orderer_name = st.text_input("Your Full Name *", placeholder="e.g. Ali Raza")
            orderer_contact = st.text_input("Phone Number *", placeholder="e.g. 03001234567")
            party_size = st.number_input("Number of Guests *", min_value=1, max_value=100, value=2)
        with c2:
            reservation_date = st.date_input("Reservation Date *", min_value=date.today())
            reservation_time = st.time_input("Reservation Time *")
            special_requests = st.text_area(
                "Special Requests (optional)",
                placeholder="e.g. Window table, birthday celebration, wheelchair access",
            )

        st.markdown("")
        if st.button("✅ Confirm Reservation", type="primary", use_container_width=True):
            if not orderer_name.strip():
                st.error("Please enter your full name.")
            elif not orderer_contact.strip():
                st.error("Please enter your phone number.")
            else:
                payload = {
                    "restaurant_id": selected["id"],
                    "restaurant_name": selected_name,
                    "orderer_name": orderer_name.strip(),
                    "orderer_contact": orderer_contact.strip(),
                    "party_size": int(party_size),
                    "reservation_date": str(reservation_date),
                    "reservation_time": reservation_time.strftime("%H:%M"),
                    "special_requests": special_requests.strip(),
                }
                result, err = api_post("/api/bookings", payload)
                if err:
                    st.error(err)
                else:
                    st.success(
                        f"🎉 Booking confirmed! Your Booking ID is **{result['booking_id']}** — save it for your records."
                    )
                    st.balloons()
                    st.markdown(
                        f"| | |\n|---|---|\n"
                        f"| 🍽️ Restaurant | {result['restaurant_name']} |\n"
                        f"| 👤 Name | {result['orderer_name']} |\n"
                        f"| 📅 Date | {result['reservation_date']} |\n"
                        f"| ⏰ Time | {result['reservation_time']} |\n"
                        f"| 👥 Guests | {result['party_size']} |\n"
                        f"| 📋 Status | {result['status'].upper()} |"
                    )

# ─── Page: My Bookings ────────────────────────────────────────────────────────

elif st.session_state.page == "📋 My Bookings":
    st.title("📋 Booking Management")
    st.markdown("View and manage all reservations")
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        search_name = st.text_input("Search by Name", placeholder="Customer name...")
    with c2:
        status_filter = st.selectbox(
            "Filter by Status", ["All", "confirmed", "pending", "cancelled", "completed"]
        )

    params = {}
    if search_name.strip():
        params["orderer_name"] = search_name.strip()
    if status_filter != "All":
        params["status"] = status_filter

    bookings, error = api_get("/api/bookings", params)

    if error:
        st.error(error)
    elif not bookings:
        st.info("No bookings found.")
    else:
        st.markdown(f"**{len(bookings)} booking(s) found**")
        STATUS_EMOJI = {"confirmed": "✅", "pending": "⏳", "cancelled": "❌", "completed": "🏁"}

        for b in bookings:
            status = b.get("status", "unknown")
            emoji = STATUS_EMOJI.get(status, "❓")

            with st.expander(
                f"{emoji} **{b['booking_id']}** — {b['restaurant_name']} | "
                f"{b['orderer_name']} | {b['reservation_date']}"
            ):
                left, right = st.columns([2, 1])
                with left:
                    st.markdown(f"**Restaurant:** {b['restaurant_name']}")
                    st.markdown(f"**Guest:** {b['orderer_name']}")
                    st.markdown(f"**Contact:** {b['orderer_contact']}")
                    st.markdown(f"**Party Size:** {b['party_size']} people")
                    st.markdown(f"**Date & Time:** {b['reservation_date']} at {b['reservation_time']}")
                    if b.get("special_requests"):
                        st.markdown(f"**Special Requests:** {b['special_requests']}")
                with right:
                    st.markdown(f"**Booking ID:** `{b['booking_id']}`")
                    st.markdown(f"**Status:** `{status.upper()}`")
                    created = b.get("created_at", "")
                    st.markdown(f"**Created:** {created[:10] if created else 'N/A'}")

                    if status not in ("cancelled", "completed"):
                        if st.button(f"❌ Cancel {b['booking_id']}", key=f"cancel_{b['booking_id']}"):
                            result, err = api_delete(f"/api/bookings/{b['booking_id']}")
                            if err:
                                st.error(err)
                            else:
                                st.success(f"Booking {b['booking_id']} has been cancelled.")
                                st.rerun()

# ─── Page: AI Assistant ───────────────────────────────────────────────────────

elif st.session_state.page == "🤖 AI Assistant":
    st.title("🤖 AI Food Guide Assistant")
    st.markdown("Chat with **Isloo Guide** for personalised recommendations and bookings")
    st.divider()

    agent, agent_error = get_agent()

    if agent_error:
        st.warning(f"⚠️ AI Assistant unavailable: {agent_error}")
        st.info(
            "Get a free Groq API key at https://console.groq.com, "
            "set `GROQ_API_KEY` as an environment variable, then restart the app."
        )
    else:
        # Show welcome message on first load
        if not st.session_state.chat_messages:
            from agents.prompt_library import WELCOME_MESSAGE
            st.session_state.chat_messages.append(
                {"role": "assistant", "content": WELCOME_MESSAGE}
            )

        # Render conversation history
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Ask me anything about food or picnic spots in Islamabad..."):
            st.session_state.chat_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Isloo Guide is thinking..."):
                    reply = agent.chat(prompt)
                st.markdown(reply)

            st.session_state.chat_messages.append({"role": "assistant", "content": reply})

        # Reset button
        _, btn_col = st.columns([5, 1])
        with btn_col:
            if st.button("🔄 Reset Chat"):
                st.session_state.chat_messages = []
                if agent:
                    agent.reset()
                st.rerun()
