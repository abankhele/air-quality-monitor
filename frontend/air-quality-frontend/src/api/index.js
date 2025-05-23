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

// Measurements
export const fetchMeasurements = async (params) => {
    const response = await api.get('/measurements', { params });
    return response.data;
};

export const fetchLatestMeasurements = async () => {
    const response = await api.get('/measurements/latest');
    return response.data;
};

// Stats
export const fetchStats = async () => {
    const response = await api.get('/stats/overview');
    return response.data;
};

export default api;
