import React, { useState, useEffect } from 'react';
import {
    Search as SearchIcon,
    Add as AddIcon,
    MoreVert as MoreIcon,
    Circle as OnlineIcon,
    PersonAdd as PersonAddIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';
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
    const [availableUsers, setAvailableUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);
    const [modalSearchTerm, setModalSearchTerm] = useState('');

    // Charger la liste des utilisateurs disponibles quand le modal s'ouvre
    useEffect(() => {
        if (showNewChatModal && availableUsers.length === 0) {
            loadAvailableUsers();
        }
    }, [showNewChatModal]);

    // Recherche en temps réel dans le modal
    useEffect(() => {
        if (modalSearchTerm.trim()) {
            searchUsers(modalSearchTerm);
        } else {
            setSearchResults([]);
            setIsSearching(false);
        }
    }, [modalSearchTerm]);

    const loadAvailableUsers = async () => {
        try {
            setLoading(true);
            const response = await apiService.getMessagingUsers();
            console.log('Response from API:', response); // Debug log
            console.log('Response data:', response.data); // Debug log
            
            // Vérifier la structure de la réponse - les données sont dans response.data.results
            const usersList = response?.data?.results || [];
            if (!Array.isArray(usersList)) {
                console.error('Expected array but got:', typeof usersList, usersList);
                setAvailableUsers([]);
                return;
            }
            
            const users = usersList.map(user => ({
                id: user.id,
                name: user.full_name || user.username,
                username: user.username,
                email: user.email,
                avatar: user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.username)}&background=random&size=64`,
                isOnline: user.is_online,
                municipality: user.municipality || 'Non spécifiée'
            }));
            setAvailableUsers(users);
        } catch (error) {
            console.error('Erreur lors du chargement des utilisateurs:', error);
            setAvailableUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const searchUsers = async (query) => {
        try {
            setIsSearching(true);
            const response = await apiService.searchMessagingUsers(query);
            console.log('Search response from API:', response); // Debug log
            console.log('Search response data:', response.data); // Debug log
            
            // Vérifier la structure de la réponse - les données sont dans response.data.results
            const usersList = response?.data?.results || [];
            if (!Array.isArray(usersList)) {
                console.error('Expected array but got:', typeof usersList, usersList);
                setSearchResults([]);
                return;
            }
            
            const users = usersList.map(user => ({
                id: user.id,
                name: user.full_name || user.username,
                username: user.username,
                email: user.email,
                avatar: user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.username)}&background=random&size=64`,
                isOnline: user.is_online,
                municipality: user.municipality || 'Non spécifiée'
            }));
            setSearchResults(users);
        } catch (error) {
            console.error('Erreur lors de la recherche:', error);
            setSearchResults([]);
        } finally {
            setIsSearching(false);
        }
    };

    // Filtrer les conversations selon le terme de recherche
    const filteredConversations = conversations.filter(conv =>
        (conv.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
        (conv.municipality || '').toLowerCase().includes(searchTerm.toLowerCase())
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

    const handleNewConversation = async (user) => {
        try {
            setLoading(true);
            // Appeler la fonction du parent avec les données utilisateur
            // Le hook useMessaging s'occupera de créer la conversation
            await onStartNewConversation(user);
            
            setShowNewChatModal(false);
            setModalSearchTerm('');
            setSearchResults([]);
        } catch (error) {
            console.error('Erreur lors de la création de la conversation:', error);
            // TODO: Afficher un message d'erreur à l'utilisateur
        } finally {
            setLoading(false);
        }
    };

    const handleCloseModal = () => {
        setShowNewChatModal(false);
        setModalSearchTerm('');
        setSearchResults([]);
    };

    // Déterminer quels utilisateurs afficher dans le modal
    const usersToDisplay = modalSearchTerm.trim() 
        ? searchResults 
        : availableUsers;

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
                <div className={styles.modalOverlay} onClick={handleCloseModal}>
                    <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h3>Nouveau Chat</h3>
                            <button
                                className={styles.closeButton}
                                onClick={handleCloseModal}
                            >
                                ×
                            </button>
                        </div>

                        <div className={styles.modalContent}>
                            <p className={styles.modalDescription}>
                                Sélectionnez un utilisateur pour commencer une nouvelle conversation :
                            </p>

                            {/* Barre de recherche dans le modal */}
                            <div className={styles.modalSearchContainer}>
                                <div className={styles.searchBox}>
                                    <SearchIcon className={styles.searchIcon} />
                                    <input
                                        type="text"
                                        placeholder="Rechercher un utilisateur..."
                                        value={modalSearchTerm}
                                        onChange={(e) => setModalSearchTerm(e.target.value)}
                                        className={styles.searchInput}
                                    />
                                </div>
                            </div>

                            {loading ? (
                                <div className={styles.loadingContainer}>
                                    <p>Chargement des utilisateurs...</p>
                                </div>
                            ) : (
                                <div className={styles.usersList}>
                                    {usersToDisplay.length > 0 ? (
                                        usersToDisplay.map((user) => (
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
                                                        onError={(e) => {
                                                            e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name)}&background=random&size=64`;
                                                        }}
                                                    />
                                                    {user.isOnline && (
                                                        <OnlineIcon className={styles.onlineIndicator} />
                                                    )}
                                                </div>

                                                <div className={styles.userInfo}>
                                                    <h4 className={styles.userName}>{user.name}</h4>
                                                    <p className={styles.userUsername}>@{user.username}</p>
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
                                        ))
                                    ) : (
                                        <div className={styles.emptyState}>
                                            {modalSearchTerm.trim() ? (
                                                <p>Aucun utilisateur trouvé pour "{modalSearchTerm}"</p>
                                            ) : (
                                                <p>Aucun utilisateur disponible</p>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatSidebar;