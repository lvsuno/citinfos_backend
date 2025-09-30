import React from 'react';
import { getPostsByMunicipality, getPostsByMunicipalityAndSection } from '../data/postsData';
import Post from './Post';
import styles from './PostFeed.module.css';

const PostFeed = ({ municipalityName, section = null }) => {
    if (!municipalityName) {
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>⚠️</div>
                <h3>Erreur de chargement</h3>
                <p>Impossible de charger les publications sans spécifier la municipalité.</p>
            </div>
        );
    }

    // Filtrer les posts selon la municipalité et optionnellement la section
    const posts = section
        ? getPostsByMunicipalityAndSection(municipalityName, section)
        : getPostsByMunicipality(municipalityName);

    if (!posts || posts.length === 0) {
        const sectionText = section ? ` dans la section "${section}"` : '';
        return (
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>📝</div>
                <h3>Aucune publication pour le moment</h3>
                <p>Soyez le premier à partager quelque chose d'intéressant{sectionText} à {municipalityName} !</p>
            </div>
        );
    }

    return (
        <div className={styles.postFeed}>
            {posts.map(post => (
                <Post key={post.id} post={post} />
            ))}
        </div>
    );
};

export default PostFeed;