import React from 'react';
import { formatTimeAgo } from '../utils/timeUtils';
import styles from './PostHeader.module.css';

const PostHeader = ({ author, timestamp, section }) => {
    return (
        <div className={styles.postHeader}>
            <div className={styles.authorInfo}>
                <div className={styles.authorAvatar}>
                    {author.avatar ? (
                        <img src={author.avatar} alt={author.name} />
                    ) : (
                        author.initials
                    )}
                </div>
                <div className={styles.authorDetails}>
                    <h3 className={styles.authorName}>{author.name}</h3>
                    <div className={styles.postMeta}>
                        <span className={styles.timestamp}>{formatTimeAgo(timestamp)}</span>
                        <span className={styles.separator}>•</span>
                        <span className={styles.postSection}>{section}</span>
                    </div>
                </div>
            </div>
            <button className={styles.moreButton} aria-label="Plus d'options">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                </svg>
            </button>
        </div>
    );
};

export default PostHeader;