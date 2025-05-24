import React, { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import PollutantChart from '../components/charts/PollutantChart';
import {
    fetchParameters,
    getComparisonData,
    fetchLocations,
    fetchChartMeasurements
} from '../api';

const TrendsPage = () => {
    const [parameters, setParameters] = useState([]);
    const [locations, setLocations] = useState([]);
    const [selectedParameter, setSelectedParameter] = useState(null);
    const [selectedLocations, setSelectedLocations] = useState([]);
    const [measurements, setMeasurements] = useState({});
    const [loading, setLoading] = useState(true);
    const [searchTerm, setSearchTerm] = useState('');
    const [filterByMetro, setFilterByMetro] = useState('all');
    const [locationDataInfo, setLocationDataInfo] = useState({});

    // Predefined comparison sets
    const predefinedSets = {
        'Houston Metro': [
            'Houston Deer Park C3',
            'Houston North Loop C',
            'Houston Bayland Park',
            'UH Moody Tower C695'
        ],
        'Cross-Country': [
            'Houston Deer Park C3',
            'West Phoenix',
            'Miami Fire Station #',
            'Morro Bay'
        ],
        'Urban Centers': [
            'Houston North Loop C',
            'West Phoenix',
            'Miami Fire Station #',
            'Indpls-Washington Pa'
        ],
        'Texas Locations': [
            'Houston Deer Park C3',
            'Houston North Loop C',
            'Danciger C618',
            'Lake Jackson C1016'
        ]
    };

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [parametersData, locationsData] = await Promise.all([
                    fetchParameters(),
                    fetchLocations()
                ]);

                setParameters(parametersData);
                setLocations(locationsData.results || []);

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

    // Check data availability when parameter changes
    useEffect(() => {
        if (selectedParameter && locations.length > 0) {
            const checkDataAvailability = async () => {
                const dataInfo = {};

                for (const location of locations) {
                    try {
                        const data = await fetchChartMeasurements(location.id, selectedParameter.id, 1);
                        dataInfo[location.id] = {
                            hasData: data.results?.length > 0,
                            count: data.meta?.total || 0
                        };
                    } catch (error) {
                        dataInfo[location.id] = { hasData: false, count: 0 };
                    }
                }

                setLocationDataInfo(dataInfo);
            };

            checkDataAvailability();
        }
    }, [selectedParameter, locations]);

    useEffect(() => {
        if (selectedParameter && selectedLocations.length > 0) {
            const fetchMeasurementsData = async () => {
                try {
                    const comparisonData = await getComparisonData(selectedLocations, selectedParameter.id);
                    setMeasurements(comparisonData);
                } catch (error) {
                    console.error('Error fetching comparison data:', error);
                }
            };

            fetchMeasurementsData();
        }
    }, [selectedParameter, selectedLocations]);

    // Group locations by metro area
    const groupLocationsByMetro = (locations) => {
        const grouped = {};

        locations.forEach(location => {
            const metro = location.locality || 'Other Locations';
            if (!grouped[metro]) {
                grouped[metro] = [];
            }
            grouped[metro].push(location);
        });

        // Sort metros by number of locations (descending)
        const sortedGrouped = {};
        Object.keys(grouped)
            .sort((a, b) => grouped[b].length - grouped[a].length)
            .forEach(key => {
                sortedGrouped[key] = grouped[key].sort((a, b) => a.name.localeCompare(b.name));
            });

        return sortedGrouped;
    };

    // Filter locations based on search and metro filter
    const filteredLocations = locations.filter(location => {
        const matchesSearch = location.name.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesMetro = filterByMetro === 'all' || location.locality === filterByMetro;
        return matchesSearch && matchesMetro;
    });

    const groupedLocations = groupLocationsByMetro(filteredLocations);
    const metroAreas = [...new Set(locations.map(loc => loc.locality).filter(Boolean))].sort();

    const handleLocationToggle = (location) => {
        setSelectedLocations(prev => {
            const isSelected = prev.find(loc => loc.id === location.id);
            if (isSelected) {
                return prev.filter(loc => loc.id !== location.id);
            } else if (prev.length < 5) {
                return [...prev, location];
            }
            return prev;
        });
    };

    const selectPredefinedSet = (locationNames) => {
        const matchedLocations = locations.filter(loc =>
            locationNames.some(name => loc.name.includes(name) || name.includes(loc.name))
        );
        setSelectedLocations(matchedLocations.slice(0, 5)); // Limit to 5
    };

    const clearSelection = () => {
        setSelectedLocations([]);
    };

    // Filter locations that have data for the selected parameter
    const locationsWithData = selectedLocations.filter(location => {
        const locationMeasurements = measurements[location.id] || [];
        return locationMeasurements.length > 0;
    });

    // Location component with data info
    const LocationWithDataInfo = ({ location, isSelected, isDisabled }) => {
        const dataInfo = locationDataInfo[location.id] || { hasData: false, count: 0 };

        return (
            <label className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${dataInfo.hasData
                ? 'bg-green-50 border-green-200 hover:bg-green-100'
                : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                } border ${isSelected ? 'ring-2 ring-blue-500' : ''}`}>
                <div className="flex items-center space-x-2 flex-1">
                    <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => handleLocationToggle(location)}
                        disabled={isDisabled}
                        className="rounded text-blue-600"
                    />
                    <span className="text-sm font-medium">{location.name}</span>
                </div>
                <div className="text-xs ml-2">
                    {dataInfo.hasData ? (
                        <span className="text-green-600 font-medium">
                            ✓ {dataInfo.count.toLocaleString()} pts
                        </span>
                    ) : (
                        <span className="text-gray-400">No data</span>
                    )}
                </div>
            </label>
        );
    };

    // Comparison Summary Component
    const ComparisonSummary = ({ selectedLocations, measurements, parameter }) => {
        if (selectedLocations.length === 0) return null;

        return (
            <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <h3 className="font-medium mb-3">Comparison Summary - {parameter.display_name}</h3>
                <div className="overflow-x-auto">
                    <table className="min-w-full">
                        <thead>
                            <tr className="border-b border-gray-300">
                                <th className="text-left p-2 font-medium">Location</th>
                                <th className="text-left p-2 font-medium">Metro Area</th>
                                <th className="text-left p-2 font-medium">Data Points</th>
                                <th className="text-left p-2 font-medium">Latest Value</th>
                                <th className="text-left p-2 font-medium">Average</th>
                            </tr>
                        </thead>
                        <tbody>
                            {selectedLocations.map(location => {
                                const locationData = measurements[location.id] || [];
                                const latest = locationData[0]?.value;
                                const average = locationData.length > 0
                                    ? locationData.reduce((sum, m) => sum + m.value, 0) / locationData.length
                                    : 0;

                                return (
                                    <tr key={location.id} className="border-b border-gray-200">
                                        <td className="p-2 font-medium">{location.name}</td>
                                        <td className="p-2 text-gray-600">{location.locality || 'N/A'}</td>
                                        <td className="p-2">
                                            <span className={locationData.length > 0 ? 'text-green-600' : 'text-red-500'}>
                                                {locationData.length.toLocaleString()}
                                            </span>
                                        </td>
                                        <td className="p-2">
                                            {latest ? `${latest.toFixed(2)} ${parameter.unit}` : 'N/A'}
                                        </td>
                                        <td className="p-2">
                                            {average ? `${average.toFixed(2)} ${parameter.unit}` : 'N/A'}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>
        );
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
                    Air Quality Trends Comparison
                    <span className="text-sm text-gray-500 ml-2">(All available historical data)</span>
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

                        {/* Selection Status */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Selection Status
                            </label>
                            <div className="p-2 bg-gray-50 rounded-md">
                                <p className="text-sm">
                                    <span className="font-medium">{selectedLocations.length}/5</span> locations selected
                                </p>
                                {selectedLocations.length > 0 && (
                                    <p className="text-xs text-gray-600 mt-1">
                                        {locationsWithData.length} have data for {selectedParameter?.display_name}
                                    </p>
                                )}
                                {selectedLocations.length > 0 && (
                                    <button
                                        onClick={clearSelection}
                                        className="text-xs text-red-600 hover:text-red-800 mt-1"
                                    >
                                        Clear all selections
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Predefined Sets */}
                    <div className="mt-6">
                        <h4 className="font-medium text-gray-700 mb-2">Quick Comparisons:</h4>
                        <div className="flex flex-wrap gap-2">
                            {Object.entries(predefinedSets).map(([setName, locationNames]) => (
                                <button
                                    key={setName}
                                    onClick={() => selectPredefinedSet(locationNames)}
                                    className="px-3 py-1 bg-blue-100 text-blue-700 rounded-md text-sm hover:bg-blue-200 transition-colors"
                                >
                                    {setName}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Search and Filter */}
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <input
                                type="text"
                                placeholder="Search locations..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-md"
                            />
                        </div>
                        <div>
                            <select
                                value={filterByMetro}
                                onChange={(e) => setFilterByMetro(e.target.value)}
                                className="w-full p-2 border border-gray-300 rounded-md"
                            >
                                <option value="all">All Metro Areas</option>
                                {metroAreas.map(metro => (
                                    <option key={metro} value={metro}>{metro}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    {/* Grouped Location Selection */}
                    <div className="mt-6">
                        <h4 className="font-medium text-gray-700 mb-3">
                            Select Locations (max 5)
                            {selectedParameter && (
                                <span className="text-sm text-gray-500 ml-2">
                                    - Green locations have data for {selectedParameter.display_name}
                                </span>
                            )}
                        </h4>
                        <div className="max-h-80 overflow-y-auto space-y-4">
                            {Object.entries(groupedLocations).map(([metro, metroLocations]) => (
                                <div key={metro} className="border rounded-lg p-4">
                                    <h5 className="font-medium text-gray-800 mb-2">
                                        {metro} ({metroLocations.length} locations)
                                    </h5>
                                    <div className="space-y-1">
                                        {metroLocations.map(location => (
                                            <LocationWithDataInfo
                                                key={location.id}
                                                location={location}
                                                isSelected={selectedLocations.find(loc => loc.id === location.id) !== undefined}
                                                isDisabled={selectedLocations.length >= 5 && !selectedLocations.find(loc => loc.id === location.id)}
                                            />
                                        ))}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Comparison Summary */}
                {selectedParameter && selectedLocations.length > 0 && (
                    <ComparisonSummary
                        selectedLocations={selectedLocations}
                        measurements={measurements}
                        parameter={selectedParameter}
                    />
                )}

                {/* Charts - ONLY SHOW CHARTS WITH DATA */}
                {selectedParameter && selectedLocations.length > 0 && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold mb-4">
                            {selectedParameter.display_name} Trends Comparison
                            {locationsWithData.length > 0 && (
                                <span className="text-sm text-gray-500 ml-2">
                                    ({locationsWithData.length} locations with data)
                                </span>
                            )}
                        </h2>

                        {locationsWithData.length > 0 ? (
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                {locationsWithData.map(location => {
                                    const locationMeasurements = measurements[location.id] || [];

                                    // Calculate data span
                                    let dataSpan = '';
                                    if (locationMeasurements.length > 0) {
                                        const oldest = new Date(locationMeasurements[locationMeasurements.length - 1]?.timestamp);
                                        const newest = new Date(locationMeasurements[0]?.timestamp);
                                        const spanYears = (newest - oldest) / (365.25 * 24 * 60 * 60 * 1000);
                                        dataSpan = spanYears > 1
                                            ? `${oldest.getFullYear()}-${newest.getFullYear()}`
                                            : `${Math.round(spanYears * 365)} days`;
                                    }

                                    return (
                                        <div key={location.id} className="bg-gray-50 p-4 rounded-lg">
                                            <PollutantChart
                                                measurements={locationMeasurements}
                                                parameter={selectedParameter}
                                                title={`${location.name}${location.locality ? ` (${location.locality})` : ''} - ${locationMeasurements.length} points${dataSpan ? ` (${dataSpan})` : ''}`}
                                            />
                                        </div>
                                    );
                                })}
                            </div>
                        ) : selectedLocations.length > 0 ? (
                            <div className="text-center py-8">
                                <div className="text-gray-400 mb-4">
                                    <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                    </svg>
                                </div>
                                <h3 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h3>
                                <p className="text-gray-500">
                                    None of the selected locations have historical data for {selectedParameter.display_name}.
                                    Try selecting locations with green checkmarks or choose a different parameter.
                                </p>
                            </div>
                        ) : null}
                    </div>
                )}

                {selectedLocations.length === 0 && (
                    <div className="bg-white rounded-lg shadow p-6 text-center">
                        <div className="text-gray-400 mb-4">
                            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                            </svg>
                        </div>
                        <h3 className="text-lg font-medium text-gray-900 mb-2">Select Locations to Compare</h3>
                        <p className="text-gray-500 mb-4">
                            Choose up to 5 locations from the grouped list above, or use the quick comparison buttons.
                        </p>
                        <p className="text-sm text-blue-600">
                            Tip: Green locations have data for the selected parameter
                        </p>
                    </div>
                )}
            </div>
        </Layout>
    );
};

export default TrendsPage;
