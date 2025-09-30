// Context pour gérer la municipalité active
import React, { createContext, useContext, useState } from 'react';
import { searchMunicipalities } from '../data/municipalitiesUtils';

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

    const switchMunicipality = (municipalityName) => {
        // Rechercher la municipalité dans notre base de données
        const municipality = searchMunicipalities(municipalityName, 1)[0];
        if (municipality) {
            setActiveMunicipality(municipality);
            // Sauvegarder dans localStorage
            localStorage.setItem('selectedMunicipality', municipality.nom);
        }
    };

    const getMunicipalitySlug = (municipalityName) => {
        return municipalityName
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '') // Enlever les accents
            .replace(/[^a-z0-9]/g, '-') // Remplacer caractères spéciaux par tirets
            .replace(/-+/g, '-') // Remplacer tirets multiples par un seul
            .replace(/^-|-$/g, ''); // Enlever tirets en début/fin
    };

    // Récupérer la municipalité sauvegardée au démarrage
    React.useEffect(() => {
        const savedMunicipalityName = localStorage.getItem('selectedMunicipality');
        if (savedMunicipalityName) {
            const municipality = searchMunicipalities(savedMunicipalityName, 1)[0];
            if (municipality) {
                setActiveMunicipality(municipality);
            }
        }
    }, []);

    const contextValue = {
        activeMunicipality,
        switchMunicipality,
        getMunicipalitySlug
    };

    return (
        <MunicipalityContext.Provider value={contextValue}>
            {children}
        </MunicipalityContext.Provider>
    );
};

export default MunicipalityContext;