import { useState, useEffect, useRef, useCallback } from 'react';
import { messagingAPI } from '../services/messagingAPI';
import { apiService } from '../services/apiService';
import ConnectionManager from '../utils/ConnectionManager';

export const useMessaging = (user) => {
    const [conversations, setConversations] = useState([]);
    const [messages, setMessages] = useState({});
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [onlineUsers, setOnlineUsers] = useState([]);
    const [loadingConversations, setLoadingConversations] = useState(false);
    const [loadingMessages, setLoadingMessages] = useState(false);
    const [notifications, setNotifications] = useState([]);

    const connectionManager = useRef(new ConnectionManager());
    const notificationIdCounter = useRef(0);

    // Fonction pour afficher une notification
    const showNotification = useCallback((message, type = 'info') => {
        const id = ++notificationIdCounter.current;
        const notification = { id, message, type };
        setNotifications(prev => [...prev, notification]);

        // Auto-suppression après 5 secondes
        setTimeout(() => {
            setNotifications(prev => prev.filter(n => n.id !== id));
        }, 5000);
    }, []);

    // Supprimer une notification
    const removeNotification = useCallback((id) => {
        setNotifications(prev => prev.filter(n => n.id !== id));
    }, []);

    // Fonction utilitaire pour obtenir le nom d'une conversation
    const getConversationName = useCallback((room) => {
        if (room.room_type === 'direct') {
            const otherParticipant = room.participants?.find(p => p.id !== user?.id);
            return otherParticipant ?
                `${otherParticipant.first_name || ''} ${otherParticipant.last_name || ''}`.trim() ||
                otherParticipant.username :
                'Conversation directe';
        }
        return room.name || 'Conversation de groupe';
    }, [user?.id]);

    // Fonction utilitaire pour obtenir l'avatar d'une conversation
    const getConversationAvatar = useCallback((room) => {
        if (room.room_type === 'direct') {
            const otherParticipant = room.participants?.find(p => p.id !== user?.id);
            return otherParticipant?.avatar;
        }
        return room.image;
    }, [user?.id]);

    // Charger les conversations
    const loadConversations = useCallback(async () => {
        if (!user) return;

        setLoadingConversations(true);
        try {
            const response = await connectionManager.current.executeWithRetry(
                () => messagingAPI.getChatRooms(),
                showNotification
            );

            const chatRooms = response.results || response;

            const formattedConversations = chatRooms.map(room => ({
                id: room.id,
                name: room.name || getConversationName(room),
                avatar: room.image || getConversationAvatar(room),
                lastMessage: room.last_message?.content || 'Aucun message',
                timestamp: room.last_activity ? new Date(room.last_activity) : new Date(),
                unreadCount: room.unread_count || 0,
                isOnline: false,
                municipality: room.municipality || 'Non spécifiée',
                room_type: room.room_type,
                participants: room.participants || []
            }));

            setConversations(formattedConversations);

            // Charger les utilisateurs en ligne
            const onlineResponse = await connectionManager.current.executeWithRetry(
                () => messagingAPI.getOnlineUsers(),
                showNotification
            );

            const onlineUserIds = (onlineResponse.results || onlineResponse).map(presence =>
                presence.user?.id || presence.user
            );
            setOnlineUsers(onlineUserIds);

        } catch (error) {
            console.error('Erreur lors du chargement des conversations:', error);
            showNotification('Impossible de charger les conversations. Mode hors ligne activé.', 'warning');
            setConversations([]);
        }
        setLoadingConversations(false);
    }, [user, getConversationName, getConversationAvatar, showNotification]);

    // Charger les messages d'une conversation
    const loadMessages = useCallback(async (roomId) => {
        if (!roomId) {
            console.error('roomId is undefined in loadMessages');
            setLoadingMessages(false);
            return;
        }
        
        setLoadingMessages(true);
        try {
            const response = await connectionManager.current.executeWithRetry(
                () => apiService.getRoomMessages(roomId),
                showNotification
            );

            console.log('loadMessages response:', response); // Debug log
            console.log('loadMessages response.data:', response.data); // Debug log
            
            // L'endpoint /messaging/messages/ avec params retourne un objet paginé {results: [...]}
            const apiMessages = response.data?.results || [];
            console.log('apiMessages:', apiMessages, 'Type:', typeof apiMessages, 'IsArray:', Array.isArray(apiMessages)); // Debug log

            // Vérifier que apiMessages est un tableau
            if (!Array.isArray(apiMessages)) {
                console.error('apiMessages is not an array:', apiMessages);
                setMessages(prev => ({
                    ...prev,
                    [roomId]: []
                }));
                return;
            }

            const formattedMessages = apiMessages.map(msg => ({
                id: msg.id,
                senderId: msg.sender?.id || msg.sender,
                senderName: msg.sender?.user?.first_name && msg.sender?.user?.last_name ?
                    `${msg.sender.user.first_name} ${msg.sender.user.last_name}` :
                    msg.sender?.user?.username || 'Utilisateur',
                content: msg.content,
                timestamp: new Date(msg.created_at),
                type: msg.message_type || 'text',
                attachments: msg.attachments || [],
                reactions: msg.reactions || [],
                isEdited: msg.is_edited || false
            }));

            setMessages(prev => ({
                ...prev,
                [roomId]: formattedMessages
            }));

        } catch (error) {
            console.error('Erreur lors du chargement des messages:', error);
            showNotification('Impossible de charger les messages.', 'error');
            setMessages(prev => ({
                ...prev,
                [roomId]: []
            }));
        }
        setLoadingMessages(false);
    }, [showNotification]);

    // Sélectionner une conversation
    const selectConversation = useCallback(async (conversation) => {
        setSelectedConversation(conversation);

        // Marquer comme lu
        try {
            await messagingAPI.markRoomAsRead(conversation.id);
            setConversations(prev =>
                prev.map(conv =>
                    conv.id === conversation.id
                        ? { ...conv, unreadCount: 0 }
                        : conv
                )
            );
        } catch (error) {
            console.error('Erreur lors du marquage comme lu:', error);
        }

        await loadMessages(conversation.id);
    }, [loadMessages]);

    // Envoyer un message
    const sendMessage = useCallback(async (content, type = 'text') => {
        if (!selectedConversation || !content.trim()) return;

        try {
            const messageData = {
                room: selectedConversation.id,
                content: content.trim(),
                message_type: type
            };

            const newMessage = await connectionManager.current.executeWithRetry(
                () => messagingAPI.sendMessage(messageData),
                showNotification
            );

            const formattedMessage = {
                id: newMessage.id,
                senderId: user?.id || 'current',
                senderName: user?.name || 'Vous',
                content: newMessage.content,
                timestamp: new Date(newMessage.created_at),
                type: newMessage.message_type || 'text',
                attachments: newMessage.attachments || [],
                reactions: []
            };

            setMessages(prev => ({
                ...prev,
                [selectedConversation.id]: [
                    ...(prev[selectedConversation.id] || []),
                    formattedMessage
                ]
            }));

            setConversations(prev =>
                prev.map(conv =>
                    conv.id === selectedConversation.id
                        ? {
                            ...conv,
                            lastMessage: content.trim(),
                            timestamp: new Date()
                        }
                        : conv
                )
            );

        } catch (error) {
            console.error('Erreur lors de l\'envoi du message:', error);
            showNotification('Impossible d\'envoyer le message. Veuillez réessayer.', 'error');
        }
    }, [selectedConversation, user, showNotification]);

    // Ajouter une réaction
    const addReaction = useCallback(async (messageId, emoji) => {
        if (!selectedConversation || !messageId) return;

        try {
            await connectionManager.current.executeWithRetry(
                () => messagingAPI.addReaction({ message: messageId, emoji }),
                showNotification
            );

            setMessages(prev => ({
                ...prev,
                [selectedConversation.id]: (prev[selectedConversation.id] || []).map(msg =>
                    msg.id === messageId
                        ? {
                            ...msg,
                            reactions: [
                                ...(msg.reactions || []),
                                {
                                    id: Date.now(),
                                    emoji: emoji,
                                    user: user?.id || 'current',
                                    created_at: new Date().toISOString()
                                }
                            ]
                        }
                        : msg
                )
            }));

        } catch (error) {
            console.error('Erreur lors de l\'ajout de la réaction:', error);
            showNotification('Impossible d\'ajouter la réaction.', 'error');
        }
    }, [selectedConversation, user, showNotification]);

    // Créer une nouvelle conversation
    const createConversation = useCallback(async (selectedUser) => {
        console.log('🗨️ createConversation appelée avec:', selectedUser);
        
        try {
            // Vérifier si une conversation directe existe déjà
            const existingConversation = conversations.find(conv =>
                conv.room_type === 'direct' &&
                conv.participants?.some(p => 
                    p.id === selectedUser.id || 
                    p.username === selectedUser.username
                )
            );

            console.log('🔍 Conversation existante trouvée:', existingConversation);

            if (existingConversation) {
                console.log('✅ Sélection de la conversation existante');
                await selectConversation(existingConversation);
                return;
            }

            console.log('🆕 Création d\'une nouvelle conversation...');
            
            // Créer une nouvelle conversation directe via l'API
            const response = await connectionManager.current.executeWithRetry(
                () => apiService.createDirectMessage(selectedUser.id),
                showNotification
            );

            const newRoom = response.data;
            console.log('📨 Nouvelle room créée:', newRoom);

            const newConversation = {
                id: newRoom.id,
                name: selectedUser.full_name || selectedUser.name || selectedUser.username,
                avatar: selectedUser.avatar,
                lastMessage: '',
                timestamp: new Date(),
                unreadCount: 0,
                isOnline: selectedUser.isOnline || selectedUser.is_online,
                municipality: selectedUser.municipality,
                room_type: 'direct',
                participants: newRoom.participants
            };

            console.log('💬 Nouvelle conversation créée:', newConversation);
            
            setConversations(prev => [newConversation, ...prev]);
            setSelectedConversation(newConversation);
            
            console.log('✅ Conversation ajoutée et sélectionnée');

        } catch (error) {
            console.error('❌ Erreur lors de la création de la conversation:', error);
            showNotification('Impossible de créer la conversation.', 'error');
        }
    }, [conversations, selectConversation, showNotification]);

    // Mettre à jour la présence
    const updatePresence = useCallback(async () => {
        if (!user) return;

        try {
            await messagingAPI.updatePresence({
                is_online: true,
                last_activity: new Date().toISOString()
            });
        } catch (error) {
            console.error('Erreur lors de la mise à jour de la présence:', error);
        }
    }, [user]);

    // Effet pour charger les données initiales
    useEffect(() => {
        loadConversations();
        updatePresence();

        // Mettre à jour la présence régulièrement
        const presenceInterval = setInterval(updatePresence, 60000);

        return () => {
            clearInterval(presenceInterval);
            connectionManager.current.destroy();

            // Marquer comme hors ligne
            if (user) {
                messagingAPI.updatePresence({
                    is_online: false,
                    last_activity: new Date().toISOString()
                }).catch(console.error);
            }
        };
    }, [user, loadConversations, updatePresence]);

    return {
        // État
        conversations,
        messages,
        selectedConversation,
        onlineUsers,
        loadingConversations,
        loadingMessages,
        notifications,

        // Actions
        selectConversation,
        sendMessage,
        addReaction,
        createConversation,
        removeNotification,
        loadConversations,
        loadMessages
    };
};

export default useMessaging;