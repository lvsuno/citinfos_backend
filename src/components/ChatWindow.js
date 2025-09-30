import React, { useState, useRef, useEffect } from 'react';
import {
    Send as SendIcon,
    AttachFile as AttachIcon,
    EmojiEmotions as EmojiIcon,
    Info as InfoIcon,
    MoreVert as MoreIcon
} from '@mui/icons-material';
import styles from './ChatWindow.module.css';

const ChatWindow = ({ conversation, messages, onSendMessage, currentUser, onClose }) => {
    const [newMessage, setNewMessage] = useState('');
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);

    // Émojis populaires pour le picker
    const popularEmojis = [
        '😀', '😂', '🥰', '😍', '🤔', '😮', '😢', '😡', '👍', '👎',
        '❤️', '💙', '💚', '💛', '🔥', '👏', '🎉', '💯', '✨', '🚀'
    ];

    // Auto-scroll vers le bas quand de nouveaux messages arrivent
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (newMessage.trim()) {
            onSendMessage(newMessage);
            setNewMessage('');
            setShowEmojiPicker(false);

            // Simuler l'indicateur de frappe
            setIsTyping(true);
            setTimeout(() => setIsTyping(false), 1000);
        }
    };

    const handleEmojiClick = (emoji) => {
        setNewMessage(prev => prev + emoji);
        setShowEmojiPicker(false);
        inputRef.current?.focus();
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const formatMessageTime = (timestamp) => {
        const messageTime = new Date(timestamp);
        return messageTime.toLocaleTimeString('fr-CA', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    };

    const formatMessageDate = (timestamp) => {
        const messageDate = new Date(timestamp);
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);

        if (messageDate.toDateString() === today.toDateString()) {
            return 'Aujourd\'hui';
        } else if (messageDate.toDateString() === yesterday.toDateString()) {
            return 'Hier';
        } else {
            return messageDate.toLocaleDateString('fr-CA', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        }
    };

    // Regrouper les messages par date
    const groupMessagesByDate = (messages) => {
        const groups = {};
        messages.forEach(message => {
            const dateKey = new Date(message.timestamp).toDateString();
            if (!groups[dateKey]) {
                groups[dateKey] = [];
            }
            groups[dateKey].push(message);
        });
        return groups;
    };

    const messageGroups = groupMessagesByDate(messages);

    return (
        <div className={styles.chatWindow}>
            {/* Header de la conversation */}
            <div className={styles.chatHeader}>
                <div className={styles.contactInfo}>
                    <img
                        src={conversation.avatar}
                        alt={conversation.name}
                        className={styles.contactAvatar}
                    />
                    <div className={styles.contactDetails}>
                        <h3 className={styles.contactName}>{conversation.name}</h3>
                        <p className={styles.contactStatus}>
                            {conversation.isOnline ? (
                                <>
                                    <span className={styles.onlineIndicator}></span>
                                    En ligne
                                </>
                            ) : (
                                'Hors ligne'
                            )}
                        </p>
                    </div>
                </div>

                <div className={styles.chatActions}>
                    <button className={styles.actionButton} title="Informations">
                        <InfoIcon />
                    </button>
                    <button className={styles.actionButton} title="Plus d'options">
                        <MoreIcon />
                    </button>
                </div>
            </div>

            {/* Zone des messages */}
            <div className={styles.messagesContainer}>
                {Object.keys(messageGroups).length === 0 ? (
                    <div className={styles.emptyMessages}>
                        <div className={styles.emptyIcon}>💬</div>
                        <p>Aucun message pour le moment</p>
                        <p className={styles.emptySubtext}>
                            Commencez votre conversation avec {conversation.name}
                        </p>
                    </div>
                ) : (
                    Object.entries(messageGroups).map(([dateKey, dateMessages]) => (
                        <div key={dateKey} className={styles.messageGroup}>
                            {/* Séparateur de date */}
                            <div className={styles.dateSeparator}>
                                <span className={styles.dateLabel}>
                                    {formatMessageDate(new Date(dateKey))}
                                </span>
                            </div>

                            {/* Messages de cette date */}
                            {dateMessages.map((message, index) => {
                                const isCurrentUser = message.senderId === (currentUser?.id || 'current');
                                const showAvatar = !isCurrentUser && (
                                    index === 0 ||
                                    dateMessages[index - 1]?.senderId !== message.senderId
                                );

                                return (
                                    <div
                                        key={message.id}
                                        className={`${styles.messageWrapper} ${isCurrentUser ? styles.sent : styles.received
                                            }`}
                                    >
                                        {showAvatar && (
                                            <img
                                                src={conversation.avatar}
                                                alt={message.senderName}
                                                className={styles.messageAvatar}
                                            />
                                        )}

                                        <div className={styles.messageContent}>
                                            <div className={`${styles.messageBubble} ${isCurrentUser ? styles.sentBubble : styles.receivedBubble
                                                }`}>
                                                <p className={styles.messageText}>
                                                    {message.content}
                                                </p>
                                            </div>

                                            <div className={styles.messageTime}>
                                                {formatMessageTime(message.timestamp)}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    ))
                )}

                {/* Indicateur de frappe */}
                {isTyping && (
                    <div className={styles.typingIndicator}>
                        <div className={styles.typingDots}>
                            <span></span>
                            <span></span>
                            <span></span>
                        </div>
                        <span className={styles.typingText}>
                            {conversation.name} est en train d'écrire...
                        </span>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Zone de saisie */}
            <div className={styles.inputContainer}>
                {/* Picker d'émojis */}
                {showEmojiPicker && (
                    <div className={styles.emojiPicker}>
                        <div className={styles.emojiGrid}>
                            {popularEmojis.map((emoji, index) => (
                                <button
                                    key={index}
                                    className={styles.emojiButton}
                                    onClick={() => handleEmojiClick(emoji)}
                                >
                                    {emoji}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <form onSubmit={handleSendMessage} className={styles.inputForm}>
                    <button
                        type="button"
                        className={styles.attachButton}
                        title="Joindre un fichier"
                    >
                        <AttachIcon />
                    </button>

                    <div className={styles.messageInputContainer}>
                        <textarea
                            ref={inputRef}
                            value={newMessage}
                            onChange={(e) => setNewMessage(e.target.value)}
                            onKeyPress={handleKeyPress}
                            placeholder={`Écrivez un message à ${conversation.name}...`}
                            className={styles.messageInput}
                            rows="1"
                        />

                        <button
                            type="button"
                            className={styles.emojiButton}
                            onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                            title="Ajouter un emoji"
                        >
                            <EmojiIcon />
                        </button>
                    </div>

                    <button
                        type="submit"
                        className={`${styles.sendButton} ${newMessage.trim() ? styles.active : ''
                            }`}
                        disabled={!newMessage.trim()}
                    >
                        <SendIcon />
                    </button>
                </form>
            </div>
        </div>
    );
};

export default ChatWindow;