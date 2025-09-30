import React, { useState, useRef, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import chatStyles from './ChatPage.module.css';

// Icons
import SearchIcon from '@mui/icons-material/Search';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import EmojiEmotionsIcon from '@mui/icons-material/EmojiEmotions';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import FiberManualRecordIcon from '@mui/icons-material/FiberManualRecord';

const ChatPage = () => {
    const { municipalitySlug } = useParams();
    const [selectedConversation, setSelectedConversation] = useState(null);
    const [conversations, setConversations] = useState([
        {
            id: 1,
            name: 'Marie Dubois',
            municipality: 'Sherbrooke',
            lastMessage: 'Salut! Comment ça va?',
            lastMessageTime: '14:30',
            unreadCount: 2,
            online: true,
            avatar: null
        },
        {
            id: 2,
            name: 'Jean Tremblay',
            municipality: 'Magog',
            lastMessage: 'Merci pour l\'information!',
            lastMessageTime: '13:45',
            unreadCount: 0,
            online: false,
            avatar: null
        },
        {
            id: 3,
            name: 'Sophie Martin',
            municipality: 'Granby',
            lastMessage: 'À bientôt!',
            lastMessageTime: 'Hier',
            unreadCount: 1,
            online: true,
            avatar: null
        }
    ]);

    const [messages, setMessages] = useState({
        1: [
            { id: 1, sender: 'Marie Dubois', content: 'Salut! Comment ça va?', timestamp: '14:25', isOwn: false },
            { id: 2, sender: 'Moi', content: 'Ça va très bien, merci! Et toi?', timestamp: '14:28', isOwn: true },
            { id: 3, sender: 'Marie Dubois', content: 'Super! J\'aimerais organiser un événement culturel à Sherbrooke. Tu as des idées?', timestamp: '14:30', isOwn: false }
        ],
        2: [
            { id: 1, sender: 'Jean Tremblay', content: 'Bonjour! Pouvez-vous m\'aider avec l\'organisation de l\'événement?', timestamp: '13:40', isOwn: false },
            { id: 2, sender: 'Moi', content: 'Bien sûr! Je vais vous envoyer les détails.', timestamp: '13:42', isOwn: true },
            { id: 3, sender: 'Jean Tremblay', content: 'Merci pour l\'information!', timestamp: '13:45', isOwn: false }
        ],
        3: [
            { id: 1, sender: 'Sophie Martin', content: 'Salut! L\'événement de samedi était génial!', timestamp: 'Hier 16:20', isOwn: false },
            { id: 2, sender: 'Moi', content: 'Oui, c\'était vraiment réussi!', timestamp: 'Hier 16:25', isOwn: true },
            { id: 3, sender: 'Sophie Martin', content: 'À bientôt!', timestamp: 'Hier 16:30', isOwn: false }
        ]
    });

    const [newMessage, setNewMessage] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const messagesEndRef = useRef(null);

    const filteredConversations = conversations.filter(conv =>
        conv.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        conv.municipality.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, selectedConversation]);

    const handleSendMessage = () => {
        if (newMessage.trim() && selectedConversation) {
            const newMsg = {
                id: Date.now(),
                sender: 'Moi',
                content: newMessage.trim(),
                timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
                isOwn: true
            };

            setMessages(prev => ({
                ...prev,
                [selectedConversation.id]: [...(prev[selectedConversation.id] || []), newMsg]
            }));

            setConversations(prev => prev.map(conv =>
                conv.id === selectedConversation.id
                    ? { ...conv, lastMessage: newMessage.trim(), lastMessageTime: 'À l\'instant' }
                    : conv
            ));

            setNewMessage('');
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    };

    const getInitials = (name) => {
        return name.split(' ').map(n => n[0]).join('').toUpperCase();
    };

    return (
        <div className={chatStyles.chatContainer}>
            {/* Sidebar des conversations */}
            <div className={chatStyles.conversationsSidebar}>
                <div className={chatStyles.sidebarHeader}>
                    <div className={chatStyles.searchContainer}>
                        <SearchIcon className={chatStyles.searchIcon} />
                        <input
                            type="text"
                            placeholder="Rechercher des conversations..."
                            className={chatStyles.searchInput}
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <button className={chatStyles.newChatButton}>
                        <PersonAddIcon />
                    </button>
                </div>

                        <div className={chatStyles.conversationsList}>
                            {filteredConversations.map(conversation => (
                                <div
                                    key={conversation.id}
                                    className={`${chatStyles.conversationItem} ${
                                        selectedConversation?.id === conversation.id ? chatStyles.selected : ''
                                    }`}
                                    onClick={() => setSelectedConversation(conversation)}
                                >
                                    <div className={chatStyles.avatarContainer}>
                                        <div className={chatStyles.avatar}>
                                            {getInitials(conversation.name)}
                                        </div>
                                        {conversation.online && (
                                            <FiberManualRecordIcon className={chatStyles.onlineIndicator} />
                                        )}
                                    </div>
                                    <div className={chatStyles.conversationInfo}>
                                        <div className={chatStyles.conversationHeader}>
                                            <h4 className={chatStyles.contactName}>{conversation.name}</h4>
                                            <span className={chatStyles.timestamp}>{conversation.lastMessageTime}</span>
                                        </div>
                                        <div className={chatStyles.conversationFooter}>
                                            <p className={chatStyles.lastMessage}>{conversation.lastMessage}</p>
                                            {conversation.unreadCount > 0 && (
                                                <span className={chatStyles.unreadBadge}>
                                                    {conversation.unreadCount}
                                                </span>
                                            )}
                                        </div>
                                        <span className={chatStyles.municipality}>{conversation.municipality}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Zone de chat principale */}
                    <div className={chatStyles.chatWindow}>
                        {selectedConversation ? (
                            <>
                                <div className={chatStyles.chatHeader}>
                                    <div className={chatStyles.chatHeaderInfo}>
                                        <div className={chatStyles.avatar}>
                                            {getInitials(selectedConversation.name)}
                                        </div>
                                        <div>
                                            <h3 className={chatStyles.chatTitle}>{selectedConversation.name}</h3>
                                            <p className={chatStyles.chatSubtitle}>
                                                {selectedConversation.municipality} • {selectedConversation.online ? 'En ligne' : 'Hors ligne'}
                                            </p>
                                        </div>
                                    </div>
                                    <button className={chatStyles.menuButton}>
                                        <MoreVertIcon />
                                    </button>
                                </div>

                                <div className={chatStyles.messagesContainer}>
                                    {messages[selectedConversation.id]?.map(message => (
                                        <div
                                            key={message.id}
                                            className={`${chatStyles.messageWrapper} ${
                                                message.isOwn ? chatStyles.own : chatStyles.other
                                            }`}
                                        >
                                            <div className={chatStyles.messageBubble}>
                                                <p className={chatStyles.messageContent}>{message.content}</p>
                                                <span className={chatStyles.messageTimestamp}>{message.timestamp}</span>
                                            </div>
                                        </div>
                                    ))}
                                    <div ref={messagesEndRef} />
                                </div>

                                <div className={chatStyles.messageInput}>
                                    <button className={chatStyles.attachButton}>
                                        <AttachFileIcon />
                                    </button>
                                    <div className={chatStyles.inputContainer}>
                                        <textarea
                                            value={newMessage}
                                            onChange={(e) => setNewMessage(e.target.value)}
                                            onKeyPress={handleKeyPress}
                                            placeholder="Tapez votre message..."
                                            className={chatStyles.textInput}
                                            rows="1"
                                        />
                                        <button className={chatStyles.emojiButton}>
                                            <EmojiEmotionsIcon />
                                        </button>
                                    </div>
                                    <button
                                        onClick={handleSendMessage}
                                        className={chatStyles.sendButton}
                                        disabled={!newMessage.trim()}
                                    >
                                        <SendIcon />
                                    </button>
                                </div>
                            </>
                        ) : (
                            <div className={chatStyles.emptyChatState}>
                                <ChatBubbleOutlineIcon className={chatStyles.emptyChatIcon} />
                                <h3>Sélectionnez une conversation</h3>
                                <p>Choisissez une conversation existante ou commencez-en une nouvelle</p>
                            </div>
                        )}
                    </div>
                </div>
        </div>
    );
};

export default ChatPage;