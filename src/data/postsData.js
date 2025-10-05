// Données générales des posts par municipalité
import { sherbrookePosts } from './sherbrookePosts';

// Structure centralisée de tous les posts par municipalité
export const allPosts = {
    'Sherbrooke': sherbrookePosts,
    // Autres municipalités pourront être ajoutées ici
    // 'Magog': magogPosts,
    // 'Lennoxville': lennoxvillePosts,
    // etc.
};

// Fonction principale pour obtenir les posts d'une municipalité
export const getPostsByMunicipality = (municipalityName) => {
    const posts = allPosts[municipalityName] || [];
    return posts.filter(post =>
        post.municipality.toLowerCase() === municipalityName.toLowerCase()
    );
};

// Fonction pour obtenir les posts d'une municipalité et d'une section spécifique
export const getPostsByMunicipalityAndSection = (municipalityName, section) => {
    const posts = allPosts[municipalityName] || [];
    return posts.filter(post =>
        post.municipality.toLowerCase() === municipalityName.toLowerCase() &&
        post.section.toLowerCase() === section.toLowerCase()
    );
};

// Fonction pour obtenir toutes les sections disponibles pour une municipalité
export const getSectionsByMunicipality = (municipalityName) => {
    const posts = allPosts[municipalityName] || [];
    const sections = [...new Set(posts.map(post => post.section))];
    return sections.sort();
};

// Fonction pour obtenir le nombre de posts par section pour une municipalité
export const getPostCountBySection = (municipalityName) => {
    const posts = allPosts[municipalityName] || [];
    const counts = {};

    posts.forEach(post => {
        const section = post.section;
        counts[section] = (counts[section] || 0) + 1;
    });

    return counts;
};

// Fonction pour ajouter un nouveau post (pour les créations dynamiques)
export const addPost = (municipalityName, post) => {
    if (!allPosts[municipalityName]) {
        allPosts[municipalityName] = [];
    }

    const newPost = {
        ...post,
        id: `post-${municipalityName.toLowerCase()}-${Date.now()}`,
        municipality: municipalityName,
        timestamp: new Date(),
        reactions: { like: 0, love: 0, haha: 0, wow: 0, sad: 0, angry: 0 },
        userReaction: null,
        comments: [],
        commentsCount: 0
    };

    allPosts[municipalityName].unshift(newPost);
    return newPost;
};

const postsData = {
    getPostsByMunicipality,
    getPostsByMunicipalityAndSection,
    getSectionsByMunicipality,
    getPostCountBySection,
    addPost,
    allPosts
};

export default postsData;