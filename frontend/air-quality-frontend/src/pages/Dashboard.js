import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import AirQualityMap from '../components/map/AirQualityMap';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import {
    fetchLocations,
    fetchParameters,
    getLocationAllParameters,
    fetchStats,
    checkDataAvailability
} from '../api';

const Dashboard = () => {
    const [locations, setLocations] = useState([]);
    const [parameters, setParameters] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [measurements, setMeasurements] = useState({});
    const [stats, setStats] = useState(null);
    const [dataInfo, setDataInfo] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [locationsData, parametersData, statsData, dataAvailability] = await Promise.all([
                    fetchLocations(),
                    fetchParameters(),
                    fetchStats(),
                    checkDataAvailability()
                ]);

                setLocations(locationsData.results || []);
                setParameters(parametersData || []);
                setStats(statsData || {});
                setDataInfo(dataAvailability);

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
                    // Get all historical data for this location
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

    // Filter parameters that have data for charts
    const parametersWithData = parameters.filter(parameter => {
        const paramMeasurements = measurements[parameter.id] || [];
        return paramMeasurements.length > 0;
    });

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
                {/* Data Overview */}
                {dataInfo && (
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                        <h3 className="font-medium text-blue-800 mb-2">📊 Historical Data Available</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <span className="text-blue-600 font-medium">Oldest Data:</span>
                                <br />
                                <span className="text-blue-800">{dataInfo.overall_oldest_data ? new Date(dataInfo.overall_oldest_data).toLocaleDateString() : 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-blue-600 font-medium">Newest Data:</span>
                                <br />
                                <span className="text-blue-800">{dataInfo.overall_newest_data ? new Date(dataInfo.overall_newest_data).toLocaleDateString() : 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-blue-600 font-medium">Data Span:</span>
                                <br />
                                <span className="text-blue-800">{dataInfo.data_span_years ? `${dataInfo.data_span_years.toFixed(1)} years` : 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-blue-600 font-medium">Total Measurements:</span>
                                <br />
                                <span className="text-blue-800">{dataInfo.total_measurements?.toLocaleString() || 'N/A'}</span>
                            </div>
                        </div>
                    </div>
                )}

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
                            <h3 className="text-lg font-medium text-gray-900">Active Sensors</h3>
                            <p className="text-3xl font-bold text-orange-600">{stats.active_sensors || 0}</p>
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

                {/* Charts - ONLY SHOW CHARTS WITH DATA */}
                {selectedLocation && (
                    <div className="bg-white rounded-lg shadow p-4">
                        <h2 className="text-xl font-semibold mb-4">
                            Historical Trends for {selectedLocation.name}
                            <span className="text-sm text-gray-500 ml-2">
                                ({parametersWithData.length} of {parameters.length} parameters have data)
                            </span>
                        </h2>

                        {parametersWithData.length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {parametersWithData.map(parameter => {
                                    const paramMeasurements = measurements[parameter.id] || [];

                                    // Calculate data span for this parameter
                                    let dataSpanText = '';
                                    if (paramMeasurements.length > 0) {
                                        const oldest = new Date(paramMeasurements[paramMeasurements.length - 1]?.timestamp);
                                        const newest = new Date(paramMeasurements[0]?.timestamp);
                                        const spanYears = (newest - oldest) / (365.25 * 24 * 60 * 60 * 1000);
                                        dataSpanText = spanYears > 1 ? `${spanYears.toFixed(1)} years` : `${Math.round(spanYears * 365)} days`;
                                    }

                                    return (
                                        <div key={parameter.id} className="bg-gray-50 p-4 rounded-lg">
                                            <PollutantChart
                                                measurements={paramMeasurements}
                                                parameter={parameter}
                                                title={`${parameter.display_name} - ${paramMeasurements.length} measurements${dataSpanText ? ` (${dataSpanText})` : ''}`}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="text-center py-8">
                                <div className="text-gray-400 mb-4">
                                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No Historical Data Available</h3>
                                <p className="text-gray-500">
                                    This location doesn't have historical measurement data in our database yet.
                                    Try selecting a different location or check back later.
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default Dashboard;
