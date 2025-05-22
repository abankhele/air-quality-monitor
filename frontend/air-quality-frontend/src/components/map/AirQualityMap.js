import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { fetchLocations } from '../../api';
import L from 'leaflet';

// Fix for Leaflet marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const getMarkerColor = (aqi) => {
    if (!aqi) return 'gray';
    if (aqi <= 50) return 'green';
    if (aqi <= 100) return 'yellow';
    if (aqi <= 150) return 'orange';
    if (aqi <= 200) return 'red';
    if (aqi <= 300) return 'purple';
    return 'maroon';
};

const AirQualityMap = () => {
    const [locations, setLocations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const getLocations = async () => {
            try {
                setLoading(true);
                const data = await fetchLocations();
                setLocations(data);
            } catch (err) {
                console.error('Error fetching locations:', err);
                setError('Failed to load locations');
            } finally {
                setLoading(false);
            }
        };

        getLocations();
    }, []);

    if (loading) return <div className="flex justify-center items-center h-full">Loading map data...</div>;
    if (error) return <div className="text-red-500">{error}</div>;

    return (
        <div className="h-full w-full rounded-lg overflow-hidden shadow-lg">
            <MapContainer center={[39.8283, -98.5795]} zoom={4} style={{ height: '100%', width: '100%' }}>
                <TileLayer
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                {locations.map((location) => (
                    <Marker
                        key={location.id}
                        position={[location.latitude, location.longitude]}
                        icon={L.divIcon({
                            className: 'custom-marker',
                            html: `<div style="background-color: ${getMarkerColor(location.aqi)}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
                            iconSize: [16, 16],
                            iconAnchor: [8, 8]
                        })}
                    >
                        <Popup>
                            <div>
                                <h3 className="font-bold">{location.name}</h3>
                                <p>AQI: {location.aqi || 'N/A'}</p>
                                <a href={`/location/${location.id}`} className="text-blue-500 hover:underline">View Details</a>
                            </div>
                        </Popup>
                    </Marker>
                ))}
            </MapContainer>
        </div>
    );
};

export default AirQualityMap;
