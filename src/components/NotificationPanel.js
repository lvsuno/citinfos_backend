import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Close as CloseIcon,
    FavoriteRounded as LikeIcon,
    CommentRounded as CommentIcon,
    ChatRounded as MessageIcon,
    PersonAddRounded as FollowIcon,
    EventRounded as EventIcon,
    CheckCircle as CheckIcon,
    Circle as UnreadIcon,
    MarkEmailRead as MarkReadIcon
} from '@mui/icons-material';
import { formatDistanceToNow } from 'date-fns';
import { fr } from 'date-fns/locale';
import styles from './NotificationPanel.module.css';

const NotificationPanel = ({ isOpen, onClose, notifications, onMarkAsRead, onMarkAllAsRead }) => {
    const navigate = useNavigate();
    const [filter, setFilter] = useState('all'); // all, unread, read

    if (!isOpen) return null;

    const getNotificationIcon = (type) => {
        // Handle both notification_type and type fields
        const notifType = type?.toLowerCase() || 'default';

        switch (notifType) {
            case 'like':
            case 'social':
                return <LikeIcon className={`${styles.notifIcon} ${styles.likeIcon}`} />;
            case 'comment':
            case 'community':
                return <CommentIcon className={`${styles.notifIcon} ${styles.commentIcon}`} />;
            case 'message':
            case 'messaging':
                return <MessageIcon className={`${styles.notifIcon} ${styles.messageIcon}`} />;
            case 'follow':
                return <FollowIcon className={`${styles.notifIcon} ${styles.followIcon}`} />;
            case 'event':
            case 'system':
                return <EventIcon className={`${styles.notifIcon} ${styles.eventIcon}`} />;
            default:
                return <CheckIcon className={`${styles.notifIcon} ${styles.defaultIcon}`} />;
        }
    };

    const getNotificationText = (notification) => {
        // Handle both old format (user, content, target) and new format (title, message, sender)
        const title = notification.title || '';
        const message = notification.message || notification.content || '';
        const senderName = notification.sender?.display_name ||
                          notification.sender?.username ||
                          notification.user?.name ||
                          'Système';

        // If we have a title, use it with the message
        if (title) {
            return (
                <span>
                    <strong>{title}</strong>
                    {message && <em> - {message.slice(0, 100)}{message.length > 100 ? '...' : ''}</em>}
                </span>
            );
        }

        // Otherwise fall back to old format
        const { type, user, content, target } = notification;

        switch (type) {
            case 'like':
                return (
                    <span>
                        <strong>{senderName}</strong> a aimé votre publication
                        {target && <em> "{target.slice(0, 50)}..."</em>}
                    </span>
                );
            case 'comment':
                return (
                    <span>
                        <strong>{senderName}</strong> a commenté votre publication
                        {content && <em> : "{content.slice(0, 100)}..."</em>}
                    </span>
                );
            case 'message':
                return (
                    <span>
                        <strong>{senderName}</strong> vous a envoyé un message
                        {content && <em> : "{content.slice(0, 80)}..."</em>}
                    </span>
                );
            case 'follow':
                return (
                    <span>
                        <strong>{senderName}</strong> a commencé à vous suivre
                    </span>
                );
            case 'event':
                return (
                    <span>
                        <strong>Événement :</strong> {content}
                    </span>
                );
            default:
                return <span>{message || content || 'Notification'}</span>;
        }
    };

    const filteredNotifications = notifications.filter(notif => {
        // Handle both isRead and read properties
        const isRead = notif.read !== undefined ? notif.read : notif.isRead;

        if (filter === 'unread') return !isRead;
        if (filter === 'read') return isRead;
        return true;
    });

    const unreadCount = notifications.filter(n => {
        const isRead = n.read !== undefined ? n.read : n.isRead;
        return !isRead;
    }).length;

    const handleViewAll = () => {
        navigate('/notifications');
        onClose();
    };

    return (
        <div className={styles.notificationOverlay}>
            <div className={styles.notificationPanel}>
                {/* Header du panneau */}
                <div className={styles.panelHeader}>
                    <div className={styles.headerLeft}>
                        <h3 className={styles.panelTitle}>Notifications</h3>
                        {unreadCount > 0 && (
                            <span className={styles.unreadBadge}>{unreadCount}</span>
                        )}
                    </div>

                    <div className={styles.headerActions}>
                        {unreadCount > 0 && (
                            <button
                                className={styles.markAllReadBtn}
                                onClick={onMarkAllAsRead}
                                title="Marquer tout comme lu"
                            >
                                <MarkReadIcon />
                            </button>
                        )}
                        <button
                            className={styles.closeBtn}
                            onClick={onClose}
                            title="Fermer"
                        >
                            <CloseIcon />
                        </button>
                    </div>
                </div>

                {/* Filtres */}
                <div className={styles.filterTabs}>
                    <button
                        className={`${styles.filterTab} ${filter === 'all' ? styles.active : ''}`}
                        onClick={() => setFilter('all')}
                    >
                        Toutes ({notifications.length})
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === 'unread' ? styles.active : ''}`}
                        onClick={() => setFilter('unread')}
                    >
                        Non lues ({unreadCount})
                    </button>
                    <button
                        className={`${styles.filterTab} ${filter === 'read' ? styles.active : ''}`}
                        onClick={() => setFilter('read')}
                    >
                        Lues ({notifications.length - unreadCount})
                    </button>
                </div>

                {/* Liste des notifications */}
                <div className={styles.notificationsList}>
                    {filteredNotifications.length > 0 ? (
                        filteredNotifications.map((notification) => {
                            const isRead = notification.read !== undefined ? notification.read : notification.isRead;
                            const createdAt = notification.timestamp || notification.createdAt;

                            return (
                                <div
                                    key={notification.id}
                                    className={`${styles.notificationItem} ${!isRead ? styles.unread : styles.read}`}
                                    onClick={() => !isRead && onMarkAsRead(notification.id)}
                                >
                                    <div className={styles.notifContent}>
                                        <div className={styles.notifIconContainer}>
                                            {getNotificationIcon(notification.notification_type || notification.type)}
                                        </div>

                                        <div className={styles.notifBody}>
                                            <div className={styles.notifText}>
                                                {getNotificationText(notification)}
                                            </div>
                                            <div className={styles.notifTime}>
                                                {formatDistanceToNow(new Date(createdAt), {
                                                    addSuffix: true,
                                                    locale: fr
                                                })}
                                            </div>
                                        </div>

                                        <div className={styles.notifStatus}>
                                            {isRead ? (
                                                <CheckIcon className={styles.readIcon} />
                                            ) : (
                                                <UnreadIcon className={styles.unreadIcon} />
                                            )}
                                        </div>
                                    </div>

                                    {(notification.sender?.avatar || notification.user?.avatar) && (
                                        <div className={styles.notifAvatar}>
                                            <img
                                                src={notification.sender?.avatar || notification.user?.avatar}
                                                alt={notification.sender?.display_name || notification.user?.name || 'User'}
                                                onError={(e) => {
                                                    e.target.style.display = 'none';
                                                }}
                                            />
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    ) : (
                        <div className={styles.emptyState}>
                            <div className={styles.emptyIcon}>🔔</div>
                            <h4>Aucune notification</h4>
                            <p>
                                {filter === 'unread'
                                    ? 'Toutes vos notifications ont été lues !'
                                    : filter === 'read'
                                        ? 'Aucune notification lue pour le moment.'
                                        : 'Vous n\'avez pas encore de notifications.'
                                }
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer avec actions */}
                {filteredNotifications.length > 0 && (
                    <div className={styles.panelFooter}>
                        <button className={styles.viewAllBtn} onClick={handleViewAll}>
                            Voir toutes les notifications
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationPanel;