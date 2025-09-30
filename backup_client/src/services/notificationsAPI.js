import BaseAPIService from './baseAPI';

class NotificationsAPI extends BaseAPIService {
    constructor() {
        super();
    }

    // Get all notifications
    async getNotifications(params = {}) {
        const response = await this.get('/notifications/', { params });
        return response;
    }

    // Get notification summary
    async getNotificationSummary() {
        const response = await this.get('/notifications/summary/');
        return response;
    }

    // Get inline notification data
    async getInlineNotifications() {
        const response = await this.get('/notifications/inline/');
        return response;
    }

    // Get specific notification details (with content object)
    async getNotificationDetail(notificationId) {
        const response = await this.get(`/notifications/${notificationId}/`);
        return response;
    }

    // Mark notifications as read
    async markAsRead(notificationIds = []) {
        const response = await this.post('/notifications/mark-read/', {
            notification_ids: notificationIds
        });
        return response;
    }

    // Delete notification
    async deleteNotification(notificationId) {
        const response = await this.delete(`/notifications/${notificationId}/delete/`);
        return response;
    }

    // Process moderator nomination (redirects to communities API)
    async processModeratorNomination(data) {
        const response = await this.post('/communities/process-moderator-nomination/', data);
        return response;
    }

    // WebSocket-related methods
    subscribeToNotifications(callback) {
        // This would integrate with the existing notificationWebSocket service
        const ws = new WebSocket(`ws://localhost:8000/ws/notifications/`);

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            callback(data);
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };

        return ws;
    }

    // Utility methods
    getNotificationTypeIcon(type) {
        const icons = {
            'like': '👍',
            'comment': '💬',
            'follow': '👥',
            'mention': '@',
            'message': '✉️',
            'new_message': '📨',
            'share': '🔄',
            'report': '⚠️',
            'repost': '🔁',
            'system': '⚙️',
            'badge': '🏆',
            'achievement': '🎯',
            'warranty': '🛡️',
            'maintenance': '🔧',
            'equipment_shared': '📦',
            'equipment_request': '📋',
            'equipment_approved': '✅',
            'welcome': '👋',
            'security_alert': '🔒',
            'digest': '📊',
            'moderator_nomination': '👑',
            'moderator_accepted': '✅',
            'moderator_declined': '❌'
        };
        return icons[type] || '📬';
    }

    getNotificationPriorityColor(priority) {
        switch (priority) {
            case 1: return '#f44336'; // High - Red
            case 2: return '#ff9800'; // Elevated - Orange
            case 3: return '#2196f3'; // Normal - Blue
            case 4: return '#4caf50'; // Low - Green
            case 5: return '#9e9e9e'; // Very Low - Grey
            default: return '#2196f3';
        }
    }

    formatTimeAgo(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) {
            return 'Just now';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `${minutes}m ago`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `${hours}h ago`;
        } else if (diffInSeconds < 604800) {
            const days = Math.floor(diffInSeconds / 86400);
            return `${days}d ago`;
        } else {
            return date.toLocaleDateString();
        }
    }
}

export default new NotificationsAPI();
