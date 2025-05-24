import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import PollutantChart from '../components/charts/PollutantChart';
import {
    fetchParameters,
    getComparisonData,  // Use this instead of fetchRecentMeasurements
    fetchLocations
} from '../api';

const TrendsPage = () => {
    const [parameters, setParameters] = useState([]);
    const [locations, setLocations] = useState([]);
    const [selectedParameter, setSelectedParameter] = useState(null);
    const [selectedLocations, setSelectedLocations] = useState([]);
    const [measurements, setMeasurements] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [parametersData, locationsData] = await Promise.all([
                    fetchParameters(),
                    fetchLocations()
                ]);

                setParameters(parametersData);
                setLocations(locationsData.results?.slice(0, 20) || []); // First 20 locations

                if (parametersData.length > 0) {
                    setSelectedParameter(parametersData[0]);
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
        if (selectedParameter && selectedLocations.length > 0) {
            const fetchMeasurementsData = async () => {
                try {
                    // Use the comparison helper function
                    const comparisonData = await getComparisonData(selectedLocations, selectedParameter.id);
                    setMeasurements(comparisonData);
                } catch (error) {
                    console.error('Error fetching comparison data:', error);
                }
            };

            fetchMeasurementsData();
        }
    }, [selectedParameter, selectedLocations]);

    const handleLocationToggle = (location) => {
        setSelectedLocations(prev => {
            const isSelected = prev.find(loc => loc.id === location.id);
            if (isSelected) {
                return prev.filter(loc => loc.id !== location.id);
            } else {
                return [...prev, location];
            }
        });
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
                <h1 className="text-2xl font-bold text-gray-900">
                    Air Quality Trends
                    <span className="text-sm text-gray-500 ml-2">(Fresh data from May 21, 2025+)</span>
                </h1>

                {/* Controls */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        {/* Parameter Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Parameter
                            </label>
                            <select
                                value={selectedParameter?.id || ''}
                                onChange={(e) => {
                                    const param = parameters.find(p => p.id === parseInt(e.target.value));
                                    setSelectedParameter(param);
                                }}
                                className="w-full p-2 border border-gray-300 rounded-md"
                            >
                                {parameters.map(param => (
                                    <option key={param.id} value={param.id}>
                                        {param.display_name} ({param.unit})
                                    </option>
                                ))}
                            </select>
                        </div>

                        {/* Location Selection */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Locations (max 5)
                            </label>
                            <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2">
                                {locations.map(location => (
                                    <label key={location.id} className="flex items-center space-x-2 py-1">
                                        <input
                                            type="checkbox"
                                            checked={selectedLocations.find(loc => loc.id === location.id) !== undefined}
                                            onChange={() => handleLocationToggle(location)}
                                            disabled={selectedLocations.length >= 5 && !selectedLocations.find(loc => loc.id === location.id)}
                                            className="rounded"
                                        />
                                        <span className="text-sm">{location.name} - {location.locality}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Charts */}
                {selectedParameter && selectedLocations.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">
                            {selectedParameter.display_name} Trends Comparison
                        </h2>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                            {selectedLocations.map(location => {
                                const locationMeasurements = measurements[location.id] || [];
                                return (
                                    <div key={location.id} className="bg-gray-50 p-4 rounded-lg">
                                        <PollutantChart
                                            measurements={locationMeasurements}
                                            parameter={selectedParameter}
                                            title={`${location.name} - ${selectedParameter.display_name} (${locationMeasurements.length} points)`}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {selectedLocations.length === 0 && (
                    <div className="bg-white rounded-lg shadow p-6 text-center">
                        <p className="text-gray-500">Select locations to view trends comparison</p>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default TrendsPage;
