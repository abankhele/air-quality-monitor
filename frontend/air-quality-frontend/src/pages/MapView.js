import React from 'react';
import Layout from '../components/layout/Layout';
import AirQualityMap from '../components/map/AirQualityMap';

const MapView = () => {
    return (
        <Layout>
            <div className="h-full">
                <h1 className="text-2xl font-bold text-gray-900 mb-4">Air Quality Map</h1>
                <div className="bg-white rounded-lg shadow p-4 h-96">
                    <AirQualityMap />
                </div>
            </div>
        </Layout>
    );
};

export default MapView;
