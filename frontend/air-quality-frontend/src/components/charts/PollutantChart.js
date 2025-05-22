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

const PollutantChart = ({ measurements, parameter }) => {
    if (!measurements || measurements.length === 0) {
        return <div className="text-center p-4">No data available</div>;
    }

    const data = {
        labels: measurements.map(m => new Date(m.timestamp).toLocaleTimeString()),
        datasets: [
            {
                label: parameter.display_name,
                data: measurements.map(m => m.value),
                borderColor: getColorForParameter(parameter.name),
                backgroundColor: getColorForParameter(parameter.name, 0.2),
                borderWidth: 2,
                tension: 0.1,
                fill: true,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: `${parameter.display_name} (${parameter.unit})`,
            },
        },
        scales: {
            y: {
                beginAtZero: true,
                title: {
                    display: true,
                    text: parameter.unit,
                },
            },
            x: {
                title: {
                    display: true,
                    text: 'Time',
                },
            },
        },
    };

    return <Line data={data} options={options} />;
};

// Helper function to get colors for different parameters
function getColorForParameter(paramName, alpha = 1) {
    const colors = {
        pm25: `rgba(255, 99, 132, ${alpha})`,
        pm10: `rgba(255, 159, 64, ${alpha})`,
        o3: `rgba(75, 192, 192, ${alpha})`,
        no2: `rgba(54, 162, 235, ${alpha})`,
        so2: `rgba(153, 102, 255, ${alpha})`,
        co: `rgba(201, 203, 207, ${alpha})`,
        default: `rgba(0, 0, 0, ${alpha})`,
    };

    return colors[paramName] || colors.default;
}

export default PollutantChart;
