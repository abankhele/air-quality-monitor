import React from 'react';
import { Doughnut } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(ArcElement, Tooltip, Legend);

const AQIGauge = ({ aqi }) => {
    const value = aqi || 0;

    // AQI categories
    const categories = [
        { max: 50, label: 'Good', color: 'rgba(0, 228, 0, 1)' },
        { max: 100, label: 'Moderate', color: 'rgba(255, 255, 0, 1)' },
        { max: 150, label: 'Unhealthy for Sensitive Groups', color: 'rgba(255, 126, 0, 1)' },
        { max: 200, label: 'Unhealthy', color: 'rgba(255, 0, 0, 1)' },
        { max: 300, label: 'Very Unhealthy', color: 'rgba(143, 63, 151, 1)' },
        { max: 500, label: 'Hazardous', color: 'rgba(126, 0, 35, 1)' }
    ];

    // Find current category
    const currentCategory = categories.find(cat => value <= cat.max) || categories[categories.length - 1];

    const data = {
        datasets: [
            {
                data: [value, 500 - value],
                backgroundColor: [
                    currentCategory.color,
                    'rgba(220, 220, 220, 0.5)'
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
                <div className="text-3xl font-bold">{value}</div>
                <div className="text-sm text-gray-500">{currentCategory.label}</div>
            </div>
        </div>
    );
};

export default AQIGauge;
