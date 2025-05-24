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

// Measurements - OPTIMIZED FOR YOUR FRESH DATA (NO DATE PARAMS)
export const fetchMeasurements = async (params) => {
    // Backend is hardcoded to May 21, 2025+ so no need for date filtering
    // Remove any date-related parameters that might interfere
    const { days, start_date, end_date, ...cleanParams } = params || {};

    const response = await api.get('/measurements', { params: cleanParams });
    return response.data;
};

// Get measurements for charts (your fresh data)
export const fetchChartMeasurements = async (locationId, parameterId, limit = 100) => {
    const response = await api.get('/measurements', {
        params: {
            location_id: locationId,
            parameter_id: parameterId,
            limit: limit
        }
    });
    return response.data;
};

// Get measurements for a specific sensor (your fresh data)
export const fetchSensorMeasurements = async (sensorId, limit = 100) => {
    const response = await api.get('/measurements', {
        params: {
            sensor_id: sensorId,
            limit: limit
        }
    });
    return response.data;
};

// Get measurements for a location (all parameters)
export const fetchLocationMeasurements = async (locationId, limit = 200) => {
    const response = await api.get('/measurements', {
        params: {
            location_id: locationId,
            limit: limit
        }
    });
    return response.data;
};

// Get measurements for a parameter (all locations)
export const fetchParameterMeasurements = async (parameterId, limit = 200) => {
    const response = await api.get('/measurements', {
        params: {
            parameter_id: parameterId,
            limit: limit
        }
    });
    return response.data;
};

// Get all measurements (no filters) - BE CAREFUL WITH THIS
export const fetchAllMeasurements = async (limit = 1000) => {
    const response = await api.get('/measurements', {
        params: { limit: limit }
    });
    return response.data;
};

// Get latest measurements for all sensors
export const fetchLatestMeasurements = async () => {
    const response = await api.get('/measurements/latest');
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

// Get chart data for dashboard
export const getDashboardChartData = async (locationId, parameterId) => {
    try {
        const data = await fetchChartMeasurements(locationId, parameterId, 50);
        return data.results || [];
    } catch (error) {
        console.error(`Error fetching chart data for location ${locationId}, parameter ${parameterId}:`, error);
        return [];
    }
};

// Get all parameters data for a location (for multiple charts)
// Get all parameters data for a location (ONLY for parameters this location has)
export const getLocationAllParameters = async (locationId, allParameters) => {
    const measurementsData = {};

    console.log(`🔍 Fetching data for location ${locationId}`);

    // First, get the location details to see what sensors it actually has
    try {
        const locationDetail = await fetchLocationDetail(locationId);
        const locationSensors = locationDetail.sensors || [];

        console.log(`📍 Location ${locationDetail.name} has ${locationSensors.length} sensors`);

        // Only fetch data for parameters this location actually has sensors for
        const availableParameterIds = locationSensors.map(sensor => sensor.parameter.id);
        const parametersToFetch = allParameters.filter(param =>
            availableParameterIds.includes(param.id)
        );

        console.log(`🎯 Will fetch data for ${parametersToFetch.length} parameters that this location has`);

        for (const parameter of parametersToFetch) {
            try {
                const data = await fetchChartMeasurements(locationId, parameter.id, 100);
                measurementsData[parameter.id] = data.results || [];

                if (data.results && data.results.length > 0) {
                    console.log(`✅ Parameter ${parameter.name}: ${data.results.length} measurements`);
                } else {
                    console.log(`❌ Parameter ${parameter.name}: 0 measurements (but sensor exists)`);
                }
            } catch (error) {
                console.error(`Error fetching data for parameter ${parameter.id}:`, error);
                measurementsData[parameter.id] = [];
            }
        }

        // For parameters this location doesn't have, set empty array
        for (const parameter of allParameters) {
            if (!measurementsData[parameter.id]) {
                measurementsData[parameter.id] = [];
            }
        }

    } catch (error) {
        console.error('Error fetching location details:', error);
    }

    return measurementsData;
};


// Get comparison data for trends page
export const getComparisonData = async (locations, parameterId) => {
    const comparisonData = {};

    for (const location of locations) {
        try {
            const data = await fetchChartMeasurements(location.id, parameterId, 100);
            comparisonData[location.id] = data.results || [];
            console.log(`Location ${location.name}: ${data.results?.length || 0} measurements`);
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
        console.log('Data availability:', {
            totalMeasurements: debug.total_measurements,
            freshMeasurements: debug.fresh_measurements_since_may_21,
            validSensors: debug.valid_sensors,
            startDate: debug.start_date_filter
        });
        return debug;
    } catch (error) {
        console.error('Error checking data availability:', error);
        return null;
    }
};

// Error handling wrapper
const withErrorHandling = (apiCall) => {
    return async (...args) => {
        try {
            return await apiCall(...args);
        } catch (error) {
            console.error('API Error:', error.response?.data || error.message);
            throw error;
        }
    };
};

// Export wrapped functions with error handling
export const safeApi = {
    fetchLocations: withErrorHandling(fetchLocations),
    fetchLocationDetail: withErrorHandling(fetchLocationDetail),
    fetchParameters: withErrorHandling(fetchParameters),
    fetchMeasurements: withErrorHandling(fetchMeasurements),
    fetchStats: withErrorHandling(fetchStats),
    getDashboardChartData: withErrorHandling(getDashboardChartData),
    getLocationAllParameters: withErrorHandling(getLocationAllParameters),
    checkDataAvailability: withErrorHandling(checkDataAvailability)
};

export default api;
