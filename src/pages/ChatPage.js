import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ChatSidebar from '../components/ChatSidebar';
import ChatWindow from '../components/ChatWindow';
import styles from './ChatPage.module.css';

const ChatPage = () => {
    const { user } = useAuth();
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [conversations, setConversations] = useState([]);
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [messages, setMessages] = useState({});

    // Données de démonstration pour les conversations
    useEffect(() => {
        // Simuler des conversations existantes
        const demoConversations = [
            {
                id: 1,
                name: 'Marie Dubois',
                avatar: 'https://images.unsplash.com/photo-1494790108755-2616b25aa2f0?w=64&h=64&fit=crop&crop=face',
                lastMessage: 'Salut ! Comment ça va ?',
                timestamp: new Date(Date.now() - 10 * 60 * 1000), // 10 minutes ago
                unreadCount: 2,
                isOnline: true,
                municipality: 'Québec'
            },
            {
                id: 2,
                name: 'Jean Tremblay',
                avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=64&h=64&fit=crop&crop=face',
                lastMessage: 'Parfait, merci pour les informations !',
                timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
                unreadCount: 0,
                isOnline: false,
                municipality: 'Montréal'
            },
            {
                id: 3,
                name: 'Sophie Martin',
                avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=64&h=64&fit=crop&crop=face',
                lastMessage: 'J\'ai hâte de voir ton projet artistique !',
                timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000), // 1 day ago
                unreadCount: 1,
                isOnline: true,
                municipality: 'Sherbrooke'
            },
            {
                id: 4,
                name: 'Pierre Gagnon',
                avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=64&h=64&fit=crop&crop=face',
                lastMessage: 'Excellent travail sur le poème !',
                timestamp: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
                unreadCount: 0,
                isOnline: false,
                municipality: 'Laval'
            }
        ];

        // Messages de démonstration
        const demoMessages = {
            1: [
                {
                    id: 1,
                    senderId: 1,
                    senderName: 'Marie Dubois',
                    content: 'Salut ! J\'ai vu ton travail sur la littérature, c\'est vraiment impressionnant !',
                    timestamp: new Date(Date.now() - 25 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 2,
                    senderId: user?.id || 'current',
                    senderName: user?.name || 'Vous',
                    content: 'Merci beaucoup ! J\'apprécie vraiment tes commentaires.',
                    timestamp: new Date(Date.now() - 20 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 3,
                    senderId: 1,
                    senderName: 'Marie Dubois',
                    content: 'Est-ce que tu travailles sur quelque chose de nouveau ?',
                    timestamp: new Date(Date.now() - 15 * 60 * 1000),
                    type: 'text'
                },
                {
                    id: 4,
                    senderId: 1,
                    senderName: 'Marie Dubois',
                    content: 'Salut ! Comment ça va ?',
                    timestamp: new Date(Date.now() - 10 * 60 * 1000),
                    type: 'text'
                }
            ],
            3: [
                {
                    id: 1,
                    senderId: 3,
                    senderName: 'Sophie Martin',
                    content: 'J\'ai hâte de voir ton projet artistique !',
                    timestamp: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000),
                    type: 'text'
                }
            ]
        };

        setConversations(demoConversations);
        setMessages(demoMessages);
        setOnlineUsers([1, 3]); // Marie et Sophie sont en ligne
    }, [user]);

    const handleConversationSelect = (conversation) => {
        setSelectedConversation(conversation);

        // Marquer les messages comme lus
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

        // Ajouter le message à la conversation
        setMessages(prev => ({
            ...prev,
            [selectedConversation.id]: [
                ...(prev[selectedConversation.id] || []),
                newMessage
            ]
        }));

        // Mettre à jour le dernier message de la conversation
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

    const handleStartNewConversation = (user) => {
        // Créer une nouvelle conversation
        const newConversation = {
            id: Date.now(),
            name: user.name,
            avatar: user.avatar,
            lastMessage: '',
            timestamp: new Date(),
            unreadCount: 0,
            isOnline: user.isOnline,
            municipality: user.municipality
        };

        setConversations(prev => [newConversation, ...prev]);
        setSelectedConversation(newConversation);
    };

    if (!user) {
        return (
            <div className={styles.authRequired}>
                <h2>Messages</h2>
                <p>Connectez-vous pour accéder à vos messages</p>
                <button onClick={() => window.location.href = '/login'} className={styles.loginButton}>
                    Se connecter
                </button>
            </div>
        );
    }

    return (
        <div className={styles.chatContainer}>
            {/* Sidebar des conversations */}
            <ChatSidebar
                conversations={conversations}
                selectedConversation={selectedConversation}
                onConversationSelect={handleConversationSelect}
                onStartNewConversation={handleStartNewConversation}
                onlineUsers={onlineUsers}
            />

            {/* Zone de chat principale */}
            <div className={styles.chatMain}>
                {selectedConversation ? (
                    <ChatWindow
                        conversation={selectedConversation}
                        messages={messages[selectedConversation.id] || []}
                        onSendMessage={handleSendMessage}
                        currentUser={user}
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
        </div>
    );
};

export default ChatPage;