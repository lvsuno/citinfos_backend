/**
 * Messaging API Service
 * Handles all messaging-related API operations
 * Connects to the messaging app backend endpoints
 */

import BaseAPIService from './baseAPI';

class MessagingAPI extends BaseAPIService {
    constructor() {
        super();
        this.messagingBaseURL = '/messaging';
    }

    // Chat Rooms API
    async getChatRooms(params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`${this.messagingBaseURL}/rooms/${queryString}`);
    }

    async getChatRoom(roomId) {
        return this.get(`${this.messagingBaseURL}/rooms/${roomId}/`);
    }

    async createChatRoom(roomData) {
        return this.post(`${this.messagingBaseURL}/rooms/`, roomData);
    }

    async updateChatRoom(roomId, roomData) {
        return this.patch(`${this.messagingBaseURL}/rooms/${roomId}/`, roomData);
    }

    async deleteChatRoom(roomId) {
        return this.delete(`${this.messagingBaseURL}/rooms/${roomId}/`);
    }

    async addParticipant(roomId, userId) {
        return this.post(`${this.messagingBaseURL}/rooms/${roomId}/add_participant/`, {
            user_id: userId
        });
    }

    async removeParticipant(roomId, userId) {
        return this.post(`${this.messagingBaseURL}/rooms/${roomId}/remove_participant/`, {
            user_id: userId
        });
    }

    // Messages API
    async getMessages(roomId, params = {}) {
        const queryString = this.buildQueryString(params);
        return this.get(`${this.messagingBaseURL}/messages/${queryString}&room=${roomId}`);
    }

    async sendMessage(messageData) {
        return this.post(`${this.messagingBaseURL}/messages/`, messageData);
    }

    async updateMessage(messageId, messageData) {
        return this.patch(`${this.messagingBaseURL}/messages/${messageId}/`, messageData);
    }

    async deleteMessage(messageId) {
        return this.delete(`${this.messagingBaseURL}/messages/${messageId}/`);
    }

    async markMessageAsRead(messageId) {
        return this.post(`${this.messagingBaseURL}/reads/`, {
            message: messageId
        });
    }

    async markRoomAsRead(roomId) {
        return this.post(`${this.messagingBaseURL}/rooms/${roomId}/mark_read/`);
    }

    // Message Reactions API
    async addReaction(messageId, emoji) {
        return this.post(`${this.messagingBaseURL}/reactions/`, {
            message: messageId,
            emoji: emoji
        });
    }

    async removeReaction(reactionId) {
        return this.delete(`${this.messagingBaseURL}/reactions/${reactionId}/`);
    }

    async getMessageReactions(messageId) {
        return this.get(`${this.messagingBaseURL}/reactions/?message=${messageId}`);
    }

    // User Presence API
    async updatePresence(presenceData) {
        return this.post(`${this.messagingBaseURL}/presence/update_status/`, presenceData);
    }

    async getPresence(userId) {
        return this.get(`${this.messagingBaseURL}/presence/${userId}/`);
    }

    async getOnlineUsers() {
        return this.get(`${this.messagingBaseURL}/presence/online_users/`);
    }

    // Typing Indicators (if implemented)
    async startTyping(roomId) {
        return this.post(`${this.messagingBaseURL}/typing/start/`, {
            room_id: roomId
        });
    }

    async stopTyping(roomId) {
        return this.post(`${this.messagingBaseURL}/typing/stop/`, {
            room_id: roomId
        });
    }

    async getTypingUsers(roomId) {
        return this.get(`${this.messagingBaseURL}/typing/${roomId}/`);
    }

    // Utility methods for direct message creation
    async getOrCreateDirectMessage(userId) {
        try {
            // Try to find existing direct message room
            const rooms = await this.getChatRooms({
                room_type: 'direct',
                participant: userId
            });

            if (rooms.results && rooms.results.length > 0) {
                return rooms.results[0];
            }

            // Create new direct message room
            return await this.createChatRoom({
                room_type: 'direct',
                participants: [userId],
                name: '' // Direct messages don't need names
            });
        } catch (error) {
            console.error('Error getting/creating direct message:', error);
            throw error;
        }
    }

    // Search functionality
    async searchMessages(query, roomId = null) {
        const params = { search: query };
        if (roomId) {
            params.room = roomId;
        }
        const queryString = this.buildQueryString(params);
        return this.get(`${this.messagingBaseURL}/messages/${queryString}`);
    }

    async searchChatRooms(query) {
        const queryString = this.buildQueryString({ search: query });
        return this.get(`${this.messagingBaseURL}/rooms/${queryString}`);
    }

    // File upload for message attachments
    async uploadMessageAttachment(file, messageType = 'image') {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('message_type', messageType);

        return this.post(`${this.messagingBaseURL}/attachments/`, formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    }

    // Helper methods for UI
    getMessageTypeIcon(messageType) {
        const icons = {
            text: '💬',
            image: '📸',
            video: '🎥',
            audio: '🎵',
            file: '📎',
            location: '📍',
            system: '⚙️'
        };
        return icons[messageType] || '💬';
    }

    getPresenceColor(status) {
        const colors = {
            online: '#44bb44',
            away: '#ffaa00',
            busy: '#ff4444',
            offline: '#999999',
            invisible: '#999999'
        };
        return colors[status] || '#999999';
    }

    getPresenceText(status) {
        const texts = {
            online: 'En ligne',
            away: 'Absent',
            busy: 'Occupé',
            offline: 'Hors ligne',
            invisible: 'Invisible'
        };
        return texts[status] || 'Inconnu';
    }

    // Format message timestamp
    formatMessageTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        // Less than a minute
        if (diff < 60000) {
            return 'À l\'instant';
        }

        // Less than an hour
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}min`;
        }

        // Same day
        if (date.toDateString() === now.toDateString()) {
            return date.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        // Different day
        return date.toLocaleDateString('fr-FR', {
            day: 'numeric',
            month: 'short'
        });
    }
}

// Create and export singleton instance
export const messagingAPI = new MessagingAPI();
export default messagingAPI;

// Export organized methods for easy importing
export const {
    // Chat Rooms
    getChatRooms,
    getChatRoom,
    createChatRoom,
    updateChatRoom,
    deleteChatRoom,
    addParticipant,
    removeParticipant,

    // Messages
    getMessages,
    sendMessage,
    updateMessage,
    deleteMessage,
    markMessageAsRead,
    markRoomAsRead,

    // Reactions
    addReaction,
    removeReaction,
    getMessageReactions,

    // Presence
    updatePresence,
    getPresence,
    getOnlineUsers,

    // Typing
    startTyping,
    stopTyping,
    getTypingUsers,

    // Utilities
    getOrCreateDirectMessage,
    searchMessages,
    searchChatRooms,
    uploadMessageAttachment
} = messagingAPI;