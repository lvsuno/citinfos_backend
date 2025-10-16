import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search as SearchIcon,
    Close as CloseIcon,
    PersonAdd as PersonAddIcon,
    Person as PersonIcon,
    LocationOn as LocationIcon,
    FilterList as FilterIcon,
    Circle as OnlineIcon,
    Check as CheckIcon,
    AccessTime as PendingIcon,
    People as ConnectedIcon,
    Chat
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/apiService';
import styles from './NetworkingSidebar.module.css';

const NetworkingSidebar = ({ isOpen, onClose }) => {
    const { user: currentUser } = useAuth();
    const navigate = useNavigate();
    const [searchTerm, setSearchTerm] = useState('');
    const [users, setUsers] = useState([]);
    const [filteredUsers, setFilteredUsers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [activeFilter, setActiveFilter] = useState('all'); // all, online, same-city
    const [connectionRequests, setConnectionRequests] = useState(new Map()); // Track connection status

    // Charger la liste des utilisateurs
    useEffect(() => {
        if (isOpen) {
            loadUsers();
        }
    }, [isOpen]);

    // Filtrer les utilisateurs selon le terme de recherche et les filtres
    useEffect(() => {
        let filtered = users.filter(user => {
            const matchesSearch = !searchTerm || 
                user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                user.municipality?.toLowerCase().includes(searchTerm.toLowerCase());

            const matchesFilter = (() => {
                switch (activeFilter) {
                    case 'online':
                        return user.is_online;
                    case 'same-city':
                        return user.municipality === currentUser?.municipality;
                    default:
                        return true;
                }
            })();

            return matchesSearch && matchesFilter;
        });

        setFilteredUsers(filtered);
    }, [users, searchTerm, activeFilter, currentUser]);

    const loadUsers = async () => {
        try {
            setLoading(true);
            const response = await apiService.getMessagingUsers();
            
            const usersList = response?.data?.results || [];
            if (!Array.isArray(usersList)) {
                console.error('Expected array but got:', typeof usersList, usersList);
                setUsers([]);
                return;
            }
            
            // Filtrer le user actuel et transformer les données
            const networkingUsers = usersList
                .filter(user => user.id !== currentUser?.id)
                .map(user => ({
                    id: user.id,
                    username: user.username,
                    full_name: user.full_name || user.username,
                    email: user.email,
                    avatar: user.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name || user.username)}&background=random&size=64`,
                    is_online: user.is_online || false,
                    municipality: user.municipality || 'Non spécifiée',
                    profile: user.profile || {}
                }));
            
            setUsers(networkingUsers);
        } catch (error) {
            console.error('Erreur lors du chargement des utilisateurs:', error);
            setUsers([]);
        } finally {
            setLoading(false);
        }
    };

    const handleUserProfile = (user) => {
        // Naviguer vers le profil de l'utilisateur
        navigate(`/user/${user.username}`);
        onClose();
    };

    const handleStartConversation = (user) => {
        // Fermer le sidebar et démarrer une conversation
        onClose();
        
        // Naviguer vers le dashboard avec instruction d'ouvrir le chat
        navigate('/dashboard', { 
            state: { 
                openChatWithUser: {
                    id: user.id,
                    username: user.username,
                    full_name: user.full_name,
                    avatar: user.avatar,
                    email: user.email,
                    municipality: user.municipality
                }
            }
        });
    };

    const handleConnect = async (user) => {
        try {
            // Simuler une demande de connexion (à implémenter avec l'API)
            setConnectionRequests(prev => new Map(prev.set(user.id, 'pending')));
            
            // TODO: Remplacer par un vrai appel API
            setTimeout(() => {
                setConnectionRequests(prev => new Map(prev.set(user.id, 'connected')));
            }, 2000);
            
            console.log('Demande de connexion envoyée à:', user.full_name);
        } catch (error) {
            console.error('Erreur lors de la demande de connexion:', error);
            setConnectionRequests(prev => {
                const newMap = new Map(prev);
                newMap.delete(user.id);
                return newMap;
            });
        }
    };

    const getConnectionStatus = (userId) => {
        return connectionRequests.get(userId) || 'none';
    };

    const renderConnectionButton = (user) => {
        const status = getConnectionStatus(user.id);
        
        switch (status) {
            case 'pending':
                return (
                    <button className={`${styles.connectButton} ${styles.pending}`} disabled>
                        <PendingIcon className={styles.buttonIcon} />
                        En attente
                    </button>
                );
            case 'connected':
                return (
                    <button className={`${styles.connectButton} ${styles.connected}`} disabled>
                        <CheckIcon className={styles.buttonIcon} />
                        Connecté
                    </button>
                );
            default:
                return (
                    <button 
                        className={styles.connectButton}
                        onClick={() => handleConnect(user)}
                    >
                        <PersonAddIcon className={styles.buttonIcon} />
                        Connecter
                    </button>
                );
        }
    };

    const filters = [
        { key: 'all', label: 'Tous', icon: ConnectedIcon },
        { key: 'online', label: 'En ligne', icon: OnlineIcon },
        { key: 'same-city', label: 'Ma ville', icon: LocationIcon }
    ];

    if (!isOpen) return null;

    return (
        <>
            {/* Overlay */}
            <div className={styles.overlay} onClick={onClose} />
            
            {/* Sidebar */}
            <div className={styles.networkingSidebar}>
                {/* Header */}
                <div className={styles.header}>
                    <div className={styles.titleSection}>
                        <ConnectedIcon className={styles.headerIcon} />
                        <h2 className={styles.title}>Réseautage</h2>
                    </div>
                    <button className={styles.closeButton} onClick={onClose}>
                        <CloseIcon />
                    </button>
                </div>

                {/* Search */}
                <div className={styles.searchSection}>
                    <div className={styles.searchContainer}>
                        <SearchIcon className={styles.searchIcon} />
                        <input
                            type="text"
                            placeholder="Rechercher des utilisateurs..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className={styles.searchInput}
                        />
                    </div>
                </div>

                {/* Filters */}
                <div className={styles.filtersSection}>
                    <div className={styles.filtersContainer}>
                        {filters.map((filter) => {
                            const IconComponent = filter.icon;
                            return (
                                <button
                                    key={filter.key}
                                    className={`${styles.filterButton} ${activeFilter === filter.key ? styles.active : ''}`}
                                    onClick={() => setActiveFilter(filter.key)}
                                >
                                    <IconComponent className={styles.filterIcon} />
                                    <span>{filter.label}</span>
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Users List */}
                <div className={styles.usersSection}>
                    {loading ? (
                        <div className={styles.loadingContainer}>
                            <div className={styles.spinner}></div>
                            <p>Chargement des utilisateurs...</p>
                        </div>
                    ) : filteredUsers.length > 0 ? (
                        <div className={styles.usersList}>
                            {filteredUsers.map((user) => (
                                <div key={user.id} className={styles.userCard}>
                                    <div className={styles.userInfo} onClick={() => handleUserProfile(user)}>
                                        <div className={styles.avatarContainer}>
                                            <img
                                                src={user.avatar}
                                                alt={user.full_name}
                                                className={styles.avatar}
                                                onError={(e) => {
                                                    e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(user.full_name)}&background=random&size=64`;
                                                }}
                                            />
                                            {user.is_online && (
                                                <OnlineIcon className={styles.onlineIndicator} />
                                            )}
                                        </div>

                                        <div className={styles.userDetails}>
                                            <h3 className={styles.userName}>{user.full_name}</h3>
                                            <p className={styles.userUsername}>@{user.username}</p>
                                            <div className={styles.userLocation}>
                                                <LocationIcon className={styles.locationIcon} />
                                                <span>{user.municipality}</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className={styles.userActions}>
                                        {renderConnectionButton(user)}
                                        <button
                                            className={styles.messageButton}
                                            onClick={() => handleStartConversation(user)}
                                            title="Envoyer un message"
                                        >
                                            <Chat className={styles.buttonIcon} />
                                        </button>
                                        <button
                                            className={styles.profileButton}
                                            onClick={() => handleUserProfile(user)}
                                            title="Voir le profil"
                                        >
                                            <PersonIcon />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className={styles.emptyState}>
                            <ConnectedIcon className={styles.emptyIcon} />
                            <h3>Aucun utilisateur trouvé</h3>
                            <p>
                                {searchTerm 
                                    ? `Aucun résultat pour "${searchTerm}"`
                                    : 'Aucun utilisateur disponible pour le moment'
                                }
                            </p>
                        </div>
                    )}
                </div>

                {/* Footer Stats */}
                <div className={styles.footer}>
                    <div className={styles.stats}>
                        <span className={styles.statsText}>
                            {filteredUsers.length} utilisateur{filteredUsers.length !== 1 ? 's' : ''} 
                            {activeFilter !== 'all' && ` (${filters.find(f => f.key === activeFilter)?.label.toLowerCase()})`}
                        </span>
                    </div>
                </div>
            </div>
        </>
    );
};

export default NetworkingSidebar;