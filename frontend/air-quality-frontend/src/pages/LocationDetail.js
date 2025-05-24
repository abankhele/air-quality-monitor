import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import {
    fetchLocationDetail,
    fetchParameters,
    getLocationAllParameters,fetchMeasurements  // Use this instead of fetchRecentMeasurements
} from '../api';

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

                // DEBUG: Check if this location has measurement records
                console.log('🔍 Location sensors:', locationData.sensors?.map(s => ({
                    parameter: s.parameter.name,
                    last_value: s.last_value,
                    last_updated: s.last_updated
                })));

                // DEBUG: Test fetching measurements for one parameter this location has
                if (locationData.sensors && locationData.sensors.length > 0) {
                    const firstSensor = locationData.sensors[0];
                    console.log(`🧪 Testing measurements for parameter ${firstSensor.parameter.name} (ID: ${firstSensor.parameter.id})`);

                    const testData = await fetchMeasurements({
                        location_id: parseInt(id),
                        parameter_id: firstSensor.parameter.id,
                        limit: 5
                    });

                    console.log(`🧪 Test result: ${testData.results?.length || 0} measurements found`);
                    console.log('🧪 Sample data:', testData.results?.[0]);
                }

                // Fetch measurements for all parameters using the helper function
                const measurementsData = await getLocationAllParameters(parseInt(id), parametersData);
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
                    <h2 className="text-xl font-semibold mb-4">
                        Historical Trends
                        <span className="text-sm text-gray-500 ml-2">(Fresh data from May 21, 2025+)</span>
                    </h2>
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {parameters.map(parameter => {
                            const paramMeasurements = measurements[parameter.id] || [];
                            return (
                                <div key={parameter.id} className="bg-gray-50 p-4 rounded-lg">
                                    <PollutantChart
                                        measurements={paramMeasurements}
                                        parameter={parameter}
                                        title={`${parameter.display_name} History (${paramMeasurements.length} points)`}
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
