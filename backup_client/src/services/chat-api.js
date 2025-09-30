// Chat API service for real-time messaging
import BaseAPIService from './baseAPI';

class ChatAPI extends BaseAPIService {
  constructor() {
    super();
  }

  chatRooms = {
    list: async () => this.get('/chatrooms/'),
    get: async (roomId) => this.get(`/chatrooms/${roomId}/`),
    create: async (roomData = {}) => this.post('/chatrooms/', roomData),
    update: async (roomId, roomData = {}) => this.patch(`/chatrooms/${roomId}/`, roomData),
    delete: async (roomId) => this.delete(`/chatrooms/${roomId}/`),
    addParticipant: async (roomId, userId) => this.post(`/chatrooms/${roomId}/add_participant/`, { user_id: userId }),
    removeParticipant: async (roomId, userId) => this.post(`/chatrooms/${roomId}/remove_participant/`, { user_id: userId }),
  };

  messages = {
    list: async (roomId, page = 1, limit = 50) => {
      const endpoint = this.buildEndpoint(`/chatrooms/${roomId}/messages/`, { page, limit });
      return this.get(endpoint);
    },
    get: async (messageId) => this.get(`/messages/${messageId}/`),
    send: async (roomId, messageData) => {
      // For file uploads, we need to use FormData and the raw API instance
      if (messageData.attachments && messageData.attachments.length > 0) {
        const formData = new FormData();
        formData.append('content', messageData.content);
        formData.append('message_type', messageData.message_type || 'text');
        messageData.attachments.forEach((file, index) => {
          formData.append(`attachment_${index}`, file);
        });

        const response = await this.api.post(`/chatrooms/${roomId}/messages/`, formData);
        return response.data;
      } else {
        return this.post(`/chatrooms/${roomId}/messages/`, messageData);
      }
    },
    update: async (messageId, messageData = {}) => this.patch(`/messages/${messageId}/`, messageData),
    delete: async (messageId) => this.delete(`/messages/${messageId}/`),
    markAsRead: async (messageId) => this.post(`/messages/${messageId}/mark_read/`),
    markAllAsRead: async (roomId) => this.post(`/chatrooms/${roomId}/mark_all_read/`),
  };

  search = {
    messages: async (query, roomId) => {
      const endpoint = this.buildEndpoint('/search/messages/', {
        q: query,
        room: roomId,
      });
      return this.get(endpoint);
    },
    rooms: async (query) => this.get(`/search/chatrooms/?q=${encodeURIComponent(query)}`),
  };

  realtime = {
    connectToRoom: (roomId, onMessage) => {
      const interval = setInterval(() => {
        if (typeof onMessage === 'function') {
          onMessage({ type: 'heartbeat', roomId, ts: Date.now() });
        }
      }, 5000);
      return { disconnect: () => clearInterval(interval) };
    },
    sendTyping: async (roomId, isTyping) => this.post(`/chatrooms/${roomId}/typing/`, { is_typing: isTyping }),
  };
}

export const chatAPI = new ChatAPI();
export default chatAPI;
