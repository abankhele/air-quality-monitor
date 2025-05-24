Here's a concise README.md for your air quality monitoring project:

```markdown
# 🌬️ Air Quality Monitor

A real-time air quality monitoring dashboard visualizing data from 4,877+ US monitoring stations. Track historical trends, compare locations, and monitor current air quality conditions.

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-336791)

## ✨ Features

- **4,877+ US Monitoring Stations** with real-time data
- **Historical Trends** from 2016 to present (where available)
- **Interactive Map** with location details
- **Compare up to 5 locations** side-by-side
- **Automated data updates** every 2 hours
- **Multiple pollutants**: PM2.5, PM10, O₃, NO₂, SO₂, CO

## 🚀 Quick Start

### Prerequisites
- Python 3.9+, Node.js 16+, PostgreSQL, Redis
- OpenAQ API Key (free at [openaq.org](https://openaq.org))

### Backend Setup
```
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure .env file
cp .env.example .env
# Add: DATABASE_URL, REDIS_URL, OPENAQ_API_KEY

flask run --port 5001
```

### Frontend Setup
```
cd frontend/air-quality-frontend
npm install
echo "REACT_APP_API_URL=http://localhost:5001/api" > .env
npm start
```

### Background Services
```
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A celery_app worker --loglevel=info

# Terminal 3: Celery Beat (scheduler)
celery -A celery_app beat --loglevel=info
```

## 📊 Initial Data Load
```
# Load all US locations
python manage.py update-locs

# Fetch latest measurements
python manage.py fetch-data

# Check status
python manage.py status
```

## 🔗 Access Points
- **Frontend**: http://localhost:3000
- **API**: http://localhost:5001/api
- **Task Monitor**: http://localhost:5555

## 🛠️ Tech Stack

**Backend**: Flask, SQLAlchemy, Celery, Redis, PostgreSQL  
**Frontend**: React, Leaflet, Chart.js, Tailwind CSS  
**Data Source**: OpenAQ API

## 📈 Key APIs
```
GET /api/locations              # All locations
GET /api/locations/{id}         # Location details
GET /api/measurements           # Historical data
GET /api/parameters             # Available pollutants
```

## 🎯 Usage

1. **Dashboard** - Overview with interactive map
2. **Location Details** - Click any location for trends
3. **Trends** - Compare multiple locations
4. **Predefined Comparisons** - Houston Metro, Cross-Country, etc.

## 🔧 Management Commands
```
python manage.py fetch-data     # Update all location data
python manage.py status         # Show data statistics
python manage.py data-range     # Check data availability
```

## 📊 Data Coverage
- **23,000+ measurements** across all locations
- **Complete US coverage** with EPA monitoring network
- **Historical data** spanning multiple years
- **Real-time updates** every 2 hours


