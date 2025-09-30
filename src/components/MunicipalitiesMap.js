import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import { getAllMunicipalities } from '../data/municipalitiesUtils';
import styles from './MunicipalitiesMap.module.css';

// Import CSS de Leaflet
import 'leaflet/dist/leaflet.css';

// Configuration des icônes Leaflet
const defaultIcon = new Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const activeIcon = new Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [30, 49],
    iconAnchor: [15, 49],
    popupAnchor: [1, -42],
    shadowSize: [50, 50]
});

// Composant pour centrer la carte sur une municipalité
const MapCenterController = ({ center, zoom }) => {
    const map = useMap();

    useEffect(() => {
        if (center) {
            map.setView(center, zoom);
        }
    }, [map, center, zoom]);

    return null;
};

const MunicipalitiesMap = ({ selectedMunicipality, onMunicipalitySelect, height = '500px' }) => {
    const [municipalities, setMunicipalities] = useState([]);
    const [mapCenter, setMapCenter] = useState([46.8139, -71.2082]); // Centre du Québec
    const [mapZoom, setMapZoom] = useState(6);

    useEffect(() => {
        // Charger toutes les municipalités avec des coordonnées approximatives
        const loadMunicipalities = () => {
            const allMunicipalities = getAllMunicipalities();

            // Pour cette démo, nous allons générer des coordonnées approximatives
            // basées sur les régions. En production, vous devriez avoir les vraies coordonnées.
            const municipalitiesWithCoords = allMunicipalities.map(municipality => {
                const coords = getApproximateCoordinates(municipality);
                return {
                    ...municipality,
                    latitude: coords[0],
                    longitude: coords[1]
                };
            });

            setMunicipalities(municipalitiesWithCoords);
        };

        loadMunicipalities();
    }, []);

    // Fonction pour obtenir des coordonnées approximatives par région
    const getApproximateCoordinates = (municipality) => {
        const regionCoords = {
            'Bas-Saint-Laurent': [47.8, -68.5],
            'Saguenay-Lac-Saint-Jean': [48.5, -72.0],
            'Capitale-Nationale': [46.8, -71.2],
            'Mauricie': [46.7, -72.8],
            'Estrie': [45.5, -71.8],
            'Montréal': [45.5, -73.6],
            'Outaouais': [45.5, -75.7],
            'Abitibi-Témiscamingue': [48.2, -78.0],
            'Côte-Nord': [50.2, -66.4],
            'Nord-du-Québec': [53.0, -77.0],
            'Gaspésie-Îles-de-la-Madeleine': [48.8, -64.5],
            'Chaudière-Appalaches': [46.5, -70.8],
            'Laval': [45.6, -73.7],
            'Lanaudière': [46.0, -73.8],
            'Laurentides': [45.9, -74.2],
            'Montérégie': [45.3, -73.2],
            'Centre-du-Québec': [46.2, -72.5]
        };

        const baseCoords = regionCoords[municipality.region] || [46.8, -71.2];

        // Ajouter une petite variation aléatoire pour éviter la superposition
        const variation = 0.3;
        const lat = baseCoords[0] + (Math.random() - 0.5) * variation;
        const lng = baseCoords[1] + (Math.random() - 0.5) * variation;

        return [lat, lng];
    };

    const handleMunicipalityClick = (municipality) => {
        // Centrer la carte sur la municipalité
        setMapCenter([municipality.latitude, municipality.longitude]);
        setMapZoom(10);

        // Callback pour le parent (pour afficher les infos dans la sidebar)
        if (onMunicipalitySelect) {
            onMunicipalitySelect(municipality);
        }
    };

    // Mettre à jour le centre de la carte si une municipalité est sélectionnée
    useEffect(() => {
        if (selectedMunicipality) {
            const selected = municipalities.find(m => m.nom === selectedMunicipality.nom);
            if (selected) {
                setMapCenter([selected.latitude, selected.longitude]);
                setMapZoom(12);
            }
        }
    }, [selectedMunicipality, municipalities]);

    return (
        <div className={styles.mapContainer} style={{ height }}>
            <MapContainer
                center={mapCenter}
                zoom={mapZoom}
                style={{ height: '100%', width: '100%' }}
                className={styles.leafletMap}
            >
                <MapCenterController center={mapCenter} zoom={mapZoom} />

                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {municipalities.map((municipality) => {
                    const isSelected = selectedMunicipality?.nom === municipality.nom;

                    return (
                        <Marker
                            key={municipality.nom}
                            position={[municipality.latitude, municipality.longitude]}
                            icon={isSelected ? activeIcon : defaultIcon}
                            eventHandlers={{
                                click: () => handleMunicipalityClick(municipality),
                            }}
                        >
                            <Popup>
                                <div className={styles.popupContent}>
                                    <h3 className={styles.municipalityName}>{municipality.nom}</h3>
                                    <p className={styles.regionInfo}>
                                        <strong>Région:</strong> {municipality.region}
                                    </p>
                                    {municipality.mrc && municipality.mrc !== municipality.region && (
                                        <p className={styles.mrcInfo}>
                                            <strong>MRC:</strong> {municipality.mrc}
                                        </p>
                                    )}
                                    {municipality.population && (
                                        <p className={styles.populationInfo}>
                                            <strong>Population:</strong> {municipality.population.toLocaleString('fr-CA')} habitants
                                        </p>
                                    )}
                                    <button
                                        className={styles.visitButton}
                                        onClick={() => handleMunicipalityClick(municipality)}
                                    >
                                        Visiter {municipality.nom}
                                    </button>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            <div className={styles.mapLegend}>
                <div className={styles.legendItem}>
                    <span className={styles.legendIconBlue}></span>
                    <span>Municipalités</span>
                </div>
                <div className={styles.legendItem}>
                    <span className={styles.legendIconGreen}></span>
                    <span>Municipalité sélectionnée</span>
                </div>
            </div>
        </div>
    );
};

export default MunicipalitiesMap;