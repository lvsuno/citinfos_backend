import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ChatSidebar from './ChatSidebar';
import ChatWindow from './ChatWindow';
import { useAuth } from '../contexts/AuthContext';
import { STATIC_USERS } from '../data/users';
import styles from './Layout.module.css';

const Layout = ({
    activeRubrique,
    onRubriqueChange,
    municipalityName,
    pageDivision,
    children
}) => {
    const { user } = useAuth();

    // Mobile sidebar state (overlay on/off)
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    // Desktop collapsed state (persisted)
    const [isCollapsed, setIsCollapsed] = useState(() => {
        try {
            return localStorage.getItem('sidebarCollapsed') === 'true';
        } catch {
            return false;
        }
    });

    const [isChatOpen, setIsChatOpen] = useState(false);
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [messages, setMessages] = useState({});

    // Persist collapsed state
    useEffect(() => {
        try {
            localStorage.setItem('sidebarCollapsed', String(isCollapsed));
        } catch (error) {
            console.error('Failed to save sidebar collapsed state:', error);
        }
    }, [isCollapsed]);

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const toggleCollapsed = () => {
        setIsCollapsed(!isCollapsed);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    const toggleChat = () => {
        setIsChatOpen(!isChatOpen);
    };

    const closeChat = () => {
        setIsChatOpen(false);
    };

    // Données de démonstration pour les conversations (utilisant les vrais utilisateurs)
    useEffect(() => {
        // Créer des conversations basées sur les utilisateurs existants
        const demoConversations = STATIC_USERS.filter(u => u.id !== user?.id).map((u, index) => ({
            id: u.id,
            name: `${u.firstName} ${u.lastName}`,
            avatar: u.avatar, // Utiliser directement l'avatar de l'utilisateur
            lastMessage: index === 0 ? 'Salut ! Comment ça va ?' :
                index === 1 ? 'Parfait, merci pour les informations !' :
                    'Bonjour ! Je suis nouveau ici.',
            timestamp: new Date(Date.now() - (index + 1) * 2 * 60 * 60 * 1000), // Décalage de 2h par conversation
            unreadCount: index === 0 ? 2 : 0,
            isOnline: index === 0, // Premier utilisateur en ligne
            municipality: u.location.city
        }));

        // Messages de démonstration basés sur les vrais utilisateurs
        const demoMessages = {};

        // Messages avec le premier utilisateur (admin)
        if (STATIC_USERS.length > 0) {
            const firstUser = STATIC_USERS[0];
            demoMessages[firstUser.id] = [
                {
                    id: 1,
                    senderId: firstUser.id,
                    senderName: `${firstUser.firstName} ${firstUser.lastName}`,
                    content: `Salut ! En tant qu'${firstUser.roleDisplay.toLowerCase()}, je peux t'aider si tu as des questions.`,
                    timestamp: new Date(Date.now() - 25 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 2,
                    senderId: user?.id || 'current',
                    senderName: user?.name || 'Vous',
                    content: 'Merci beaucoup ! J\'apprécie vraiment.',
                    timestamp: new Date(Date.now() - 20 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 3,
                    senderId: firstUser.id,
                    senderName: `${firstUser.firstName} ${firstUser.lastName}`,
                    content: 'N\'hésite pas si tu as besoin d\'aide pour naviguer dans la plateforme !',
                    timestamp: new Date(Date.now() - 15 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 4,
                    senderId: firstUser.id,
                    senderName: `${firstUser.firstName} ${firstUser.lastName}`,
                    content: 'Salut ! Comment ça va ?',
                    timestamp: new Date(Date.now() - 10 * 60 * 1000),
                    type: 'text'
                }
            ];
        }

        setConversations(demoConversations);
        setMessages(demoMessages);
        setOnlineUsers([STATIC_USERS[0]?.id].filter(Boolean)); // Premier utilisateur en ligne
    }, [user]);

    const handleConversationSelect = (conversation) => {
        setSelectedConversation(conversation);
        setConversations(prev =>
            prev.map(conv =>
                conv.id === conversation.id
                    ? { ...conv, unreadCount: 0 }
                    : conv
            )
        );
    };

    const handleSendMessage = (content, type = 'text') => {
        if (!selectedConversation || !content.trim()) return;

        const newMessage = {
            id: Date.now(),
            senderId: user?.id || 'current',
            senderName: user?.name || 'Vous',
            content: content.trim(),
            timestamp: new Date(),
            type
        };

        setMessages(prev => ({
            ...prev,
            [selectedConversation.id]: [
                ...(prev[selectedConversation.id] || []),
                newMessage
            ]
        }));

        setConversations(prev =>
            prev.map(conv =>
                conv.id === selectedConversation.id
                    ? {
                        ...conv,
                        lastMessage: content.length > 50
                            ? content.substring(0, 50) + '...'
                            : content,
                        timestamp: new Date()
                    }
                    : conv
            )
        );
    };

    const handleStartNewConversation = (selectedUser) => {
        const newConversation = {
            id: selectedUser.id,
            name: selectedUser.name,
            avatar: selectedUser.avatar,
            lastMessage: '',
            timestamp: new Date(),
            unreadCount: 0,
            isOnline: selectedUser.isOnline,
            municipality: selectedUser.municipality
        };

        setConversations(prev => [newConversation, ...prev]);
        setSelectedConversation(newConversation);
    };

    return (
        <div className={styles.layout}>
            <Sidebar
                activeRubrique={activeRubrique}
                onRubriqueChange={onRubriqueChange}
                isOpen={isSidebarOpen}
                isCollapsed={isCollapsed}
                onClose={closeSidebar}
                onToggle={toggleSidebar}
                onToggleCollapse={toggleCollapsed}
                municipalityName={municipalityName}
                pageDivision={pageDivision}
            />

            <TopBar onToggleSidebar={toggleSidebar} onChatToggle={toggleChat} />

            <main className={styles.content}>
                {/* Contenu principal sans header */}
                <div className={styles.main}>
                    {children}
                </div>
            </main>

            {/* Chat Interface Overlay */}
            {isChatOpen && (
                <div className={styles.chatOverlay}>
                    <div className={styles.chatContainer}>
                        <ChatSidebar
                            conversations={conversations}
                            selectedConversation={selectedConversation}
                            onConversationSelect={handleConversationSelect}
                            onStartNewConversation={handleStartNewConversation}
                            onlineUsers={onlineUsers}
                            onClose={closeChat}
                        />

                        <div className={styles.chatMain}>
                            {selectedConversation ? (
                                <ChatWindow
                                    conversation={selectedConversation}
                                    messages={messages[selectedConversation.id] || []}
                                    onSendMessage={handleSendMessage}
                                    currentUser={user}
                                    onClose={closeChat}
                                />
                            ) : (
                                <div className={styles.welcomeScreen}>
                                    <div className={styles.welcomeContent}>
                                        <div className={styles.welcomeIcon}>💬</div>
                                        <h2 className={styles.welcomeTitle}>
                                            Bienvenue dans le Chat Communautaire
                                        </h2>
                                        <p className={styles.welcomeText}>
                                            Connectez-vous avec d'autres membres de votre communauté.
                                            Sélectionnez une conversation pour commencer à discuter !
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Bouton fermer le chat */}
                        <button className={styles.closeChatButton} onClick={closeChat}>
                            ✕
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Layout;