import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import AirQualityMap from '../components/map/AirQualityMap';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import { fetchLocations, fetchParameters, fetchMeasurements } from '../api';

const Dashboard = () => {
    const [locations, setLocations] = useState([]);
    const [parameters, setParameters] = useState([]);
    const [selectedLocation, setSelectedLocation] = useState(null);
    const [measurements, setMeasurements] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [locationsData, parametersData] = await Promise.all([
                    fetchLocations(),
                    fetchParameters()
                ]);

                setLocations(locationsData);
                setParameters(parametersData);

                // Select first location by default
                if (locationsData.length > 0) {
                    setSelectedLocation(locationsData[0]);
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
                    const measurementsData = {};

                    // Fetch measurements for each sensor at the selected location
                    for (const sensor of selectedLocation.sensors || []) {
                        const data = await fetchMeasurements(sensor.id, 1);
                        measurementsData[sensor.parameter_id] = data;
                    }

                    setMeasurements(measurementsData);
                } catch (error) {
                    console.error('Error fetching measurements:', error);
                }
            };

            fetchLocationMeasurements();
        }
    }, [selectedLocation, parameters]);

    if (loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 h-full">
                <div className="lg:col-span-2 h-96 lg:h-auto">
                    <AirQualityMap />
                </div>

                <div className="bg-white p-4 rounded-lg shadow">
                    <h2 className="text-xl font-semibold mb-4">Location Overview</h2>

                    <div className="mb-4">
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Select Location
                        </label>
                        <select
                            className="w-full p-2 border border-gray-300 rounded-md"
                            value={selectedLocation?.id || ''}
                            onChange={(e) => {
                                const location = locations.find(loc => loc.id === parseInt(e.target.value));
                                setSelectedLocation(location);
                            }}
                        >
                            {locations.map(location => (
                                <option key={location.id} value={location.id}>
                                    {location.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedLocation && (
                        <>
                            <div className="mb-4">
                                <h3 className="font-medium">Air Quality Index</h3>
                                <AQIGauge aqi={selectedLocation.aqi} />
                            </div>

                            <div className="mb-4">
                                <h3 className="font-medium mb-2">Location Details</h3>
                                <div className="bg-gray-50 p-3 rounded">
                                    <p><span className="font-medium">Name:</span> {selectedLocation.name}</p>
                                    <p><span className="font-medium">City:</span> {selectedLocation.locality || 'N/A'}</p>
                                    <p>
                                        <span className="font-medium">Coordinates:</span> {selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}
                                    </p>
                                </div>
                            </div>
                        </>
                    )}
                </div>

                <div className="lg:col-span-3 bg-white p-4 rounded-lg shadow">
                    <h2 className="text-xl font-semibold mb-4">Pollutant Trends</h2>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {parameters.map(parameter => {
                            const paramMeasurements = measurements[parameter.id] || [];
                            return (
                                <div key={parameter.id} className="h-64">
                                    <PollutantChart
                                        measurements={paramMeasurements}
                                        parameter={parameter}
                                    />
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default Dashboard;
