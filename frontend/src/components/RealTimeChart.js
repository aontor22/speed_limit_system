import React from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Filler,
  Legend
);

const RealTimeChart = ({ dataArray, label, color }) => {
  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.1)' },
        ticks: { color: '#94a3b8' }
      },
      x: {
        display: false, // Hide timestamps on x-axis for cleaner look
      }
    },
    plugins: {
      legend: { display: false },
    },
    animation: { duration: 0 } // Critical for real-time performance
  };

  const data = {
    labels: dataArray.map((_, i) => i),
    datasets: [
      {
        label: label,
        data: dataArray,
        borderColor: color,
        backgroundColor: `${color}33`,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
      },
    ],
  };

  return <Line options={options} data={data} />;
};

export default RealTimeChart;