import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search as SearchIcon,
    Notifications as NotificationsIcon,
    Chat as ChatIcon,
    Menu as MenuIcon,
    Settings as SettingsIcon,
    Logout as LogoutIcon,
    Person as PersonIcon,
    ArrowDropDown as ArrowDropDownIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import NotificationPanel from './NotificationPanel';
import { demoNotifications, markNotificationAsRead, markAllNotificationsAsRead } from '../data/notifications';
import styles from './TopBar.module.css';

const TopBar = ({ onToggleSidebar, onChatToggle }) => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [showProfileMenu, setShowProfileMenu] = useState(false);
    const [showNotifications, setShowNotifications] = useState(false);
    const [notifications, setNotifications] = useState(demoNotifications);

    // Debug - temporaire
    console.log('TopBar - user data:', user);
    console.log('TopBar - user avatar:', user?.avatar);

    // Debug temporaire
    React.useEffect(() => {
        console.log('Utilisateur dans TopBar:', user);
        console.log('Avatar de l\'utilisateur:', user?.avatar);
    }, [user]);

    // Obtenir les initiales du nom d'utilisateur
    const getUserInitials = () => {
        if (user?.firstName && user?.lastName) {
            return `${user.firstName[0]}${user.lastName[0]}`;
        }
        if (user?.email) {
            return user.email.substring(0, 2).toUpperCase();
        }
        return 'U';
    };

    const handleSearch = (e) => {
        e.preventDefault();
        console.log('Recherche:', searchQuery);
        // TODO: Implémenter la logique de recherche
    };

    const handleNotificationClick = () => {
        setShowNotifications(!showNotifications);
    };

    const handleNotificationClose = () => {
        setShowNotifications(false);
    };

    const handleMarkAsRead = (notificationId) => {
        setNotifications(prev => markNotificationAsRead(prev, notificationId));
    };

    const handleMarkAllAsRead = () => {
        setNotifications(prev => markAllNotificationsAsRead(prev));
    };

    const handleMessagesClick = () => {
        if (onChatToggle) {
            onChatToggle();
        } else {
            console.log('Messages clicked');
            // TODO: Fallback si onChatToggle n'est pas fourni
        }
    };

    const handleProfileClick = () => {
        setShowProfileMenu(!showProfileMenu);
    };

    const handleMyProfileClick = () => {
        navigate('/profil');
        setShowProfileMenu(false);
    };

    const handleSettingsClick = () => {
        navigate('/parametres');
        setShowProfileMenu(false);
    };

    const handleLogoutClick = () => {
        logout();
        navigate('/');
        setShowProfileMenu(false);
    };

    // Fermer les menus si on clique ailleurs
    React.useEffect(() => {
        const handleClickOutside = (event) => {
            // Gestion du menu profil
            if (showProfileMenu && !event.target.closest(`.${styles.profileContainer}`)) {
                setShowProfileMenu(false);
            }

            // Gestion des notifications - NE PAS fermer si on clique dans le panneau
            if (showNotifications &&
                !event.target.closest(`.${styles.notificationContainer}`) &&
                !event.target.closest('[class*="notificationPanel"]') &&
                !event.target.closest('[class*="filterTab"]') &&
                !event.target.closest('[class*="notificationItem"]')) {
                setShowNotifications(false);
            }
        };

        if (showProfileMenu || showNotifications) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showProfileMenu, showNotifications]);

    // Calculer le nombre de notifications non lues
    const unreadCount = notifications.filter(n => !n.isRead).length;

    return (
        <div className={styles.topBar}>
            {/* Bouton menu pour mobile */}
            <button
                className={styles.menuButton}
                onClick={onToggleSidebar}
                title="Ouvrir/Fermer le menu"
            >
                <MenuIcon />
            </button>

            {/* Section centre - Barre de recherche */}
            <div className={styles.centerSection}>
                <form onSubmit={handleSearch} className={styles.searchContainer}>
                    <SearchIcon className={styles.searchIcon} />
                    <input
                        type="text"
                        placeholder="Rechercher dans la communauté..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className={styles.searchInput}
                    />
                </form>
            </div>

            {/* Section droite - Notifications, Messages, Profil */}
            <div className={styles.rightSection}>
                {/* Notifications */}
                <div className={styles.notificationContainer}>
                    <button
                        className={`${styles.iconButton} ${unreadCount > 0 ? styles.hasNotification : ''}`}
                        onClick={handleNotificationClick}
                        title="Notifications"
                    >
                        <NotificationsIcon />
                        {unreadCount > 0 && (
                            <span className={styles.notificationBadge}>
                                {unreadCount > 99 ? '99+' : unreadCount}
                            </span>
                        )}
                    </button>
                </div>

                {/* Messages */}
                <button
                    className={`${styles.iconButton} ${styles.hasNotification}`}
                    onClick={handleMessagesClick}
                    title="Chat"
                >
                    <ChatIcon />
                </button>

                {/* Profil utilisateur */}
                <div className={styles.profileContainer}>
                    <div
                        className={styles.profileTrigger}
                        onClick={handleProfileClick}
                        title="Mon profil"
                    >
                        <div className={styles.profileAvatar}>
                            {user?.avatar ? (
                                <img
                                    src={user.avatar}
                                    alt="Avatar"
                                    style={{ width: '100%', height: '100%', borderRadius: '10px' }}
                                    onError={(e) => {
                                        console.log('Erreur chargement avatar:', user.avatar);
                                        e.target.style.display = 'none';
                                        // Chercher l'élément de fallback et l'afficher
                                        const fallback = e.target.parentElement.querySelector('.fallback-avatar');
                                        if (fallback) {
                                            fallback.style.display = 'flex';
                                        }
                                    }}
                                />
                            ) : null}
                            <span
                                className="fallback-avatar"
                                style={{
                                    color: 'white',
                                    fontWeight: 'bold',
                                    fontSize: '14px',
                                    display: user?.avatar ? 'none' : 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    width: '100%',
                                    height: '100%'
                                }}
                            >
                                {getUserInitials()}
                            </span>
                        </div>

                        <div className={styles.profileInfo}>
                            <p className={styles.profileName}>
                                {user?.firstName && user?.lastName
                                    ? `${user.firstName} ${user.lastName}`
                                    : user?.email?.split('@')[0] || 'Utilisateur'
                                }
                            </p>
                            <p className={styles.profileRole}>
                                {user?.roleDisplay || 'Utilisateur'}
                            </p>
                        </div>

                        <ArrowDropDownIcon className={`${styles.dropdownIcon} ${showProfileMenu ? styles.rotated : ''}`} />
                    </div>

                    {/* Menu déroulant */}
                    {showProfileMenu && (
                        <div className={styles.profileMenu}>
                            <div className={styles.menuItem} onClick={handleMyProfileClick}>
                                <PersonIcon className={styles.menuIcon} />
                                <span>Mon Profil</span>
                            </div>
                            <div className={styles.menuItem} onClick={handleSettingsClick}>
                                <SettingsIcon className={styles.menuIcon} />
                                <span>Paramètres</span>
                            </div>
                            <div className={styles.menuDivider} />
                            <div className={styles.menuItem} onClick={handleLogoutClick}>
                                <LogoutIcon className={styles.menuIcon} />
                                <span>Se déconnecter</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Panneau des notifications */}
            <NotificationPanel
                isOpen={showNotifications}
                onClose={handleNotificationClose}
                notifications={notifications}
                onMarkAsRead={handleMarkAsRead}
                onMarkAllAsRead={handleMarkAllAsRead}
            />
        </div>
    );
};

export default TopBar;