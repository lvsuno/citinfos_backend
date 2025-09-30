import React, { useState } from 'react';
import {
    Search as SearchIcon,
    Add as AddIcon,
    MoreVert as MoreIcon,
    Circle as OnlineIcon
} from '@mui/icons-material';
import { STATIC_USERS } from '../data/users';
import { useAuth } from '../contexts/AuthContext';
import styles from './ChatSidebar.module.css';

const ChatSidebar = ({
    conversations,
    selectedConversation,
    onConversationSelect,
    onStartNewConversation,
    onlineUsers,
    onClose
}) => {
    const { user: currentUser } = useAuth();
    const [searchTerm, setSearchTerm] = useState('');
    const [showNewChatModal, setShowNewChatModal] = useState(false);

    // Utilisateurs disponibles basés sur les vrais utilisateurs (excluant l'utilisateur actuel)
    const availableUsers = STATIC_USERS
        .filter(u => u.id !== currentUser?.id)
        .map(u => ({
            id: u.id,
            name: `${u.firstName} ${u.lastName}`,
            avatar: u.avatar, // Utiliser directement l'avatar de l'utilisateur
            isOnline: onlineUsers.includes(u.id),
            municipality: u.location.city
        }));

    // Filtrer les conversations selon le terme de recherche
    const filteredConversations = conversations.filter(conv =>
        conv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conv.municipality.toLowerCase().includes(searchTerm.toLowerCase())
    );

    // Formater le timestamp
    const formatTimestamp = (timestamp) => {
        const now = new Date();
        const messageTime = new Date(timestamp);
        const diffInMinutes = Math.floor((now - messageTime) / (1000 * 60));
        const diffInHours = Math.floor(diffInMinutes / 60);
        const diffInDays = Math.floor(diffInHours / 24);

        if (diffInMinutes < 1) return 'À l\'instant';
        if (diffInMinutes < 60) return `${diffInMinutes}m`;
        if (diffInHours < 24) return `${diffInHours}h`;
        if (diffInDays < 7) return `${diffInDays}j`;

        return messageTime.toLocaleDateString('fr-CA', {
            month: 'short',
            day: 'numeric'
        });
    };

    const handleNewConversation = (user) => {
        onStartNewConversation(user);
        setShowNewChatModal(false);
    };

    return (
        <div className={styles.sidebar}>
            {/* Header de la sidebar */}
            <div className={styles.header}>
                <h2 className={styles.title}>Messages</h2>
                <div className={styles.headerActions}>
                    <button
                        className={styles.newChatButton}
                        onClick={() => setShowNewChatModal(true)}
                        title="Nouveau chat"
                    >
                        <AddIcon />
                    </button>
                    <button className={styles.moreButton} title="Plus d'options">
                        <MoreIcon />
                    </button>
                </div>
            </div>

            {/* Barre de recherche */}
            <div className={styles.searchContainer}>
                <div className={styles.searchBox}>
                    <SearchIcon className={styles.searchIcon} />
                    <input
                        type="text"
                        placeholder="Rechercher conversations..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className={styles.searchInput}
                    />
                </div>
            </div>

            {/* Liste des conversations */}
            <div className={styles.conversationsList}>
                {filteredConversations.length > 0 ? (
                    filteredConversations.map((conversation) => (
                        <div
                            key={conversation.id}
                            className={`${styles.conversationItem} ${selectedConversation?.id === conversation.id
                                ? styles.selected
                                : ''
                                }`}
                            onClick={() => onConversationSelect(conversation)}
                        >
                            <div className={styles.avatarContainer}>
                                <img
                                    src={conversation.avatar}
                                    alt={conversation.name}
                                    className={styles.avatar}
                                />
                                {conversation.isOnline && (
                                    <OnlineIcon className={styles.onlineIndicator} />
                                )}
                            </div>

                            <div className={styles.conversationContent}>
                                <div className={styles.conversationHeader}>
                                    <h3 className={styles.name}>{conversation.name}</h3>
                                    <span className={styles.timestamp}>
                                        {formatTimestamp(conversation.timestamp)}
                                    </span>
                                </div>

                                <div className={styles.conversationPreview}>
                                    <p className={styles.lastMessage}>
                                        {conversation.lastMessage || 'Aucun message'}
                                    </p>
                                    {conversation.unreadCount > 0 && (
                                        <span className={styles.unreadBadge}>
                                            {conversation.unreadCount}
                                        </span>
                                    )}
                                </div>

                                <div className={styles.municipality}>
                                    📍 {conversation.municipality}
                                </div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className={styles.emptyState}>
                        <p>Aucune conversation trouvée</p>
                    </div>
                )}
            </div>

            {/* Modal pour nouveau chat */}
            {showNewChatModal && (
                <div className={styles.modalOverlay} onClick={() => setShowNewChatModal(false)}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>Nouveau Chat</h3>
                            <button
                                className={styles.closeButton}
                                onClick={() => setShowNewChatModal(false)}
                            >
                                ×
                            </button>
                        </div>

                        <div className={styles.modalContent}>
                            <p className={styles.modalDescription}>
                                Sélectionnez un utilisateur pour commencer une nouvelle conversation :
                            </p>

                            <div className={styles.usersList}>
                                {availableUsers.map((user) => (
                                    <div
                                        key={user.id}
                                        className={styles.userItem}
                                        onClick={() => handleNewConversation(user)}
                                    >
                                        <div className={styles.avatarContainer}>
                                            <img
                                                src={user.avatar}
                                                alt={user.name}
                                                className={styles.avatar}
                                            />
                                            {user.isOnline && (
                                                <OnlineIcon className={styles.onlineIndicator} />
                                            )}
                                        </div>

                                        <div className={styles.userInfo}>
                                            <h4 className={styles.userName}>{user.name}</h4>
                                            <p className={styles.userMunicipality}>
                                                📍 {user.municipality}
                                            </p>
                                        </div>

                                        <div className={styles.userStatus}>
                                            {user.isOnline ? (
                                                <span className={styles.onlineText}>En ligne</span>
                                            ) : (
                                                <span className={styles.offlineText}>Hors ligne</span>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatSidebar;