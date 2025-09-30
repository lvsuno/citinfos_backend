import React, { useEffect, useRef } from 'react';
import styles from './ReactionsPanel.module.css';

const ReactionsPanel = ({ isVisible, onReactionSelect, onClose, currentReaction }) => {
    const panelRef = useRef(null);

    const reactions = [
        { type: 'like', emoji: '👍', label: 'J\'aime' },
        { type: 'love', emoji: '❤️', label: 'Adore' },
        { type: 'haha', emoji: '😂', label: 'Haha' },
        { type: 'wow', emoji: '😮', label: 'Wow' },
        { type: 'sad', emoji: '😢', label: 'Triste' },
        { type: 'angry', emoji: '😠', label: 'Grrr' }
    ];

    useEffect(() => {
        if (isVisible && panelRef.current) {
            const panel = panelRef.current;
            const rect = panel.getBoundingClientRect();
            const viewportWidth = window.innerWidth;

            // Réinitialiser les attributs
            panel.removeAttribute('data-overflow');

            // Vérifier le débordement
            if (rect.right > viewportWidth - 20) {
                panel.setAttribute('data-overflow', 'right');
            } else if (rect.left < 20) {
                panel.setAttribute('data-overflow', 'left');
            }
        }
    }, [isVisible]);

    if (!isVisible) return null;

    return (
        <div
            ref={panelRef}
            className={styles.reactionsPanel}
        >
            {reactions.map(({ type, emoji, label }) => (
                <button
                    key={type}
                    className={`${styles.reactionOption} ${currentReaction === type ? styles.active : ''}`}
                    onClick={() => onReactionSelect(type)}
                    aria-label={label}
                >
                    <span className={styles.reactionIcon}>{emoji}</span>
                    <span className={styles.reactionLabel}>{label}</span>
                </button>
            ))}
        </div>
    );
};

export default ReactionsPanel;