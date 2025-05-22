# AirQuality Monitor

A comprehensive air quality monitoring dashboard that visualizes real-time and historical air quality data across the United States.

## Features

- **Interactive Map**: Visualize air quality data across 4,800+ monitoring stations in the US
- **Real-time Updates**: Latest air quality measurements from OpenAQ API
- **Historical Data**: Track air quality trends over time
- **Pollutant Analysis**: Monitor multiple parameters (PM2.5, PM10, O3, NO2, SO2, CO)
- **Location Details**: Detailed information for each monitoring station

## Tech Stack

### Backend
- Python/Flask
- SQLAlchemy ORM
- PostgreSQL
- Celery/Redis for task scheduling

### Frontend
- React.js
- Leaflet for mapping
- Chart.js for data visualization
- Tailwind CSS for styling

## Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL
- Redis

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/air-quality-monitor.git
cd air-quality-monitor/backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and database settings

# Initialize database
flask db upgrade

# Seed initial data
python -m app.seed_locations

# Run the development server
flask run
```

### Frontend Setup
```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Start development server
npm start
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/locations` | GET | Get all monitoring stations |
| `/api/locations/:id` | GET | Get details for a specific station |
| `/api/parameters` | GET | Get all available parameters |
| `/api/measurements` | GET | Get measurements with filtering options |

## Data Source

This project uses data from the [OpenAQ](https://openaq.org/) platform, which aggregates air quality data from government agencies and other sources worldwide.


## Acknowledgments

- OpenAQ for providing the air quality data API
- All contributors to the open-source libraries used in this project
