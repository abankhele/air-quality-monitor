import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchLocations } from '../../api';

// Fix for default markers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const getMarkerColor = (aqi) => {
    if (!aqi) return '#gray';
    if (aqi <= 50) return '#00e400';
    if (aqi <= 100) return '#ffff00';
    if (aqi <= 150) return '#ff7e00';
    if (aqi <= 200) return '#ff0000';
    if (aqi <= 300) return '#8f3f97';
    return '#7e0023';
};

const createCustomIcon = (aqi) => {
    const color = getMarkerColor(aqi);
    return L.divIcon({
        className: 'custom-div-icon',
        html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 4px rgba(0,0,0,0.3);"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
    });
};

const AirQualityMap = ({ onLocationSelect }) => {
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getLocations = async () => {
            try {
                setLoading(true);
                const data = await fetchLocations();
                setLocations(data.results || []);
            } catch (err) {
                console.error('Error fetching locations:', err);
                setError('Failed to load locations');
            } finally {
                setLoading(false);
            }
        };

        getLocations();
    }, []);

    if (loading) {
        return (
            <div className="flex justify-center items-center h-full">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (error) {
        return <div className="text-red-500 text-center p-4">{error}</div>;
    }

    return (
        <div className="h-full w-full rounded-lg overflow-hidden shadow-lg">
            <MapContainer
                center={[39.8283, -98.5795]}
                zoom={4}
                style={{ height: '100%', width: '100%' }}
                className="z-10"
            >
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {locations.map((location) => (
                    <Marker
                        key={location.id}
                        position={[location.latitude, location.longitude]}
                        icon={createCustomIcon(location.aqi)}
                    >
                        <Popup>
                            <div className="p-2">
                                <h3 className="font-bold text-lg">{location.name}</h3>
                                <p className="text-sm text-gray-600">{location.locality}</p>
                                <div className="mt-2">
                                    <span className="text-sm font-medium">AQI: </span>
                                    <span className={`font-bold ${location.aqi <= 50 ? 'text-green-600' :
                                            location.aqi <= 100 ? 'text-yellow-600' :
                                                location.aqi <= 150 ? 'text-orange-600' :
                                                    location.aqi <= 200 ? 'text-red-600' :
                                                        location.aqi <= 300 ? 'text-purple-600' : 'text-red-800'
                                        }`}>
                                        {location.aqi || 'N/A'}
                                    </span>
                                </div>
                                <button
                                    onClick={() => onLocationSelect && onLocationSelect(location)}
                                    className="mt-2 px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                                >
                                    View Details
                                </button>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
};

export default AirQualityMap;
