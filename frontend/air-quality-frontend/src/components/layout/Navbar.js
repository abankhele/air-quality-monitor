import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchLocations } from '../../api';

const Navbar = () => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [showResults, setShowResults] = useState(false);
    const navigate = useNavigate();

    const handleSearch = async (query) => {
        setSearchQuery(query);
        if (query.length > 2) {
            try {
                const results = await searchLocations(query);
                setSearchResults(results.results || []);
                setShowResults(true);
            } catch (error) {
                console.error('Search error:', error);
            }
        } else {
            setShowResults(false);
        }
    };

    const handleLocationSelect = (location) => {
        navigate(`/location/${location.id}`);
        setShowResults(false);
        setSearchQuery('');
    };

    return (
        <nav className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="flex justify-between h-16">
                    <div className="flex items-center">
                        <h1 className="text-xl font-semibold text-gray-900">Air Quality Dashboard</h1>
                    </div>

                    <div className="flex items-center space-x-4">
                        {/* Search Bar */}
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search locations..."
                                value={searchQuery}
                                onChange={(e) => handleSearch(e.target.value)}
                                className="w-64 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            />

                            {/* Search Results Dropdown */}
                            {showResults && searchResults.length > 0 && (
                                <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
                                    {searchResults.map((location) => (
                                        <div
                                            key={location.id}
                                            className="px-4 py-2 hover:bg-gray-100 cursor-pointer border-b last:border-b-0"
                                            onClick={() => handleLocationSelect(location)}
                                        >
                                            <div className="font-medium">{location.name}</div>
                                            <div className="text-sm text-gray-500">{location.locality}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <button className="p-2 rounded-md text-gray-500 hover:text-gray-700 focus:outline-none">
                            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
