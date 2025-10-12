/**
 * Visitor Stats Card Component
 *
 * Displays a single visitor statistic with icon and trend indicator
 */

import React from 'react';
import './VisitorStatsCard.css';

const VisitorStatsCard = ({
    title,
    value,
    change,
    changeType = 'neutral', // 'increase', 'decrease', 'neutral'
    icon,
    subtitle,
    loading = false
}) => {
    const renderChangeIndicator = () => {
        if (!change && change !== 0) return null;

        const isPositive = change > 0;
        const isNegative = change < 0;

        let changeClass = 'change-neutral';
        let arrow = '';

        if (changeType === 'increase') {
            changeClass = isPositive ? 'change-positive' : 'change-negative';
            arrow = isPositive ? '↑' : '↓';
        } else if (changeType === 'decrease') {
            changeClass = isNegative ? 'change-positive' : 'change-negative';
            arrow = isNegative ? '↓' : '↑';
        }

        return (
            <span className={`change-indicator ${changeClass}`}>
                {arrow} {Math.abs(change)}%
            </span>
        );
    };

    if (loading) {
        return (
            <div className="visitor-stats-card loading">
                <div className="card-content">
                    <div className="skeleton skeleton-title"></div>
                    <div className="skeleton skeleton-value"></div>
                    <div className="skeleton skeleton-subtitle"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="visitor-stats-card">
            <div className="card-header">
                {icon && <span className="card-icon">{icon}</span>}
                <h3 className="card-title">{title}</h3>
            </div>
            <div className="card-content">
                <div className="stat-value">{value?.toLocaleString() || 0}</div>
                {renderChangeIndicator()}
                {subtitle && <p className="stat-subtitle">{subtitle}</p>}
            </div>
        </div>
    );
};

export default VisitorStatsCard;
