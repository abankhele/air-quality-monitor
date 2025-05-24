# Air Quality Monitor

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.9+-blue" alt="Python 3.9+"></a>
  <a href="https://reactjs.org/"><img src="https://img.shields.io/badge/React-18+-61dafb" alt="React 18+"></a>
  <a href="https://www.postgresql.org/"><img src="https://img.shields.io/badge/PostgreSQL-13+-336791" alt="PostgreSQL 13+"></a>
  <a href="https://redis.io/"><img src="https://img.shields.io/badge/Redis-6+-dc382d" alt="Redis 6+"></a>
</p>

> A real-time dashboard monitoring air quality across **4,877+ US stations**, with historical trends and location comparisons.

---

## 📋 Table of Contents

1. [Tech Stack](#tech-stack)
2. [Architecture Diagram](#architecture-diagram)
3. [Data Flow](#data-flow)
4. [Quick Start](#quick-start)
5. [Key APIs](#key-apis)
6. [Performance Features](#performance-features)

---

## 🛠 Tech Stack

### Backend

* **Flask**: REST API framework
* **SQLAlchemy**: ORM for PostgreSQL
* **Celery**: Distributed task queue
* **Redis**: Caching & message broker
* **Flask-Caching**: Response caching
* **Requests**: HTTP client for OpenAQ

### Frontend

* **React 18**: UI with hooks
* **Leaflet**: Maps & geospatial visualization
* **Chart.js**: Interactive charts
* **Tailwind CSS**: Utility-first styling
* **Axios**: API requests

### Infrastructure

* **PostgreSQL**: Primary DB with indexes
* **Redis**: Cache & Celery broker
* **OpenAQ API**: External data source (4,877+ stations)
* **Flower**: Celery monitoring dashboard

---

## 🏗 Architecture Diagram

```plain
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ React Frontend│◄──▶│ Flask Backend │◄──▶│ PostgreSQL    │
│ - Maps & UI   │    │ - REST APIs   │    │ - 23K+ records│
└───────────────┘    └───────────────┘    └───────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    Redis      │◄──▶│    Celery     │───▶│   OpenAQ API  │
│ - Cache       │    │ - Workers     │    │ - Real-time   │
└───────────────┘    │ - Scheduler   │    │ - Historical  │
                     └───────────────┘    └───────────────┘
```

---

## 🔄 Data Flow

1. **Celery** polls OpenAQ API every 2 hours.
2. Data stored in **PostgreSQL** (locations, sensors, measurements).
3. **Redis** caches frequent queries and API responses.
4. **Flask** exposes paginated endpoints with eager loading.
5. **React** renders maps, charts, and comparisons in real-time.

---

## 🚀 Quick Start

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask run --port 5001

# Frontend
cd frontend/air-quality-frontend\ n
npm install && npm start

# Services
redis-server
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

---

## 🔑 Key APIs

```http
GET /api/locations      # List all stations
GET /api/measurements   # Historical measurement data
GET /api/parameters     # Supported pollutants
GET /api/stats/overview # System health & stats
```

---

## ⚡️ Performance Features

* **Redis Caching**: 10–50 ms response times
* **DB Indexes**: Fast querying of 23K+ records
* **Eager Loading**: Avoids N+1 queries
* **Rate Limiting**: Throttles API calls to OpenAQ
* **Async Processing**: Non-blocking Celery tasks

---


