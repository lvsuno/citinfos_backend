import apiService from './apiService';

class NotificationService {
    /**
     * Récupérer toutes les notifications de l'utilisateur
     * @param {Object} params - Paramètres de filtrage
     * @returns {Promise} Liste des notifications
     */
    async getNotifications(params = {}) {
        try {
            const queryParams = new URLSearchParams();

            if (params.is_read !== undefined) {
                queryParams.append('is_read', params.is_read);
            }
            if (params.type) {
                queryParams.append('type', params.type);
            }
            if (params.priority) {
                queryParams.append('priority', params.priority);
            }

            const url = `/notifications/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            console.log('NotificationService: Appel API GET', url);

            const response = await apiService.get(url);
            console.log('NotificationService: Réponse reçue', response.data);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la récupération des notifications:', error);
            console.error('Détails de l\'erreur:', error.response?.data);
            throw error;
        }
    }

    /**
     * Récupérer le résumé des notifications (nombre non lues, dernière notification, etc.)
     * @returns {Promise} Résumé des notifications
     */
    async getNotificationSummary() {
        try {
            console.log('NotificationService: Appel API GET /notifications/summary/');
            const response = await apiService.get('/notifications/summary/');
            console.log('NotificationService: Résumé reçu', response.data);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la récupération du résumé des notifications:', error);
            console.error('Détails de l\'erreur:', error.response?.data);
            throw error;
        }
    }

    /**
     * Récupérer le résumé inline des notifications (pour embed dans d'autres réponses)
     * @returns {Promise} Résumé inline
     */
    async getInlineNotificationSummary() {
        try {
            const response = await apiService.get('/notifications/inline/');
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la récupération du résumé inline:', error);
            throw error;
        }
    }

    /**
     * Récupérer une notification spécifique
     * @param {string} notificationId - ID de la notification
     * @returns {Promise} Détails de la notification
     */
    async getNotificationDetail(notificationId) {
        try {
            const response = await apiService.get(`/notifications/${notificationId}/`);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la récupération de la notification:', error);
            throw error;
        }
    }

    /**
     * Marquer des notifications comme lues
     * @param {Array} notificationIds - IDs des notifications à marquer (optionnel, toutes si vide)
     * @returns {Promise} Résultat de l'opération
     */
    async markNotificationsAsRead(notificationIds = []) {
        try {
            const data = notificationIds.length > 0 ? { notification_ids: notificationIds } : {};
            const response = await apiService.post('/notifications/mark-read/', data);
            return response.data;
        } catch (error) {
            console.error('Erreur lors du marquage des notifications:', error);
            throw error;
        }
    }

    /**
     * Marquer toutes les notifications comme lues
     * @returns {Promise} Résultat de l'opération
     */
    async markAllNotificationsAsRead() {
        return this.markNotificationsAsRead([]);
    }

    /**
     * Supprimer une notification
     * @param {string} notificationId - ID de la notification à supprimer
     * @returns {Promise} Résultat de l'opération
     */
    async deleteNotification(notificationId) {
        try {
            const response = await apiService.delete(`/notifications/${notificationId}/delete/`);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la suppression de la notification:', error);
            throw error;
        }
    }

    /**
     * Transformer les données du backend vers le format attendu par le frontend
     * @param {Object} backendNotification - Notification du backend
     * @returns {Object} Notification formatée pour le frontend
     */
    transformNotificationForFrontend(backendNotification) {
        return {
            id: backendNotification.id,
            type: backendNotification.notification_type,
            user: backendNotification.sender ? {
                id: backendNotification.sender.id,
                name: `${backendNotification.sender.user.first_name || ''} ${backendNotification.sender.user.last_name || ''}`.trim()
                    || backendNotification.sender.user.username,
                avatar: backendNotification.sender.profile_picture || null
            } : null,
            title: backendNotification.title,
            content: backendNotification.message,
            target: backendNotification.extra_data?.target || null,
            priority: backendNotification.priority,
            createdAt: new Date(backendNotification.created_at),
            isRead: backendNotification.is_read,
            readAt: backendNotification.read_at ? new Date(backendNotification.read_at) : null,
            expiresAt: backendNotification.expires_at ? new Date(backendNotification.expires_at) : null,
            extraData: backendNotification.extra_data || {}
        };
    }

    /**
     * Transformer une liste de notifications du backend
     * @param {Array} backendNotifications - Liste des notifications du backend
     * @returns {Array} Liste des notifications formatées
     */
    transformNotificationListForFrontend(backendNotifications) {
        if (!Array.isArray(backendNotifications)) {
            return [];
        }
        return backendNotifications.map(notification =>
            this.transformNotificationForFrontend(notification)
        );
    }

    /**
     * Créer une notification de test (pour le développement)
     * @param {Object} notificationData - Données de la notification
     * @returns {Promise} Notification créée
     */
    async createTestNotification(notificationData) {
        try {
            const response = await apiService.post('/notifications/test/create/', notificationData);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la création de la notification de test:', error);
            throw error;
        }
    }

    /**
     * Créer plusieurs notifications de test en une fois
     * @param {Object} params - Paramètres pour la création en lot
     * @returns {Promise} Notifications créées
     */
    async createBulkTestNotifications(params = {}) {
        try {
            const response = await apiService.post('/notifications/test/bulk/', params);
            return response.data;
        } catch (error) {
            console.error('Erreur lors de la création des notifications de test en lot:', error);
            throw error;
        }
    }
}

// Export de l'instance singleton
const notificationService = new NotificationService();
export default notificationService;

// Export des types de notifications pour référence
export const NOTIFICATION_TYPES = {
    LIKE: 'like',
    COMMENT: 'comment',
    FOLLOW: 'follow',
    MENTION: 'mention',
    MESSAGE: 'message',
    NEW_MESSAGE: 'new_message',
    SHARE: 'share',
    REPORT: 'report',
    REPOST: 'repost',
    SYSTEM: 'system',
    BADGE: 'badge',
    ACHIEVEMENT: 'achievement',
    WARRANTY: 'warranty',
    MAINTENANCE: 'maintenance',
    WELCOME: 'welcome',
    SECURITY_ALERT: 'security_alert',
    DIGEST: 'digest',
    COMMUNITY_INVITE: 'community_invite',
    COMMUNITY_JOIN: 'community_join',
    COMMUNITY_POST: 'community_post',
    COMMUNITY_ROLE_CHANGE: 'community_role_change',
    GEO_RESTRICTION: 'geo_restriction'
};

export const PRIORITY_LEVELS = {
    HIGH: 1,
    ELEVATED: 2,
    NORMAL: 3,
    LOW: 4,
    VERY_LOW: 5
};