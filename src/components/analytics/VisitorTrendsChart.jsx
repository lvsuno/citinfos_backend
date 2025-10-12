/**
 * Visitor Trends Chart Component
 *
 * Displays visitor trends over time using Chart.js
 */

import React, { useEffect, useRef } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';
import './VisitorTrendsChart.css';

// Register Chart.js components
ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const VisitorTrendsChart = ({
    data,
    type = 'line', // 'line' or 'bar'
    title = 'Visitor Trends',
    loading = false
}) => {
    const chartRef = useRef(null);

    const chartData = {
        labels: data?.labels || [],
        datasets: [
            {
                label: 'Total Visitors',
                data: data?.total || [],
                borderColor: '#1877f2',
                backgroundColor: type === 'line'
                    ? 'rgba(24, 119, 242, 0.1)'
                    : 'rgba(24, 119, 242, 0.6)',
                fill: type === 'line',
                tension: 0.4,
            },
            {
                label: 'Authenticated',
                data: data?.authenticated || [],
                borderColor: '#00a400',
                backgroundColor: type === 'line'
                    ? 'rgba(0, 164, 0, 0.1)'
                    : 'rgba(0, 164, 0, 0.6)',
                fill: type === 'line',
                tension: 0.4,
            },
            {
                label: 'Anonymous',
                data: data?.anonymous || [],
                borderColor: '#f59e0b',
                backgroundColor: type === 'line'
                    ? 'rgba(245, 158, 11, 0.1)'
                    : 'rgba(245, 158, 11, 0.6)',
                fill: type === 'line',
                tension: 0.4,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: {
                    usePointStyle: true,
                    padding: 15,
                    font: {
                        size: 12,
                        weight: '600',
                    },
                },
            },
            title: {
                display: false,
            },
            tooltip: {
                mode: 'index',
                intersect: false,
                backgroundColor: 'rgba(0, 0, 0, 0.8)',
                padding: 12,
                titleFont: {
                    size: 13,
                    weight: '600',
                },
                bodyFont: {
                    size: 12,
                },
                callbacks: {
                    label: function(context) {
                        let label = context.dataset.label || '';
                        if (label) {
                            label += ': ';
                        }
                        label += context.parsed.y.toLocaleString();
                        return label;
                    },
                },
            },
        },
        scales: {
            x: {
                grid: {
                    display: false,
                },
                ticks: {
                    font: {
                        size: 11,
                    },
                },
            },
            y: {
                beginAtZero: true,
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)',
                },
                ticks: {
                    font: {
                        size: 11,
                    },
                    callback: function(value) {
                        return value.toLocaleString();
                    },
                },
            },
        },
        interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false,
        },
    };

    if (loading) {
        return (
            <div className="visitor-trends-chart loading">
                <div className="chart-header">
                    <h3 className="chart-title">{title}</h3>
                </div>
                <div className="chart-container">
                    <div className="loading-skeleton"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="visitor-trends-chart">
            <div className="chart-header">
                <h3 className="chart-title">{title}</h3>
            </div>
            <div className="chart-container">
                {type === 'line' ? (
                    <Line ref={chartRef} data={chartData} options={options} />
                ) : (
                    <Bar ref={chartRef} data={chartData} options={options} />
                )}
            </div>
        </div>
    );
};

export default VisitorTrendsChart;
