import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const AQIGauge = ({ aqi }) => {
    const value = aqi || 0;

    const getAQIInfo = (aqi) => {
        if (aqi <= 50) return { label: 'Good', color: 'rgba(0, 228, 0, 1)', textColor: 'text-green-600' };
        if (aqi <= 100) return { label: 'Moderate', color: 'rgba(255, 255, 0, 1)', textColor: 'text-yellow-600' };
        if (aqi <= 150) return { label: 'Unhealthy for Sensitive Groups', color: 'rgba(255, 126, 0, 1)', textColor: 'text-orange-600' };
        if (aqi <= 200) return { label: 'Unhealthy', color: 'rgba(255, 0, 0, 1)', textColor: 'text-red-600' };
        if (aqi <= 300) return { label: 'Very Unhealthy', color: 'rgba(143, 63, 151, 1)', textColor: 'text-purple-600' };
        return { label: 'Hazardous', color: 'rgba(126, 0, 35, 1)', textColor: 'text-red-800' };
    };

    const aqiInfo = getAQIInfo(value);

    const data = {
        datasets: [
            {
                data: [value, Math.max(0, 500 - value)],
                backgroundColor: [
                    aqiInfo.color,
                    'rgba(220, 220, 220, 0.3)'
                ],
                borderWidth: 0,
                circumference: 180,
                rotation: 270,
            }
        ]
    };

    const options = {
        cutout: '70%',
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                enabled: false
            }
        },
        maintainAspectRatio: false
    };

    return (
        <div className="relative h-40">
            <Doughnut data={data} options={options} />
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className={`text-3xl font-bold ${aqiInfo.textColor}`}>{value}</div>
                <div className="text-sm text-gray-600 text-center px-2">{aqiInfo.label}</div>
            </div>
        </div>
    );
};

export default AQIGauge;
