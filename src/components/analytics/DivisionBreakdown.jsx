/**
 * Division Breakdown Component
 *
 * Displays visitor distribution by administrative division
 */

import React from 'react';
import './DivisionBreakdown.css';

const DivisionBreakdown = ({ data, loading = false }) => {
    const total = data?.reduce((sum, item) => sum + item.count, 0) || 0;

    const renderProgressBar = (count) => {
        const percentage = total > 0 ? (count / total) * 100 : 0;
        return (
            <div className="progress-bar">
                <div
                    className="progress-fill"
                    style={{ width: `${percentage}%` }}
                ></div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="division-breakdown loading">
                <div className="breakdown-header">
                    <h3 className="breakdown-title">Visitor Distribution by Location</h3>
                </div>
                <div className="breakdown-list">
                    {[1, 2, 3, 4, 5].map((i) => (
                        <div key={i} className="breakdown-item skeleton-item">
                            <div className="skeleton skeleton-name"></div>
                            <div className="skeleton skeleton-count"></div>
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="division-breakdown empty">
                <div className="breakdown-header">
                    <h3 className="breakdown-title">Visitor Distribution by Location</h3>
                </div>
                <div className="empty-state">
                    <span className="empty-icon">📍</span>
                    <p>No location data available</p>
                </div>
            </div>
        );
    }

    return (
        <div className="division-breakdown">
            <div className="breakdown-header">
                <h3 className="breakdown-title">Visitor Distribution by Location</h3>
                <span className="total-count">{total.toLocaleString()} total</span>
            </div>
            <div className="breakdown-list">
                {data.map((item, index) => {
                    const percentage = total > 0 ? ((item.count / total) * 100).toFixed(1) : 0;
                    return (
                        <div key={item.division_id || index} className="breakdown-item">
                            <div className="item-header">
                                <div className="item-info">
                                    <span className="item-rank">#{index + 1}</span>
                                    <span className="item-name">{item.division_name}</span>
                                    {item.division_type && (
                                        <span className="item-type">{item.division_type}</span>
                                    )}
                                </div>
                                <div className="item-stats">
                                    <span className="item-count">{item.count.toLocaleString()}</span>
                                    <span className="item-percentage">{percentage}%</span>
                                </div>
                            </div>
                            {renderProgressBar(item.count)}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default DivisionBreakdown;
