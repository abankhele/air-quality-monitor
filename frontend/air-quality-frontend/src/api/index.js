import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

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

// Parameters
export const fetchParameters = async () => {
    const response = await api.get('/parameters');
    return response.data;
};

// Measurements
export const fetchMeasurements = async (sensorId, days = 1) => {
    const response = await api.get('/measurements', {
        params: { sensor_id: sensorId, days }
    });
    return response.data;
};

export default api;
