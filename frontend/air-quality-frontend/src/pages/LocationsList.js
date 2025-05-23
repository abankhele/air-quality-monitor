import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Layout from '../components/layout/Layout';
import { fetchLocations } from '../api';

const LocationsList = () => {
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const itemsPerPage = 20;

    useEffect(() => {
        const getLocations = async () => {
            try {
                setLoading(true);
                const data = await fetchLocations();
                setLocations(data.results || []);
                setTotalPages(Math.ceil((data.meta?.total || 0) / itemsPerPage));
            } catch (error) {
                console.error('Error fetching locations:', error);
            } finally {
                setLoading(false);
            }
        };

        getLocations();
    }, [currentPage]);

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
                <h1 className="text-2xl font-bold text-gray-900">All Monitoring Locations</h1>

                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul className="divide-y divide-gray-200">
                        {locations.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage).map((location) => (
                            <li key={location.id}>
                                <Link
                                    to={`/location/${location.id}`}
                                    className="block hover:bg-gray-50 px-4 py-4 sm:px-6"
                                >
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center">
                                            <div className="flex-shrink-0">
                                                <div className={`w-4 h-4 rounded-full ${location.aqi <= 50 ? 'bg-green-500' :
                                                        location.aqi <= 100 ? 'bg-yellow-500' :
                                                            location.aqi <= 150 ? 'bg-orange-500' :
                                                                location.aqi <= 200 ? 'bg-red-500' :
                                                                    'bg-purple-500'
                                                    }`}></div>
                                            </div>
                                            <div className="ml-4">
                                                <div className="text-sm font-medium text-gray-900">
                                                    {location.name}
                                                </div>
                                                <div className="text-sm text-gray-500">
                                                    {location.locality}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-sm font-medium text-gray-900">
                                                AQI: {location.aqi || 'N/A'}
                                            </div>
                                            <div className="text-sm text-gray-500">
                                                {location.sensors?.length || 0} sensors
                                            </div>
                                        </div>
                                    </div>
                                </Link>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Pagination */}
                <div className="flex justify-center">
                    <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                        <button
                            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                            disabled={currentPage === 1}
                            className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                        >
                            Previous
                        </button>
                        <span className="relative inline-flex items-center px-4 py-2 border border-gray-300 bg-white text-sm font-medium text-gray-700">
                            Page {currentPage} of {totalPages}
                        </span>
                        <button
                            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                            disabled={currentPage === totalPages}
                            className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50"
                        >
                            Next
                        </button>
                    </nav>
                </div>
            </div>
        </Layout>
    );
};

export default LocationsList;
