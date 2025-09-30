import React, { useState } from 'react';
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
    const [filter, setFilter] = useState('all'); // all, unread, read

    if (!isOpen) return null;

    const getNotificationIcon = (type) => {
        switch (type) {
            case 'like':
                return <LikeIcon className={`${styles.notifIcon} ${styles.likeIcon}`} />;
            case 'comment':
                return <CommentIcon className={`${styles.notifIcon} ${styles.commentIcon}`} />;
            case 'message':
                return <MessageIcon className={`${styles.notifIcon} ${styles.messageIcon}`} />;
            case 'follow':
                return <FollowIcon className={`${styles.notifIcon} ${styles.followIcon}`} />;
            case 'event':
                return <EventIcon className={`${styles.notifIcon} ${styles.eventIcon}`} />;
            default:
                return <CheckIcon className={`${styles.notifIcon} ${styles.defaultIcon}`} />;
        }
    };

    const getNotificationText = (notification) => {
        const { type, user, content, target } = notification;

        switch (type) {
            case 'like':
                return (
                    <span>
                        <strong>{user.name}</strong> a aimé votre publication
                        {target && <em> "{target.slice(0, 50)}..."</em>}
                    </span>
                );
            case 'comment':
                return (
                    <span>
                        <strong>{user.name}</strong> a commenté votre publication
                        {content && <em> : "{content.slice(0, 100)}..."</em>}
                    </span>
                );
            case 'message':
                return (
                    <span>
                        <strong>{user.name}</strong> vous a envoyé un message
                        {content && <em> : "{content.slice(0, 80)}..."</em>}
                    </span>
                );
            case 'follow':
                return (
                    <span>
                        <strong>{user.name}</strong> a commencé à vous suivre
                    </span>
                );
            case 'event':
                return (
                    <span>
                        <strong>Événement :</strong> {content}
                    </span>
                );
            default:
                return <span>{content}</span>;
        }
    };

    const filteredNotifications = notifications.filter(notif => {
        if (filter === 'unread') return !notif.isRead;
        if (filter === 'read') return notif.isRead;
        return true;
    });

    const unreadCount = notifications.filter(n => !n.isRead).length;

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
                        filteredNotifications.map((notification) => (
                            <div
                                key={notification.id}
                                className={`${styles.notificationItem} ${!notification.isRead ? styles.unread : styles.read
                                    }`}
                                onClick={() => !notification.isRead && onMarkAsRead(notification.id)}
                            >
                                <div className={styles.notifContent}>
                                    <div className={styles.notifIconContainer}>
                                        {getNotificationIcon(notification.type)}
                                    </div>

                                    <div className={styles.notifBody}>
                                        <div className={styles.notifText}>
                                            {getNotificationText(notification)}
                                        </div>
                                        <div className={styles.notifTime}>
                                            {formatDistanceToNow(new Date(notification.createdAt), {
                                                addSuffix: true,
                                                locale: fr
                                            })}
                                        </div>
                                    </div>

                                    <div className={styles.notifStatus}>
                                        {notification.isRead ? (
                                            <CheckIcon className={styles.readIcon} />
                                        ) : (
                                            <UnreadIcon className={styles.unreadIcon} />
                                        )}
                                    </div>
                                </div>

                                {notification.user?.avatar && (
                                    <div className={styles.notifAvatar}>
                                        <img
                                            src={notification.user.avatar}
                                            alt={notification.user.name}
                                            onError={(e) => {
                                                e.target.style.display = 'none';
                                            }}
                                        />
                                    </div>
                                )}
                            </div>
                        ))
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
                        <button className={styles.viewAllBtn}>
                            Voir toutes les notifications
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default NotificationPanel;