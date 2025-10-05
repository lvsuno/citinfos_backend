import React, { useState } from 'react';
import {
    Add as AddIcon,
    PhotoLibrary as PhotoLibraryIcon,
    VideoFile as VideoFileIcon,
    Send as SendIcon,
    Close as CloseIcon,
    AutoAwesome as AutoAwesomeIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import styles from './PostCreator.module.css';

const PostCreator = ({ onPostCreated, sectionName, municipalityName }) => {
    const { user } = useAuth();
    const [isExpanded, setIsExpanded] = useState(false);
    const [content, setContent] = useState('');
    const [attachments, setAttachments] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const handleFileSelect = (event) => {
        const files = Array.from(event.target.files);
        const newAttachments = files.map(file => ({
            id: Date.now() + Math.random(),
            file,
            type: file.type.startsWith('image/') ? 'image' : 'video',
            url: URL.createObjectURL(file),
            name: file.name
        }));

        setAttachments(prev => [...prev, ...newAttachments]);
    };

    const removeAttachment = (id) => {
        setAttachments(prev => {
            const updated = prev.filter(att => att.id !== id);
            // Nettoyer l'URL d'objet pour éviter les fuites mémoire
            const toRemove = prev.find(att => att.id === id);
            if (toRemove) {
                URL.revokeObjectURL(toRemove.url);
            }
            return updated;
        });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!content.trim() && attachments.length === 0) return;

        setIsSubmitting(true);
        try {
            // Simuler la création d'un post
            const newPost = {
                id: Date.now(),
                content: content.trim(),
                attachments: attachments.map(att => ({
                    id: att.id,
                    type: att.type,
                    name: att.name,
                    url: att.url // Dans un vrai projet, ceci serait une URL uploadée
                })),
                author: {
                    id: user.id,
                    name: `${user.firstName} ${user.lastName}`,
                    avatar: user.avatar
                },
                section: sectionName,
                municipality: municipalityName,
                createdAt: new Date().toISOString(),
                likes: 0,
                comments: []
            };

            // Appeler la fonction callback pour ajouter le post
            if (onPostCreated) {
                onPostCreated(newPost);
            }

            // Réinitialiser le formulaire
            setContent('');
            setAttachments([]);
            setIsExpanded(false);
        } catch (error) {
            console.error('Erreur lors de la création du post:', error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const getUserInitials = () => {
        if (user?.firstName && user?.lastName) {
            return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
        }
        if (user?.username) {
            return user.username[0].toUpperCase();
        }
        return 'U';
    };

    return (
        <div className={styles.postCreator}>
            <div className={styles.creatorHeader} onClick={() => setIsExpanded(true)}>
                <div className={styles.userAvatar}>
                    {user?.avatar ? (
                        <img src={user.avatar} alt="Avatar" />
                    ) : (
                        <span>{getUserInitials()}</span>
                    )}
                </div>
                <div className={styles.placeholder}>
                    {isExpanded ? '' : `Quoi de neuf dans ${sectionName} à ${municipalityName} ?`}
                </div>
                {!isExpanded && (
                    <button className={styles.expandButton}>
                        <AddIcon />
                    </button>
                )}
            </div>

            {isExpanded && (
                <form onSubmit={handleSubmit} className={styles.expandedForm}>
                    <div className={styles.formHeader}>
                        <div className={styles.headerContent}>
                            <AutoAwesomeIcon className={styles.headerIcon} />
                            <h3>Créer une publication</h3>
                        </div>
                        <button
                            type="button"
                            className={styles.closeButton}
                            onClick={() => setIsExpanded(false)}
                        >
                            <CloseIcon />
                        </button>
                    </div>                    <div className={styles.contentArea}>
                        <textarea
                            placeholder={`Partagez quelque chose d'intéressant sur ${sectionName} à ${municipalityName}...`}
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            className={styles.contentInput}
                            rows={4}
                            autoFocus
                        />
                    </div>

                    {attachments.length > 0 && (
                        <div className={styles.attachmentPreview}>
                            {attachments.map(attachment => (
                                <div key={attachment.id} className={styles.attachment}>
                                    {attachment.type === 'image' ? (
                                        <img src={attachment.url} alt={attachment.name} />
                                    ) : (
                                        <div className={styles.videoPreview}>
                                            <VideoFileIcon />
                                            <span>{attachment.name}</span>
                                        </div>
                                    )}
                                    <button
                                        type="button"
                                        className={styles.removeAttachment}
                                        onClick={() => removeAttachment(attachment.id)}
                                    >
                                        <CloseIcon />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className={styles.formActions}>
                        <div className={styles.attachmentButtons}>
                            <input
                                type="file"
                                id="file-input"
                                accept="image/*,video/*"
                                multiple
                                onChange={handleFileSelect}
                                style={{ display: 'none' }}
                            />
                            <label htmlFor="file-input" className={styles.attachButton}>
                                <PhotoLibraryIcon />
                                Média
                            </label>
                        </div>

                        <button
                            type="submit"
                            className={styles.submitButton}
                            disabled={isSubmitting || (!content.trim() && attachments.length === 0)}
                        >
                            {isSubmitting ? (
                                <div className={styles.spinner} />
                            ) : (
                                <>
                                    <SendIcon />
                                    Publier
                                </>
                            )}
                        </button>
                    </div>
                </form>
            )}
        </div>
    );
};

export default PostCreator;