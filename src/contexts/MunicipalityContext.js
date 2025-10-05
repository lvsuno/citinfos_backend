// Context pour gérer la division administrative active (municipalité, commune, etc.)
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { searchMunicipalities, getLocalizedAdminLabels, getAdminDivisionInfo } from '../data/municipalitiesUtils';
import { getCurrentDivision, setCurrentDivision } from '../utils/divisionStorage';

const MunicipalityContext = createContext();

export const useMunicipality = () => {
    const context = useContext(MunicipalityContext);
    if (!context) {
        throw new Error('useMunicipality must be used within a MunicipalityProvider');
    }
    return context;
};

export const MunicipalityProvider = ({ children }) => {
    const [activeMunicipality, setActiveMunicipality] = useState(null);
    const { user } = useAuth();

    const switchMunicipality = useCallback((municipalityName, divisionId = null) => {
        // Rechercher la municipalité dans notre base de données
        const municipality = searchMunicipalities(municipalityName, 1)[0];

        if (municipality) {
            // Found in local data - add division ID if provided
            const municipalityWithId = {
                ...municipality,
                id: divisionId || municipality.id
            };
            setActiveMunicipality(municipalityWithId);
            // Note: We no longer persist to localStorage here
            // Page divisions are cached with pageDivision_ prefix in MunicipalityDashboard
        } else if (divisionId) {
            // Not in local data but we have API data - create minimal municipality object
            const apiMunicipality = {
                id: divisionId,
                nom: municipalityName,
                name: municipalityName,
                fromApi: true
            };
            setActiveMunicipality(apiMunicipality);
        }
    }, []); // Empty deps - function doesn't depend on any external values

    const getMunicipalitySlug = (municipalityName) => {
        return municipalityName
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Enlever les accents
            .replace(/[^a-z0-9]/g, '-') // Remplacer caractères spéciaux par tirets
            .replace(/-+/g, '-') // Remplacer tirets multiples par un seul
            .replace(/^-|-$/g, ''); // Enlever tirets en début/fin
    };

    // Clean up old localStorage keys on mount (migration cleanup)
    useEffect(() => {
        // Remove old keys that are no longer used
        const oldKeys = ['selectedMunicipality', 'selectedMunicipalityId'];
        oldKeys.forEach(key => {
            if (localStorage.getItem(key)) {
                console.log(`🧹 Cleaning up old localStorage key: ${key}`);
                localStorage.removeItem(key);
            }
        });

        // Load current division from localStorage on mount ONLY if no user
        const currentDivision = getCurrentDivision();
        if (currentDivision && !user) {
            console.log('📍 MunicipalityContext - Loading division from localStorage on mount:', currentDivision.name);
            setActiveMunicipality({
                id: currentDivision.id,
                nom: currentDivision.name,
                name: currentDivision.name,
                region: currentDivision.parent?.name,
                slug: currentDivision.slug,
                country: currentDivision.country,
                boundary_type: currentDivision.boundary_type,
                admin_level: currentDivision.admin_level,
                fromStorage: true
            });
        } else {
            console.log('⚠️ MunicipalityContext - No division found in localStorage on mount or user logged in');
        }
    }, []);

    // Update activeMunicipality when user logs in (PRIORITY over localStorage)
    useEffect(() => {
        if (user?.location) {
            const userLocation = user.location;
            console.log('✅ MunicipalityContext - User logged in, updating activeMunicipality from user location:', userLocation);

            const municipality = {
                id: userLocation.division_id,
                nom: userLocation.city,
                name: userLocation.city,
                region: userLocation.parent_name || userLocation.level_1_name,
                country: userLocation.country,
                boundary_type: userLocation.boundary_type,
                admin_level: userLocation.admin_level,
                level_1_id: userLocation.level_1_id,
                fromUserLogin: true
            };

            setActiveMunicipality(municipality);

            // Also update localStorage with fresh user location
            setCurrentDivision({
                id: userLocation.division_id,
                name: userLocation.city,
                slug: getMunicipalitySlug(userLocation.city),
                country: userLocation.country,
                parent: {
                    id: userLocation.level_1_id,
                    name: userLocation.level_1_name || userLocation.parent_name
                },
                boundary_type: userLocation.boundary_type,
                admin_level: userLocation.admin_level,
                level_1_id: userLocation.level_1_id
            });

            console.log('💾 MunicipalityContext - Saved user location to localStorage');
        }
    }, [user, getMunicipalitySlug]);

    // Fonctions pour obtenir les informations de division administrative
    const getAdminLabels = (language = 'fr') => {
        return getLocalizedAdminLabels(language);
    };

    const getAdminInfo = () => {
        return getAdminDivisionInfo();
    };

    const contextValue = {
        activeMunicipality,
        switchMunicipality,
        getMunicipalitySlug,
        getAdminLabels,
        getAdminInfo
    };

    return (
        <MunicipalityContext.Provider value={contextValue}>
            {children}
        </MunicipalityContext.Provider>
    );
};

export default MunicipalityContext;