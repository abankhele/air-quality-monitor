import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import AirQualityMap from '../components/map/AirQualityMap';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import {
    fetchLocations,
    fetchParameters,
    getLocationAllParameters,  // Use this instead of fetchRecentMeasurements
    fetchStats
} from '../api';

const Dashboard = () => {
    const [locations, setLocations] = useState([]);
    const [parameters, setParameters] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [measurements, setMeasurements] = useState({});
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [locationsData, parametersData, statsData] = await Promise.all([
                    fetchLocations(),
                    fetchParameters(),
                    fetchStats()
                ]);

                setLocations(locationsData.results || []);
                setParameters(parametersData || []);
                setStats(statsData || {});

                // Select first location by default
                if (locationsData.results && locationsData.results.length > 0) {
                    setSelectedLocation(locationsData.results[0]);
                }
            } catch (error) {
                console.error('Error fetching data:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        if (selectedLocation && parameters.length > 0) {
            const fetchLocationMeasurements = async () => {
                try {
                    // Use the new helper function to get all parameter data
                    const measurementsData = await getLocationAllParameters(selectedLocation.id, parameters);
                    setMeasurements(measurementsData);
                } catch (error) {
                    console.error('Error fetching measurements:', error);
                }
            };

            fetchLocationMeasurements();
        }
    }, [selectedLocation, parameters]);

    const handleLocationSelect = (location) => {
        setSelectedLocation(location);
    };

    if (loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="space-y-6">
                {/* Stats Overview */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900">Total Locations</h3>
                            <p className="text-3xl font-bold text-blue-600">{stats.location_count || 0}</p>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900">Total Sensors</h3>
                            <p className="text-3xl font-bold text-green-600">{stats.sensor_count || 0}</p>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900">Total Measurements</h3>
                            <p className="text-3xl font-bold text-purple-600">{stats.measurement_count || 0}</p>
                        </div>
                        <div className="bg-white p-6 rounded-lg shadow">
                            <h3 className="text-lg font-medium text-gray-900">Fresh Data (May 21+)</h3>
                            <p className="text-3xl font-bold text-orange-600">{stats.recent_measurement_count || 0}</p>
                        </div>
                    </div>
                )}

                {/* Main Content */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    {/* Map */}
                    <div className="lg:col-span-2 bg-white rounded-lg shadow p-4">
                        <h2 className="text-xl font-semibold mb-4">Air Quality Map</h2>
                        <div className="h-96">
                            <AirQualityMap onLocationSelect={handleLocationSelect} />
                        </div>
                    </div>

                    {/* Location Details */}
                    <div className="bg-white rounded-lg shadow p-4">
                        <h2 className="text-xl font-semibold mb-4">Location Details</h2>

                        {selectedLocation ? (
                            <div className="space-y-4">
                                <div>
                                    <h3 className="font-medium text-lg">{selectedLocation.name}</h3>
                                    <p className="text-gray-600">{selectedLocation.locality}</p>
                                    <p className="text-sm text-gray-500">
                                        {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
                                    </p>
                                </div>

                                <div>
                                    <h4 className="font-medium mb-2">Air Quality Index</h4>
                                    <AQIGauge aqi={selectedLocation.aqi} />
                                </div>

                                <div>
                                    <h4 className="font-medium mb-2">Available Sensors</h4>
                                    <div className="space-y-2">
                                        {selectedLocation.sensors?.map((sensor) => (
                                            <div key={sensor.id} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                                                <span className="text-sm font-medium">{sensor.parameter.display_name}</span>
                                                <span className="text-sm text-gray-600">
                                                    {sensor.last_value ? `${sensor.last_value} ${sensor.parameter.unit}` : 'No data'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-gray-500">Select a location on the map to view details</p>
                        )}
                    </div>
                </div>

                {/* Charts */}
                {selectedLocation && (
                    <div className="bg-white rounded-lg shadow p-4">
                        <h2 className="text-xl font-semibold mb-4">
                            Pollutant Trends for {selectedLocation.name}
                            <span className="text-sm text-gray-500 ml-2">(Fresh data from May 21, 2025+)</span>
                        </h2>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {parameters.map(parameter => {
                                const paramMeasurements = measurements[parameter.id] || [];
                                return (
                                    <div key={parameter.id} className="bg-gray-50 p-4 rounded-lg">
                                        <PollutantChart
                                            measurements={paramMeasurements}
                                            parameter={parameter}
                                            title={`${parameter.display_name} Trend (${paramMeasurements.length} data points)`}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default Dashboard;
