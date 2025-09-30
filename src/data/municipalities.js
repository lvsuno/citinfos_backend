// Données des municipalités disponibles

export const municipalities = [
    {
        id: 'sherbrooke',
        name: 'Sherbrooke',
        region: 'Estrie',
        province: 'Québec',
        pays: 'Canada',

        population: '167 000',
        coordinates: {
            lat: 45.4042,
            lng: -71.8929
        },
        description: 'Centre urbain de l\'Estrie',
        color: '#06B6D4'
    },
    {
        id: 'drummondville',
        name: 'Drummondville',
        region: 'Centre-du-Québec',
        province: 'Québec',
        pays: 'Canada',
        population: '79 000',
        coordinates: {
            lat: 45.8833,
            lng: -72.4833
        },
        description: 'Carrefour du Centre-du-Québec',
        color: '#84CC16'
    }
];

// Fonction pour obtenir une municipalité par ID
export const getMunicipalityById = (id) => {
    return municipalities.find(municipality => municipality.id === id);
};

// Fonction pour obtenir toutes les municipalités
export const getAllMunicipalities = () => {
    return municipalities;
};

// Municipalité par défaut
export const DEFAULT_MUNICIPALITY = municipalities[0]; // Sherbrooke