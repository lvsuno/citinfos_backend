import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { useMunicipality } from '../contexts/MunicipalityContext';
import geolocationService from '../services/geolocationService';
import { setCurrentDivision } from '../utils/divisionStorage';
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

const MunicipalitiesMap = ({ selectedMunicipality, onMunicipalitySelect, selectedCountry, height = '500px' }) => {
    const [divisionGeometry, setDivisionGeometry] = useState(null);
    const [divisionCentroid, setDivisionCentroid] = useState(null);
    const [mapCenter, setMapCenter] = useState([46.8139, -71.2082]); // Default: Quebec center
    const [mapZoom, setMapZoom] = useState(6);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { switchMunicipality, getMunicipalitySlug } = useMunicipality();

    // Helper to get localized division type label
    const getDivisionTypeLabel = () => {
        if (!selectedCountry) return 'Division sélectionnée';

        // Map country's default_division_name to singular French form
        const divisionName = selectedCountry.default_division_name?.toLowerCase();

        const singularMap = {
            'municipalités': 'Municipalité',
            'municipalities': 'Municipalité',
            'communes': 'Commune',
            'villes': 'Ville',
            'cities': 'Ville',
            'arrondissements': 'Arrondissement',
            'régions': 'Région',
            'regions': 'Région',
            'provinces': 'Province',
            'départements': 'Département',
            'departments': 'Département',
            'préfectures': 'Préfecture',
            'prefectures': 'Préfecture',
        };

        const divisionType = singularMap[divisionName] || 'Division';
        return `${divisionType} sélectionnée`;
    };

    // Fetch division geometry when selectedMunicipality changes
    useEffect(() => {
        const fetchDivisionGeometry = async () => {
            if (!selectedMunicipality?.id) {
                setDivisionGeometry(null);
                setDivisionCentroid(null);
                return;
            }

            setLoading(true);
            try {
                // Fetch division details including geometry
                const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
                const response = await fetch(`${API_BASE_URL}/auth/divisions/${selectedMunicipality.id}/geometry/`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.geometry) {
                    // Parse GeoJSON geometry
                    const geom = data.geometry;

                    // Convert geometry to Leaflet coordinates format
                    let coordinates = null;
                    if (geom.type === 'Polygon') {
                        // Polygon: array of rings, each ring is array of [lng, lat]
                        coordinates = geom.coordinates[0].map(coord => [coord[1], coord[0]]);
                    } else if (geom.type === 'MultiPolygon') {
                        // MultiPolygon: array of polygons
                        coordinates = geom.coordinates.map(polygon =>
                            polygon[0].map(coord => [coord[1], coord[0]])
                        );
                    }

                    setDivisionGeometry({
                        type: geom.type,
                        coordinates
                    });

                    // Set centroid for marker
                    if (data.centroid) {
                        const centroid = [data.centroid.coordinates[1], data.centroid.coordinates[0]];
                        setDivisionCentroid(centroid);
                        setMapCenter(centroid);
                        setMapZoom(10);
                    }
                }
            } catch (error) {
                console.error('Error fetching division geometry:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchDivisionGeometry();
    }, [selectedMunicipality]);

    const handleVisitDivision = () => {
        if (selectedMunicipality?.name && selectedMunicipality?.boundary_type) {
            // Update municipality context with both name and ID
            switchMunicipality(selectedMunicipality.name, selectedMunicipality.id);

            // Create slug from division name
            const divisionSlug = selectedMunicipality.name
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .replace(/[^a-z0-9]/g, '-')
                .replace(/-+/g, '-')
                .replace(/^-|-$/g, '');

            // Convert boundary type to singular English form for URL
            const boundaryTypeMap = {
                'municipalités': 'municipality',
                'municipalities': 'municipality',
                'commune': 'commune',
                'communes': 'commune',
                'city': 'city',
                'cities': 'city',
                'town': 'town',
                'towns': 'town',
                'village': 'village',
                'villages': 'village'
            };

            // Get the mapped type or create slug from original boundary_type
            let typeSlug = boundaryTypeMap[selectedMunicipality.boundary_type.toLowerCase()];

            if (!typeSlug) {
                // If not in map, create slug from boundary type
                typeSlug = selectedMunicipality.boundary_type
                    .toLowerCase()
                    .normalize('NFD')
                    .replace(/[\u0300-\u036f]/g, '')
                    .replace(/[^a-z0-9]/g, '-')
                    .replace(/-+/g, '-')
                    .replace(/^-|-$/g, '');
            }

            // Store as current active division (single source of truth)
            const countryCode = selectedMunicipality.country?.iso3 || 'CAN'; // Default to CAN
            setCurrentDivision({
                id: selectedMunicipality.id,
                name: selectedMunicipality.name,
                slug: divisionSlug,
                country: countryCode,
                parent: selectedMunicipality.parent_name ? { name: selectedMunicipality.parent_name } : null,
                boundary_type: selectedMunicipality.boundary_type,
                admin_level: selectedMunicipality.admin_level,
                admin_code: selectedMunicipality.admin_code
            });

            // Navigate to /{boundary_type}/{division_name}
            navigate(`/${typeSlug}/${divisionSlug}`);
        }
    };

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

                {/* Display division polygon */}
                {divisionGeometry && (
                    <>
                        {divisionGeometry.type === 'Polygon' ? (
                            <Polygon
                                positions={divisionGeometry.coordinates}
                                pathOptions={{
                                    color: '#06b6d4',
                                    fillColor: '#06b6d4',
                                    fillOpacity: 0.2,
                                    weight: 2
                                }}
                            />
                        ) : divisionGeometry.type === 'MultiPolygon' ? (
                            divisionGeometry.coordinates.map((polygon, index) => (
                                <Polygon
                                    key={index}
                                    positions={polygon}
                                    pathOptions={{
                                        color: '#06b6d4',
                                        fillColor: '#06b6d4',
                                        fillOpacity: 0.2,
                                        weight: 2
                                    }}
                                />
                            ))
                        ) : null}
                    </>
                )}

                {/* Display centroid marker */}
                {divisionCentroid && selectedMunicipality && (
                    <Marker
                        position={divisionCentroid}
                        icon={activeIcon}
                    >
                        <Popup>
                            <div className={styles.popupContent}>
                                <h3 className={styles.municipalityName}>
                                    {selectedMunicipality.name}
                                </h3>
                                {selectedMunicipality.parent_name && (
                                    <p className={styles.regionInfo}>
                                        <strong>Parent:</strong> {selectedMunicipality.parent_name}
                                    </p>
                                )}
                                {selectedMunicipality.boundary_type && (
                                    <p className={styles.typeInfo}>
                                        <strong>Type:</strong> {selectedMunicipality.boundary_type}
                                    </p>
                                )}
                                {selectedMunicipality.admin_code && (
                                    <p className={styles.codeInfo}>
                                        <strong>Code:</strong> {selectedMunicipality.admin_code}
                                    </p>
                                )}
                                <button
                                    className={styles.visitButton}
                                    onClick={handleVisitDivision}
                                >
                                    Visiter {selectedMunicipality.name}
                                </button>
                            </div>
                        </Popup>
                    </Marker>
                )}
            </MapContainer>

            {loading && (
                <div className={styles.mapLoading}>
                    <div className={styles.loadingSpinner} />
                    Loading division...
                </div>
            )}

            {divisionGeometry && (
                <div className={styles.mapLegend}>
                    <div className={styles.legendItem}>
                        <span className={styles.legendIconCyan}></span>
                        <span>{getDivisionTypeLabel()}</span>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MunicipalitiesMap;