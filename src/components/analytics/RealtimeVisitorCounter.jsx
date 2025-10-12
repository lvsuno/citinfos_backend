/**
 * Real-Time Visitor Counter Component
 *
 * Displays current online visitors with WebSocket updates
 */

import React, { useState, useEffect, useRef } from 'react';
import './RealtimeVisitorCounter.css';

const RealtimeVisitorCounter = ({
    communityId = null,
    websocketUrl = null
}) => {
    const [visitorCount, setVisitorCount] = useState(0);
    const [isConnected, setIsConnected] = useState(false);
    const [recentVisitors, setRecentVisitors] = useState([]);
    const websocketRef = useRef(null);

    useEffect(() => {
        // Connect to WebSocket
        connectWebSocket();

        return () => {
            // Cleanup on unmount
            if (websocketRef.current) {
                websocketRef.current.close();
            }
        };
    }, [communityId, websocketUrl]);

    const connectWebSocket = () => {
        const wsUrl = websocketUrl || getWebSocketURL();

        try {
            const ws = new WebSocket(wsUrl);
            websocketRef.current = ws;

            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                setIsConnected(true);

                // Request initial count
                ws.send(JSON.stringify({
                    type: 'request_count',
                    community_id: communityId
                }));
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setIsConnected(false);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);

                // Attempt to reconnect after 5 seconds
                setTimeout(() => {
                    connectWebSocket();
                }, 5000);
            };
        } catch (error) {
            console.error('Error creating WebSocket:', error);
        }
    };

    const handleWebSocketMessage = (data) => {
        switch (data.type) {
            case 'visitor_count':
                setVisitorCount(data.count || 0);
                break;

            case 'visitor_joined':
                setVisitorCount(prev => prev + 1);
                addRecentVisitor({
                    action: 'joined',
                    timestamp: new Date(),
                    ...data.visitor
                });
                break;

            case 'visitor_left':
                setVisitorCount(prev => Math.max(0, prev - 1));
                addRecentVisitor({
                    action: 'left',
                    timestamp: new Date(),
                    ...data.visitor
                });
                break;

            default:
                break;
        }
    };

    const addRecentVisitor = (visitor) => {
        setRecentVisitors(prev => {
            const updated = [visitor, ...prev].slice(0, 5); // Keep last 5
            return updated;
        });
    };

    const getWebSocketURL = () => {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const path = communityId
            ? `/ws/analytics/visitors/?community_id=${communityId}`
            : '/ws/analytics/visitors/';
        return `${protocol}//${host}${path}`;
    };

    const getStatusColor = () => {
        if (visitorCount === 0) return '#95a5a6';
        if (visitorCount < 10) return '#3498db';
        if (visitorCount < 50) return '#2ecc71';
        if (visitorCount < 100) return '#f39c12';
        return '#e74c3c';
    };

    return (
        <div className="realtime-visitor-counter">
            <div className="counter-header">
                <h3 className="counter-title">
                    <span className="pulse-dot" style={{ backgroundColor: getStatusColor() }}></span>
                    Live Visitors
                </h3>
                <span className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
                    {isConnected ? '● Connected' : '○ Disconnected'}
                </span>
            </div>

            <div className="counter-main">
                <div className="visitor-count" style={{ color: getStatusColor() }}>
                    {visitorCount.toLocaleString()}
                </div>
                <p className="counter-subtitle">
                    {visitorCount === 1 ? 'visitor online now' : 'visitors online now'}
                </p>
            </div>

            {recentVisitors.length > 0 && (
                <div className="recent-activity">
                    <h4 className="activity-title">Recent Activity</h4>
                    <div className="activity-list">
                        {recentVisitors.map((visitor, index) => (
                            <div
                                key={`${visitor.timestamp}-${index}`}
                                className={`activity-item ${visitor.action}`}
                            >
                                <span className="activity-icon">
                                    {visitor.action === 'joined' ? '→' : '←'}
                                </span>
                                <span className="activity-text">
                                    Visitor {visitor.action === 'joined' ? 'joined' : 'left'}
                                </span>
                                <span className="activity-time">
                                    {formatTime(visitor.timestamp)}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};

const formatTime = (date) => {
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);

    if (diffSecs < 60) return 'just now';
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
    return date.toLocaleTimeString();
};

export default RealtimeVisitorCounter;
