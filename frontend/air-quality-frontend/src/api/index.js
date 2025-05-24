import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Locations
export const fetchLocations = async (bounds) => {
    const params = bounds ? {
        north: bounds.north,
        south: bounds.south,
        east: bounds.east,
        west: bounds.west,
    } : {};

    const response = await api.get('/locations', { params });
    return response.data;
};

export const fetchLocationDetail = async (id) => {
    const response = await api.get(`/locations/${id}`);
    return response.data;
};

export const searchLocations = async (query) => {
    const response = await api.get('/locations/search', {
        params: { q: query }
    });
    return response.data;
};

// Parameters
export const fetchParameters = async () => {
    const response = await api.get('/parameters');
    return response.data;
};

// Measurements - REMOVE ALL DATE FILTERING - SHOW ALL HISTORICAL DATA
export const fetchMeasurements = async (params) => {
    // Remove any date-related parameters - backend now shows all historical data
    const { days, start_date, end_date, date_from, date_to, ...cleanParams } = params || {};

    const response = await api.get('/measurements', { params: cleanParams });
    return response.data;
};

// Get chart data for specific location and parameter - ALL HISTORICAL DATA
export const fetchChartMeasurements = async (locationId, parameterId, limit = 200) => {
    const response = await api.get('/measurements', {
        params: {
            location_id: locationId,
            parameter_id: parameterId,
            limit: limit
            // NO DATE FILTERING - get all available historical data
        }
    });
    return response.data;
};

// Get measurements for a specific sensor - ALL HISTORICAL DATA
export const fetchSensorMeasurements = async (sensorId, limit = 200) => {
    const response = await api.get('/measurements', {
        params: {
            sensor_id: sensorId,
            limit: limit
            // NO DATE FILTERING - get all available historical data
        }
    });
    return response.data;
};

// Get measurements for a location - ALL HISTORICAL DATA
export const fetchLocationMeasurements = async (locationId, limit = 500) => {
    const response = await api.get('/measurements', {
        params: {
            location_id: locationId,
            limit: limit
            // NO DATE FILTERING - get all available historical data
        }
    });
    return response.data;
};

// Get measurements for a parameter across locations - ALL HISTORICAL DATA
export const fetchParameterMeasurements = async (parameterId, limit = 500) => {
    const response = await api.get('/measurements', {
        params: {
            parameter_id: parameterId,
            limit: limit
            // NO DATE FILTERING - get all available historical data
        }
    });
    return response.data;
};

// Get latest measurements for all sensors
export const fetchLatestMeasurements = async () => {
    const response = await api.get('/measurements/latest');
    return response.data;
};

// NEW: Get data range for a location
export const fetchDataRange = async (locationId) => {
    const response = await api.get('/measurements/data-range', {
        params: locationId ? { location_id: locationId } : {}
    });
    return response.data;
};

// Stats
export const fetchStats = async () => {
    const response = await api.get('/stats/overview');
    return response.data;
};

// Debug endpoint
export const fetchDebugInfo = async () => {
    const response = await api.get('/measurements/debug');
    return response.data;
};

// Helper functions for common use cases

// Get chart data for dashboard - ALL HISTORICAL DATA
export const getDashboardChartData = async (locationId, parameterId) => {
    try {
        const data = await fetchChartMeasurements(locationId, parameterId, 200);
        return data.results || [];
    } catch (error) {
        console.error(`Error fetching chart data for location ${locationId}, parameter ${parameterId}:`, error);
        return [];
    }
};

// Get all parameters data for a location - ALL HISTORICAL DATA
export const getLocationAllParameters = async (locationId, parameters) => {
    const measurementsData = {};

    // First, get the data range for this location to show users what's available
    try {
        const dataRange = await fetchDataRange(locationId);
        console.log(`📊 Location ${locationId} data range:`, dataRange);
    } catch (error) {
        console.log(`Could not get data range for location ${locationId}`);
    }

    for (const parameter of parameters) {
        try {
            const data = await fetchChartMeasurements(locationId, parameter.id, 200);
            measurementsData[parameter.id] = data.results || [];

            if (data.results && data.results.length > 0) {
                const oldest = data.results[data.results.length - 1]?.timestamp;
                const newest = data.results[0]?.timestamp;
                console.log(`Parameter ${parameter.name}: ${data.results.length} measurements (${oldest} to ${newest})`);
            } else {
                console.log(`Parameter ${parameter.name}: 0 measurements`);
            }
        } catch (error) {
            console.error(`Error fetching data for parameter ${parameter.id}:`, error);
            measurementsData[parameter.id] = [];
        }
    }

    return measurementsData;
};

// Get comparison data for trends page - ALL HISTORICAL DATA
export const getComparisonData = async (locations, parameterId) => {
    const comparisonData = {};

    for (const location of locations) {
        try {
            const data = await fetchChartMeasurements(location.id, parameterId, 200);
            comparisonData[location.id] = data.results || [];

            if (data.results && data.results.length > 0) {
                const oldest = data.results[data.results.length - 1]?.timestamp;
                const newest = data.results[0]?.timestamp;
                console.log(`Location ${location.name}: ${data.results.length} measurements (${oldest} to ${newest})`);
            } else {
                console.log(`Location ${location.name}: 0 measurements`);
            }
        } catch (error) {
            console.error(`Error fetching data for location ${location.id}:`, error);
            comparisonData[location.id] = [];
        }
    }

    return comparisonData;
};

// Check data availability
export const checkDataAvailability = async () => {
    try {
        const debug = await fetchDebugInfo();
        console.log('Overall data availability:', {
            totalMeasurements: debug.total_measurements,
            oldestData: debug.oldest_data,
            newestData: debug.newest_data,
            dataSpanYears: debug.data_span_years,
            validSensors: debug.valid_sensors
        });
        return debug;
    } catch (error) {
        console.error('Error checking data availability:', error);
        return null;
    }
};

export default api;
