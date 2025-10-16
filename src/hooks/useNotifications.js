import { useState, useEffect, useCallback } from 'react';
import notificationService from '../services/notificationService';
import { useAuth } from '../contexts/AuthContext';

/**
 * Hook personnalisé pour gérer les notifications
 * @param {Object} options - Options de configuration
 * @returns {Object} État et fonctions pour gérer les notifications
 */
export const useNotifications = (options = {}) => {
    const {
        autoRefresh = true,
        refreshInterval = 30000, // 30 secondes
        initialLoad = true
    } = options;

    const { isAuthenticated } = useAuth();

    const [notifications, setNotifications] = useState([]);
    const [summary, setSummary] = useState({
        unread_count: 0,
        total_count: 0,
        has_high_priority: false,
        latest_notification: null
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [lastFetch, setLastFetch] = useState(null);

    /**
     * Charger les notifications depuis l'API
     */
    const loadNotifications = useCallback(async (params = {}) => {
        if (!isAuthenticated) {
            console.log('useNotifications: Utilisateur non authentifié');
            return;
        }

        try {
            setLoading(true);
            setError(null);

            console.log('useNotifications: Chargement des notifications...');

            const [notificationsData, summaryData] = await Promise.all([
                notificationService.getNotifications(params),
                notificationService.getNotificationSummary()
            ]);

            console.log('useNotifications: Données reçues:', { notificationsData, summaryData });

            // Transformer les données pour le frontend
            const transformedNotifications = notificationService.transformNotificationListForFrontend(
                notificationsData.results || notificationsData
            );

            console.log('useNotifications: Notifications transformées:', transformedNotifications);

            setNotifications(transformedNotifications);
            setSummary(summaryData);
            setLastFetch(new Date());
        } catch (err) {
            console.error('Erreur lors du chargement des notifications:', err);
            setError(err);
        } finally {
            setLoading(false);
        }
    }, [isAuthenticated]);

    /**
     * Recharger les notifications
     */
    const refreshNotifications = useCallback(() => {
        return loadNotifications();
    }, [loadNotifications]);

    /**
     * Marquer une notification comme lue
     */
    const markAsRead = useCallback(async (notificationId) => {
        try {
            await notificationService.markNotificationsAsRead([notificationId]);

            // Mettre à jour l'état local
            setNotifications(prev =>
                prev.map(notif =>
                    notif.id === notificationId
                        ? { ...notif, isRead: true, readAt: new Date() }
                        : notif
                )
            );

            // Mettre à jour le résumé
            setSummary(prev => ({
                ...prev,
                unread_count: Math.max(0, prev.unread_count - 1)
            }));

        } catch (err) {
            console.error('Erreur lors du marquage de la notification:', err);
            setError(err);
        }
    }, []);

    /**
     * Marquer toutes les notifications comme lues
     */
    const markAllAsRead = useCallback(async () => {
        try {
            await notificationService.markAllNotificationsAsRead();

            // Mettre à jour l'état local
            setNotifications(prev =>
                prev.map(notif => ({
                    ...notif,
                    isRead: true,
                    readAt: new Date()
                }))
            );

            // Mettre à jour le résumé
            setSummary(prev => ({
                ...prev,
                unread_count: 0
            }));

        } catch (err) {
            console.error('Erreur lors du marquage de toutes les notifications:', err);
            setError(err);
        }
    }, []);

    /**
     * Supprimer une notification
     */
    const deleteNotification = useCallback(async (notificationId) => {
        try {
            await notificationService.deleteNotification(notificationId);

            // Mettre à jour l'état local
            const notificationToDelete = notifications.find(n => n.id === notificationId);
            setNotifications(prev => prev.filter(notif => notif.id !== notificationId));

            // Mettre à jour le résumé
            setSummary(prev => ({
                ...prev,
                total_count: Math.max(0, prev.total_count - 1),
                unread_count: notificationToDelete && !notificationToDelete.isRead
                    ? Math.max(0, prev.unread_count - 1)
                    : prev.unread_count
            }));

        } catch (err) {
            console.error('Erreur lors de la suppression de la notification:', err);
            setError(err);
        }
    }, [notifications]);

    /**
     * Ajouter une nouvelle notification (pour les mises à jour en temps réel)
     */
    const addNotification = useCallback((newNotification) => {
        const transformedNotification = notificationService.transformNotificationForFrontend(newNotification);

        setNotifications(prev => [transformedNotification, ...prev]);
        setSummary(prev => ({
            ...prev,
            total_count: prev.total_count + 1,
            unread_count: prev.unread_count + 1,
            latest_notification: transformedNotification
        }));
    }, []);

    /**
     * Filtrer les notifications
     */
    const filterNotifications = useCallback((filterType) => {
        switch (filterType) {
            case 'unread':
                return notifications.filter(n => !n.isRead);
            case 'read':
                return notifications.filter(n => n.isRead);
            case 'high_priority':
                return notifications.filter(n => n.priority <= 2);
            default:
                return notifications;
        }
    }, [notifications]);

    /**
     * Obtenir le nombre de notifications non lues
     */
    const getUnreadCount = useCallback(() => {
        return summary.unread_count;
    }, [summary.unread_count]);

    /**
     * Vérifier s'il y a des notifications prioritaires
     */
    const hasHighPriorityNotifications = useCallback(() => {
        return summary.has_high_priority;
    }, [summary.has_high_priority]);

    // Chargement initial
    useEffect(() => {
        if (initialLoad && isAuthenticated) {
            loadNotifications();
        }
    }, [initialLoad, isAuthenticated, loadNotifications]);

    // Auto-refresh
    useEffect(() => {
        if (!autoRefresh || !isAuthenticated) return;

        const interval = setInterval(() => {
            loadNotifications();
        }, refreshInterval);

        return () => clearInterval(interval);
    }, [autoRefresh, refreshInterval, isAuthenticated, loadNotifications]);

    // Cleanup quand l'utilisateur se déconnecte
    useEffect(() => {
        if (!isAuthenticated) {
            setNotifications([]);
            setSummary({
                unread_count: 0,
                total_count: 0,
                has_high_priority: false,
                latest_notification: null
            });
            setError(null);
        }
    }, [isAuthenticated]);

    return {
        // État
        notifications,
        summary,
        loading,
        error,
        lastFetch,

        // Actions
        loadNotifications,
        refreshNotifications,
        markAsRead,
        markAllAsRead,
        deleteNotification,
        addNotification,

        // Utilitaires
        filterNotifications,
        getUnreadCount,
        hasHighPriorityNotifications
    };
};