# 🍽️ Islamabad & Rawalpindi Food & Picnic Guide

> **AI-powered discovery platform for restaurants, picnic spots, and smart bookings in Pakistan’s twin cities.**

A modern full-stack web application that helps users explore food places, outdoor picnic spots, and make bookings—enhanced with an AI assistant powered by Groq.

---

## 🚀 Product Overview

This platform combines **location intelligence + AI recommendations** to deliver a seamless experience for discovering:

* Restaurants based on cuisine, budget, and ratings
* Scenic picnic locations with filters for activities & amenities
* Smart reservation system
* Conversational AI assistant (*Isloo Guide*)

---

## ✨ Key Features

### 🍴 Smart Restaurant Discovery

Search and filter restaurants by:

* Cuisine type
* Location
* Rating
* Dietary preferences (e.g., vegetarian)

### 🌳 Picnic Spot Explorer

Find outdoor locations with:

* Entry fee information
* Available activities
* Family-friendly filters

### 📅 Booking System

* Reserve tables instantly
* Add special requests
* Manage booking records

### 🤖 AI Assistant (Isloo Guide)

* Context-aware recommendations
* Natural language queries
* Powered by **Groq LLaMA 3.3**

---

## 🧠 Tech Stack

| Layer      | Technology           |
| ---------- | -------------------- |
| Frontend   | Streamlit            |
| Backend    | FastAPI              |
| AI Engine  | Groq (LLaMA 3.3-70B) |
| Data Layer | JSON-based storage   |
| Runtime    | Python 3.8+          |

---

## ⚡ Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/islamabad-food-guide.git
cd islamabad-food-guide
```

---

### 2. Setup Environment

```bash
python -m venv venv
```

Activate:

**Windows**

```bash
venv\Scripts\activate
```

**macOS/Linux**

```bash
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Create a `.env` file:

```env
GROQ_API_KEY=your_api_key_here
```

Get your API key: [https://console.groq.com](https://console.groq.com)

---

### 5. Run Application

```bash
python starter.py
```

---

## 🌐 System Endpoints

| Service     | URL                                                      |
| ----------- | -------------------------------------------------------- |
| Frontend    | [http://localhost:8501](http://localhost:8501)           |
| Backend API | [http://localhost:8000](http://localhost:8000)           |
| API Docs    | [http://localhost:8000/docs](http://localhost:8000/docs) |

---

## 🧪 Development Mode

Run services separately:

```bash
# Backend
uvicorn data.service:app --reload
```

```bash
# Frontend
streamlit run app_islamabad.py
```

---

## 🔎 Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "restaurants": 5,
  "picnic_spots": 10,
  "bookings": 22
}
```

---

## 📦 Project Structure

```
├── app_islamabad.py     # Streamlit frontend
├── starter.py           # App launcher (backend + frontend)
├── agents/              # AI agent (tool-calling logic)
├── data/                # FastAPI backend + JSON storage
└── requirements.txt
```

---

## 🔐 Environment Variables

| Variable     | Description              |
| ------------ | ------------------------ |
| GROQ_API_KEY | API key for AI assistant |

---

## 📄 License

MIT License — feel free to use and modify.

---

## 🚀 Vision

This project is designed as a foundation for:

* Smart tourism platforms
* AI-powered local discovery apps
* Booking + recommendation systems

---

