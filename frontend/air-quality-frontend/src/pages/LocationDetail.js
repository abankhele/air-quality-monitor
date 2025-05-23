import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import { fetchLocationDetail, fetchParameters, fetchMeasurements } from '../api';

const LocationDetail = () => {
    const { id } = useParams();
    const [location, setLocation] = useState(null);
    const [parameters, setParameters] = useState([]);
    const [measurements, setMeasurements] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [locationData, parametersData] = await Promise.all([
                    fetchLocationDetail(id),
                    fetchParameters()
                ]);

                setLocation(locationData);
                setParameters(parametersData);

                // Fetch measurements for each parameter
                const measurementsData = {};
                for (const parameter of parametersData) {
                    try {
                        const data = await fetchMeasurements({
                            location_id: id,
                            parameter_id: parameter.id,
                            limit: 50
                        });
                        measurementsData[parameter.id] = data.results || [];
                    } catch (error) {
                        measurementsData[parameter.id] = [];
                    }
                }
                setMeasurements(measurementsData);
            } catch (error) {
                console.error('Error fetching location data:', error);
            } finally {
                setLoading(false);
            }
        };

        if (id) {
            fetchData();
        }
    }, [id]);

    if (loading) {
        return (
            <Layout>
                <div className="flex justify-center items-center h-full">
                    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
                </div>
            </Layout>
        );
    }

    if (!location) {
        return (
            <Layout>
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-gray-900">Location not found</h1>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div className="space-y-6">
                {/* Location Header */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">{location.name}</h1>
                            <p className="text-lg text-gray-600">{location.locality}</p>
                            <p className="text-sm text-gray-500">
                                {location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}
                            </p>
                        </div>
                        <div className="text-right">
                            <h3 className="text-lg font-medium mb-2">Air Quality Index</h3>
                            <AQIGauge aqi={location.aqi} />
                        </div>
                    </div>
                </div>

                {/* Sensors Info */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">Available Sensors</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {location.sensors?.map((sensor) => (
                            <div key={sensor.id} className="bg-gray-50 p-4 rounded-lg">
                                <h3 className="font-medium">{sensor.parameter.display_name}</h3>
                                <p className="text-2xl font-bold text-blue-600">
                                    {sensor.last_value ? `${sensor.last_value} ${sensor.parameter.unit}` : 'No data'}
                                </p>
                                <p className="text-sm text-gray-500">
                                    {sensor.last_updated ? `Updated: ${new Date(sensor.last_updated).toLocaleDateString()}` : 'No recent data'}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Charts */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">Historical Trends</h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {parameters.map(parameter => {
                            const paramMeasurements = measurements[parameter.id] || [];
                            return (
                                <div key={parameter.id} className="bg-gray-50 p-4 rounded-lg">
                                    <PollutantChart
                                        measurements={paramMeasurements}
                                        parameter={parameter}
                                        title={`${parameter.display_name} History`}
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

export default LocationDetail;
