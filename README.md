```markdown
# Air Quality Monitor

A real-time air quality monitoring dashboard visualizing data from 4,877+ US monitoring stations with historical trends and location comparisons.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791)
![Redis](https://img.shields.io/badge/Redis-6+-dc382d)

## Tech Stack

### Backend
- **Flask** - REST API framework
- **SQLAlchemy** - Database ORM with PostgreSQL
- **Celery** - Distributed task queue for data processing
- **Redis** - Caching and message broker
- **Flask-Caching** - API response caching
- **Requests** - HTTP client for OpenAQ API

### Frontend
- **React 18** - UI framework with hooks
- **Leaflet** - Interactive mapping library
- **Chart.js** - Data visualization
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls

### Infrastructure
- **PostgreSQL** - Primary database with indexes
- **Redis** - Cache and Celery broker
- **OpenAQ API** - External data source
- **Flower** - Celery task monitoring

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │    │   Flask Backend │    │   PostgreSQL    │
│                 │◄───┤                 │◄───┤                 │
│ -  Interactive UI │    │ -  REST APIs     │    │ -  23K+ Records  │
│ -  Charts & Maps │    │ -  Data Models   │    │ -  Optimized     │
│ -  Trend Analysis│    │ -  Caching       │    │ -  Indexed       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│      Redis      │    │     Celery      │    │   OpenAQ API    │
│                 │◄───┤                 │───►│                 │
│ -  Task Queue    │    │ -  Data Fetching │    │ -  4,877 Stations│
│ -  API Caching   │    │ -  Scheduling    │    │ -  Real-time Data│
│ -  Session Store │    │ -  Rate Limiting │    │ -  Historical    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Data Flow

1. **Celery Workers** fetch data from OpenAQ API every 2 hours
2. **PostgreSQL** stores locations, sensors, and measurements
3. **Redis** caches API responses for performance
4. **Flask APIs** serve data with eager loading and pagination
5. **React Frontend** renders interactive maps and charts

## Quick Start

```
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
flask run --port 5001

# Frontend  
cd frontend/air-quality-frontend
npm install && npm start

# Services
redis-server
celery -A celery_app worker --loglevel=info
celery -A celery_app beat --loglevel=info
```

## Key APIs

```
GET /api/locations              # All monitoring stations
GET /api/measurements           # Historical data (no date limits)
GET /api/parameters             # Available pollutants
GET /api/stats/overview         # System statistics
```

## Performance Features

- **Redis Caching**: 10-50ms cached responses
- **Database Indexes**: Optimized queries on 23K+ records  
- **Eager Loading**: Eliminates N+1 query problems
- **Rate Limiting**: Respectful OpenAQ API usage
- **Background Processing**: Non-blocking data collection
