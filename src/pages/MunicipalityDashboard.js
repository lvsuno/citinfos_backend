import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { searchMunicipalities, getMunicipalityBySlug } from '../data/municipalitiesUtils';
import Layout from '../components/Layout';
import PostCreator from '../components/PostCreator';
import PostFeed from '../components/PostFeed';
import styles from './MunicipalityDashboard.module.css';

const MunicipalityDashboard = () => {
    const { municipalitySlug, section = 'accueil' } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const { activeMunicipality, switchMunicipality } = useMunicipality();
    const [municipality, setMunicipality] = useState(null);
    const [loading, setLoading] = useState(true);
    const [activeRubrique, setActiveRubrique] = useState(section || 'accueil');
    const [posts, setPosts] = useState([]);

    // Si pas d'utilisateur connecté, rediriger vers la page de connexion
    useEffect(() => {
        if (!user) {
            navigate('/login');
            return;
        }
    }, [user, navigate]);

    // Charger la municipalité basée sur le slug de l'URL
    useEffect(() => {
        const loadMunicipality = () => {
            const foundMunicipality = getMunicipalityBySlug(municipalitySlug);

            if (foundMunicipality) {
                setMunicipality(foundMunicipality);
                switchMunicipality(foundMunicipality.nom);
            } else {
                // Si municipalité non trouvée, rediriger vers le dashboard général
                navigate('/dashboard');
                return;
            }

            setLoading(false);
        };

        loadMunicipality();
    }, [municipalitySlug, switchMunicipality, navigate]);

    // Mettre à jour la rubrique active quand la section change
    useEffect(() => {
        const currentSection = section || 'accueil';
        setActiveRubrique(currentSection);
    }, [section]);

    const handleRubriqueChange = (rubriquePathOrName) => {
        // Si c'est déjà un path (venant du Sidebar), l'utiliser directement
        // Sinon, c'est peut-être un nom, donc on essaie de le convertir
        const newSection = rubriquePathOrName.toLowerCase();
        setActiveRubrique(newSection);
        navigate(`/municipality/${municipalitySlug}/${newSection}`);
    };

    const handlePostCreated = (newPost) => {
        setPosts(prevPosts => [newPost, ...prevPosts]);
    };

    if (loading) {
        return (
            <div className={styles.loading}>
                <div className={styles.spinner}></div>
                <p>Chargement de {municipalitySlug}...</p>
            </div>
        );
    }

    if (!user) {
        return null; // Évite le flash pendant la redirection
    }

    if (!municipality) {
        return (
            <div className={styles.error}>
                <h2>Municipalité non trouvée</h2>
                <p>La municipalité "{municipalitySlug}" n'a pas été trouvée.</p>
                <button onClick={() => navigate('/dashboard')}>
                    Retour au tableau de bord
                </button>
            </div>
        );
    }

    const subtitle = `Découvrez ${municipality.nom} - ${municipality.region} • ${municipality.population ? `${municipality.population.toLocaleString('fr-CA')} habitants` : 'Population non disponible'}`;

    return (
        <Layout
            activeRubrique={activeRubrique}
            onRubriqueChange={handleRubriqueChange}
            municipalityName={municipality.nom}
        >


            <div className={styles.sectionContent}>
                {renderSectionContent(activeRubrique, municipality, handlePostCreated, posts)}
            </div>
        </Layout>
    );
};

// Fonction pour rendre le contenu spécifique à chaque section
const renderSectionContent = (section, municipality, onPostCreated, posts) => {
    const sectionLower = section.toLowerCase();

    // Fonction pour obtenir le nom d'affichage de la section
    const getSectionDisplayName = (sectionKey) => {
        const sectionNames = {
            'accueil': 'Accueil',
            'actualites': 'Actualités',
            'evenements': 'Événements',
            'transport': 'Transport',
            'commerces': 'Commerces',
            'art': 'Art',
            'litterature': 'Littérature',
            'poesie': 'Poésie',
            'photographie': 'Photographie',
            'histoire': 'Histoire',
            'sport': 'Sport',
            'culture': 'Culture',
            'reconnaissance': 'Reconnaissance',
            'chronologie': 'Chronologie'
        };
        return sectionNames[sectionKey] || sectionKey;
    };

    // Fonction pour obtenir la description de chaque section
    const getSectionDescription = (sectionKey) => {
        const sectionDescriptions = {
            'actualites': 'Partagez les dernières nouvelles, découvertes et moments marquants de votre quotidien local.',
            'evenements': 'Découvrez et annoncez les événements, festivals, spectacles et activités communautaires.',
            'transport': 'Informez-vous sur la circulation, les travaux, les transports en commun et la mobilité urbaine.',
            'commerces': 'Mettez en avant les commerces locaux, leurs nouveautés, promotions et initiatives.',
            'art': 'Exposez vos créations artistiques, découvrez les talents locaux et les expositions.',
            'litterature': 'Partagez vos écrits, recommandations de lecture et discussions littéraires.',
            'poesie': 'Exprimez-vous en vers, partagez vos poèmes et découvrez la poésie locale.',
            'photographie': 'Capturez et partagez la beauté de votre région à travers vos images.',
            'histoire': 'Explorez le patrimoine, les récits historiques et la mémoire collective.',
            'sport': 'Suivez les équipes locales, partagez vos exploits sportifs et événements athlétiques.',
            'culture': 'Célébrez la richesse culturelle locale, traditions et expressions artistiques.',
            'reconnaissance': 'Mettez en lumière les contributions remarquables de votre communauté.',
            'chronologie': 'Retracez l\'évolution et les moments clés de votre municipalité.'
        };
        return sectionDescriptions[sectionKey] || 'Participez aux discussions et partagez vos contributions dans cette section.';
    };

    switch (sectionLower) {
        case 'accueil':
            return (
                <div className={styles.sectionWrapper}>
                    <div className={styles.sectionCover}>
                        <div className={styles.coverContent}>
                            <h1 className={styles.sectionTitle}>Accueil - {municipality.nom}</h1>
                            <p className={styles.sectionDescription}>
                                Découvrez l'activité de votre communauté, connectez-vous avec vos concitoyens et restez informé de tout ce qui se passe à {municipality.nom}.
                            </p>
                        </div>
                    </div>

                    <div className={styles.postsSection}>
                        <PostCreator
                            onPostCreated={onPostCreated}
                            sectionName={getSectionDisplayName(sectionLower)}
                            municipalityName={municipality.nom}
                        />
                        <PostFeed
                            municipalityName={municipality.nom}
                        />
                    </div>
                </div>
            );

        default:
            return (
                <div className={styles.sectionWrapper}>
                    <div className={styles.sectionCover}>
                        <div className={styles.coverContent}>
                            <h1 className={styles.sectionTitle}>{getSectionDisplayName(sectionLower)}</h1>
                            <p className={styles.sectionDescription}>
                                {getSectionDescription(sectionLower)}
                            </p>
                        </div>
                    </div>

                    <div className={styles.postsSection}>
                        <PostCreator
                            onPostCreated={onPostCreated}
                            sectionName={getSectionDisplayName(sectionLower)}
                            municipalityName={municipality.nom}
                        />
                        <PostFeed
                            municipalityName={municipality.nom}
                            section={getSectionDisplayName(sectionLower)}
                        />
                    </div>
                </div>
            );
    }
};

export default MunicipalityDashboard;