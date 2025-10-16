import React, { useState, useEffect } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import ChatSidebar from './ChatSidebar';
import ChatWindow from './ChatWindow';
import ChatNotification from './chat/ChatNotification';
import NetworkingSidebar from './NetworkingSidebar';
import { useAuth } from '../contexts/AuthContext';
import { useMessaging } from '../hooks/useMessaging';
import styles from './Layout.module.css';

const Layout = ({
    activeRubrique,
    onRubriqueChange,
    municipalityName,
    pageDivision,
    children,
    // Nouveau paramètre pour ouvrir le chat avec un utilisateur spécifique
    initialChatUser = null
}) => {
    const { user } = useAuth();
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [isChatOpen, setIsChatOpen] = useState(false);
    const [isNetworkingOpen, setIsNetworkingOpen] = useState(false);

    // Utiliser le hook personnalisé pour la logique de messaging
    const {
        conversations,
        messages,
        selectedConversation,
        onlineUsers,
        loadingConversations,
        loadingMessages,
        notifications,
        selectConversation,
        sendMessage,
        addReaction,
        createConversation,
        removeNotification
    } = useMessaging(user);

    const toggleSidebar = () => {
        setIsSidebarOpen(!isSidebarOpen);
    };

    const closeSidebar = () => {
        setIsSidebarOpen(false);
    };

    const toggleChat = () => {
        setIsChatOpen(!isChatOpen);
    };

    const openChatWithUser = async (targetUser) => {
        console.log('🚀 Layout: openChatWithUser appelée avec:', targetUser);
        try {
            // Ouvrir le chat
            setIsChatOpen(true);
            console.log('💬 Chat ouvert, création de conversation...');
            
            // Créer ou trouver la conversation avec cet utilisateur
            await createConversation(targetUser);
            console.log('✅ Conversation créée/trouvée');
        } catch (error) {
            console.error('❌ Erreur lors de l\'ouverture du chat avec l\'utilisateur:', error);
        }
    };

    // Effet pour gérer l'ouverture automatique du chat avec un utilisateur
    useEffect(() => {
        console.log('🔍 Layout useEffect - initialChatUser:', initialChatUser, 'user:', !!user);
        if (initialChatUser && user) {
            console.log('🎯 Déclenchement de openChatWithUser...');
            openChatWithUser(initialChatUser);
            
            // Optionnel: nettoyer le state pour éviter la répétition
            // Note: Ceci nécessiterait une ref au navigate function
            // Pour l'instant, on laisse le comportement tel quel
        }
    }, [initialChatUser, user, createConversation]);

    const closeChat = () => {
        setIsChatOpen(false);
    };

    const toggleNetworking = () => {
        setIsNetworkingOpen(!isNetworkingOpen);
    };

    const closeNetworking = () => {
        setIsNetworkingOpen(false);
    };

    return (
        <div className={styles.layout}>
            <Sidebar
                activeRubrique={activeRubrique}
                onRubriqueChange={onRubriqueChange}
                isOpen={isSidebarOpen}
                onClose={closeSidebar}
                municipalityName={municipalityName}
                pageDivision={pageDivision}
            />

            <TopBar 
                onToggleSidebar={toggleSidebar} 
                onChatToggle={toggleChat}
                onNetworkingToggle={toggleNetworking}
            />

            <main className={styles.content}>
                {/* Contenu principal sans header */}
                <div className={styles.main}>
                    {children}
                </div>
            </main>

            {/* Networking Sidebar */}
            <NetworkingSidebar
                isOpen={isNetworkingOpen}
                onClose={closeNetworking}
            />

            {/* Chat Interface Overlay */}
            {isChatOpen && (
                <div className={styles.chatOverlay}>
                    <div className={styles.chatContainer}>
                        <ChatSidebar
                            conversations={conversations}
                            selectedConversation={selectedConversation}
                            onConversationSelect={selectConversation}
                            onStartNewConversation={createConversation}
                            onlineUsers={onlineUsers}
                            onClose={closeChat}
                            loading={loadingConversations}
                        />

                        <div className={styles.chatMain}>
                            {selectedConversation ? (
                                <ChatWindow
                                    conversation={selectedConversation}
                                    messages={messages[selectedConversation.id] || []}
                                    onSendMessage={sendMessage}
                                    onReaction={addReaction}
                                    currentUser={user}
                                    onClose={closeChat}
                                    loading={loadingMessages}
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

            {/* Notifications */}
            {notifications && notifications.length > 0 && notifications.map(notification => (
                <ChatNotification
                    key={notification.id}
                    message={notification.message}
                    type={notification.type}
                    onClose={() => removeNotification(notification.id)}
                />
            ))}
        </div>
    );
};

export default Layout;