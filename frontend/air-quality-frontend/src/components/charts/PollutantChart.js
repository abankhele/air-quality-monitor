import React from 'react';
import { Line } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

const getColorForParameter = (paramName, alpha = 1) => {
    const colors = {
        pm25: `rgba(255, 99, 132, ${alpha})`,
        pm10: `rgba(255, 159, 64, ${alpha})`,
        o3: `rgba(75, 192, 192, ${alpha})`,
        no2: `rgba(54, 162, 235, ${alpha})`,
        so2: `rgba(153, 102, 255, ${alpha})`,
        co: `rgba(201, 203, 207, ${alpha})`,
        default: `rgba(99, 102, 241, ${alpha})`,
    };
    return colors[paramName] || colors.default;
};

const PollutantChart = ({ measurements, parameter, title }) => {
    if (!measurements || measurements.length === 0) {
        return (
            <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
                <div className="text-center">
                    <p className="text-gray-500">No data available</p>
                    <p className="text-sm text-gray-400">Try selecting a different time range</p>
                </div>
            </div>
        );
    }

    const data = {
        labels: measurements.map(m => new Date(m.timestamp).toLocaleDateString()),
        datasets: [
            {
                label: parameter?.display_name || 'Measurement',
                data: measurements.map(m => m.value),
                borderColor: getColorForParameter(parameter?.name),
                backgroundColor: getColorForParameter(parameter?.name, 0.1),
                borderWidth: 2,
                tension: 0.1,
                fill: true,
                pointRadius: 3,
                pointHoverRadius: 5,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: title || `${parameter?.display_name || 'Measurement'} (${parameter?.unit || ''})`,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: parameter?.unit || 'Value',
                },
            },
            x: {
                title: {
                    display: true,
                    text: 'Date',
                },
            },
        },
    };

    return (
        <div className="h-64">
            <Line data={data} options={options} />
        </div>
    );
};

export default PollutantChart;
