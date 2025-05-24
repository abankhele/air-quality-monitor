import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import PollutantChart from '../components/charts/PollutantChart';
import AQIGauge from '../components/charts/AQIGauge';
import {
    fetchLocationDetail,
    fetchParameters,
    getLocationAllParameters,
    fetchDataRange
} from '../api';

const LocationDetail = () => {
    const { id } = useParams();
    const [location, setLocation] = useState(null);
    const [parameters, setParameters] = useState([]);
    const [measurements, setMeasurements] = useState({});
    const [dataRange, setDataRange] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [locationData, parametersData, dataRangeData] = await Promise.all([
                    fetchLocationDetail(id),
                    fetchParameters(),
                    fetchDataRange(parseInt(id))
                ]);

                setLocation(locationData);
                setParameters(parametersData);
                setDataRange(dataRangeData);

                // Fetch ALL historical measurements for all parameters
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

                {/* Data Range Info - Only show if there's data */}
                {dataRange && dataRange.total_measurements > 0 && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <h3 className="font-medium text-green-800 mb-2">📊 Historical Data Range</h3>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                            <div>
                                <span className="text-green-600 font-medium">Oldest Data:</span>
                                <br />
                                <span className="text-green-800">{dataRange.oldest_data ? new Date(dataRange.oldest_data).toLocaleDateString() : 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-green-600 font-medium">Newest Data:</span>
                                <br />
                                <span className="text-green-800">{dataRange.newest_data ? new Date(dataRange.newest_data).toLocaleDateString() : 'N/A'}</span>
                            </div>
                            <div>
                                <span className="text-green-600 font-medium">Total Measurements:</span>
                                <br />
                                <span className="text-green-800">{dataRange.total_measurements?.toLocaleString() || 'N/A'}</span>
                            </div>
                        </div>
                        {dataRange.data_span_years && (
                            <p className="text-green-700 mt-2">
                                <strong>Data Span:</strong> {dataRange.data_span_years.toFixed(1)} years of historical data
                            </p>
                        )}
                    </div>
                )}

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

                {/* Charts - ONLY SHOW CHARTS WITH DATA */}
                <div className="bg-white rounded-lg shadow p-6">
                    <h2 className="text-xl font-semibold mb-4">
                        Historical Trends
                        {parametersWithData.length > 0 && (
                            <span className="text-sm text-gray-500 ml-2">
                                ({parametersWithData.length} of {parameters.length} parameters have data)
                            </span>
                        )}
                    </h2>

                    {parametersWithData.length > 0 ? (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {parametersWithData.map(parameter => {
                                const paramMeasurements = measurements[parameter.id] || [];

                                // Calculate data span for this parameter
                                let dataInfo = '';
                                if (paramMeasurements.length > 0) {
                                    const oldest = new Date(paramMeasurements[paramMeasurements.length - 1]?.timestamp);
                                    const newest = new Date(paramMeasurements[0]?.timestamp);
                                    const spanYears = (newest - oldest) / (365.25 * 24 * 60 * 60 * 1000);
                                    dataInfo = spanYears > 1
                                        ? `${oldest.getFullYear()}-${newest.getFullYear()} (${spanYears.toFixed(1)} years)`
                                        : `${Math.round(spanYears * 365)} days of data`;
                                }

                                return (
                                    <div key={parameter.id} className="bg-gray-50 p-4 rounded-lg">
                                        <PollutantChart
                                            measurements={paramMeasurements}
                                            parameter={parameter}
                                            title={`${parameter.display_name} History - ${paramMeasurements.length} measurements${dataInfo ? ` (${dataInfo})` : ''}`}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    ) : (
                        <div className="text-center py-12">
                            <div className="text-gray-400 mb-4">
                                <svg className="mx-auto h-16 w-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <h3 className="text-xl font-medium text-gray-900 mb-2">No Historical Data Available</h3>
                            <p className="text-gray-500 mb-4">
                                This location doesn't have historical measurement data in our database yet.
                            </p>
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 max-w-md mx-auto">
                                <p className="text-blue-700 text-sm">
                                    <strong>Note:</strong> While this location has {location.sensors?.length || 0} sensors configured,
                                    no historical measurement records are available. This could mean:
                                </p>
                                <ul className="text-blue-600 text-sm mt-2 list-disc list-inside">
                                    <li>The sensors are newly installed</li>
                                    <li>Data collection is in progress</li>
                                    <li>The sensors are not currently reporting</li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </Layout>
    );
};

export default LocationDetail;
