// Utilitaires pour les municipalités du Québec
import municipalitesData from './municipalites_quebec.json';
import { getAdminDivisionUrlPath, getCurrentAdminDivision, getAdminDivisionLabels } from '../config/adminDivisions';

/**
 * Obtenir toutes les municipalités du Québec
 * @returns {Array} Liste complète des municipalités
 */
export const getAllMunicipalities = () => {
    return municipalitesData.villes.map(ville => ({
        nom: ville.nom,
        region: ville.region,
        mrc: ville.mrc || ville.region,
        population: ville.population_estimee,
        coordonnees: ville.coordonnees
    }));
};

export const getMunicipalitiesStats = () => {
    const villes = municipalitesData.villes;

    return {
        totalMunicipalities: villes.length,
        totalPopulation: villes.reduce((sum, ville) => sum + (ville.population_estimee || 0), 0),
        regions: [...new Set(villes.map(ville => ville.region))].sort(),
        largestCities: villes
            .filter(ville => ville.population_estimee)
            .sort((a, b) => b.population_estimee - a.population_estimee)
            .slice(0, 10)
            .map(ville => ({
                nom: ville.nom,
                population: ville.population_estimee,
                region: ville.region
            }))
    };
};

export const getMunicipalitiesByRegion = () => {
    const villes = municipalitesData.villes;
    const byRegion = {};

    villes.forEach(ville => {
        if (!byRegion[ville.region]) {
            byRegion[ville.region] = [];
        }
        byRegion[ville.region].push({
            nom: ville.nom,
            population: ville.population_estimee,
            superficie: ville.superficie_km2
        });
    });

    // Trier les villes par population dans chaque région
    Object.keys(byRegion).forEach(region => {
        byRegion[region].sort((a, b) => (b.population || 0) - (a.population || 0));
    });

    return byRegion;
};

export const searchMunicipalities = (searchTerm, limit = 10) => {
    if (!searchTerm) return [];

    const villes = municipalitesData.villes;
    const searchLower = searchTerm.toLowerCase();

    return villes
        .filter(ville =>
            ville.nom.toLowerCase().includes(searchLower) ||
            ville.region.toLowerCase().includes(searchLower) ||
            ville.mrc?.toLowerCase().includes(searchLower)
        )
        .sort((a, b) => {
            // Prioriser les correspondances exactes au début du nom
            const aStartsWith = a.nom.toLowerCase().startsWith(searchLower);
            const bStartsWith = b.nom.toLowerCase().startsWith(searchLower);

            if (aStartsWith && !bStartsWith) return -1;
            if (!aStartsWith && bStartsWith) return 1;

            // Ensuite trier par population (plus grande en premier)
            return (b.population_estimee || 0) - (a.population_estimee || 0);
        })
        .slice(0, limit)
        .map(ville => ({
            nom: ville.nom,
            region: ville.region,
            population: ville.population_estimee,
            mrc: ville.mrc
        }));
};

export const getMunicipalityDetails = (municipalityName) => {
    return municipalitesData.villes.find(ville =>
        ville.nom.toLowerCase() === municipalityName.toLowerCase()
    );
};

/**
 * Convertit le nom d'une municipalité en slug d'URL
 * @param {string} municipalityName - Le nom de la municipalité
 * @returns {string} Le slug pour l'URL
 */
export const getMunicipalitySlug = (municipalityName) => {
    if (!municipalityName) return null;

    return municipalityName
        .toLowerCase()
        .normalize('NFD') // Normalise les caractères accentués
        .replace(/[\u0300-\u036f]/g, '') // Supprime les accents
        .replace(/[^a-z0-9\s-]/g, '') // Garde seulement lettres, chiffres, espaces et tirets
        .replace(/\s+/g, '-') // Remplace les espaces par des tirets
        .replace(/-+/g, '-') // Évite les tirets multiples
        .trim('-'); // Supprime les tirets en début/fin
};

/**
 * Génère l'URL complète vers la page d'une division administrative (municipalité, commune, etc.)
 * @param {string} municipalityName - Le nom de la division administrative
 * @param {string} section - La section par défaut (par défaut: 'accueil')
 * @returns {string} L'URL vers la division administrative
 */
export const getMunicipalityUrl = (municipalityName, section = 'accueil') => {
    const slug = getMunicipalitySlug(municipalityName);
    if (!slug) return '/dashboard'; // Fallback vers le dashboard générique

    // Utiliser le type de division administrative dynamique
    const adminDivisionPath = getAdminDivisionUrlPath();
    return `/${adminDivisionPath}/${slug}/${section}`;
};

/**
 * Obtenir l'URL de redirection pour un utilisateur
 * @param {object} user - L'utilisateur
 * @returns {string} L'URL de redirection
 */
export const getUserRedirectUrl = (user) => {
    console.log('🔧 getUserRedirectUrl called with user:', user);

    if (!user) {
        console.log('🔧 No user, returning /dashboard');
        return '/dashboard';
    }

    // Priorité 0: Vérifier le rôle de l'utilisateur (peut être dans user.role ou user.profile.role)
    const userRole = user.role || (user.profile && user.profile.role);
    console.log('🔧 User role detected:', userRole);

    if (userRole === 'admin') {
        console.log('🔧 Admin user detected, redirecting to admin dashboard');
        return '/admin/dashboard';
    }

    if (userRole === 'moderator') {
        console.log('🔧 Moderator user detected, redirecting to moderator dashboard');
        return '/moderator/dashboard';
    }

    // Priorité 1: city dans location
    if (user.location && user.location.city) {
        console.log('🔧 User has location.city:', user.location.city);
        return getMunicipalityUrl(user.location.city);
    }

    // Priorité 2: municipality directement sur l'utilisateur
    if (user.municipality) {
        console.log('🔧 User has municipality:', user.municipality);
        return getMunicipalityUrl(user.municipality);
    }

    // Fallback: dashboard générique
    console.log('🔧 Fallback to /dashboard');
    return '/dashboard';
};

/**
 * Trouve une division administrative par son slug d'URL
 * @param {string} slug - Le slug de la division administrative
 * @returns {object|null} Les données de la division administrative ou null si non trouvée
 */
export const getMunicipalityBySlug = (slug) => {
    if (!slug) return null;

    const villes = municipalitesData.villes;

    // Chercher une correspondance exacte avec le slug généré
    return villes.find(ville => {
        const villeSlug = getMunicipalitySlug(ville.nom);
        return villeSlug === slug;
    }) || null;
};

/**
 * Obtient les informations sur le type de division administrative actuel
 * @returns {object} Configuration de la division administrative
 */
export const getAdminDivisionInfo = () => {
    return getCurrentAdminDivision();
};

/**
 * Obtient les libellés localisés pour la division administrative actuelle
 * @param {string} language - Langue (fr, en, etc.)
 * @returns {object} Labels localisés
 */
export const getLocalizedAdminLabels = (language = 'fr') => {
    return getAdminDivisionLabels(language);
};