import React from 'react';
import styles from './ChatNotification.module.css';

const ChatNotification = ({ message, type = 'info', onClose }) => {
    if (!message) return null;

    return (
        <div className={`${styles.notification} ${styles[type]}`}>
            <span className={styles.message}>{message}</span>
            {onClose && (
                <button className={styles.closeButton} onClick={onClose}>
                    ×
                </button>
            )}
        </div>
    );
};

export default ChatNotification;