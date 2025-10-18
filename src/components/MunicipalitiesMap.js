import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMap } from 'react-leaflet';
import { Icon } from 'leaflet';
import { useNavigate } from 'react-router-dom';
import { useMunicipality } from '../contexts/MunicipalityContext';
import { setCurrentDivision } from '../utils/divisionStorage';
import styles from './MunicipalitiesMap.module.css';

// Import CSS de Leaflet
import 'leaflet/dist/leaflet.css';

const activeIcon = new Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [30, 49],
    iconAnchor: [15, 49],
    popupAnchor: [1, -42],
    shadowSize: [50, 50]
});

// Composant pour centrer la carte sur une municipalité
const MapCenterController = ({ center, zoom, bounds }) => {
    const map = useMap();

    useEffect(() => {
        if (bounds) {
            // Use fitBounds for showing entire boundary - auto-calculates zoom
            map.fitBounds(bounds, { padding: [50, 50] }); // 50px padding around edges
        } else if (center) {
            // Fallback to center/zoom if no bounds available
            map.setView(center, zoom);
        }
    }, [map, center, zoom, bounds]);

    return null;
};

const MunicipalitiesMap = ({
    selectedMunicipality,
    onMunicipalitySelect,
    selectedCountry,
    selectedLevel1,  // NEW: Level 1 division (region/province)
    height = '500px'
}) => {
    const [divisionGeometry, setDivisionGeometry] = useState(null);
    const [divisionCentroid, setDivisionCentroid] = useState(null);
    // eslint-disable-next-line no-unused-vars
    const [countryBoundary, setCountryBoundary] = useState(null); // NEW: Country boundary
    const [level1Boundary, setLevel1Boundary] = useState(null); // NEW: Level 1 boundary
    const [mapCenter, setMapCenter] = useState([46.8139, -71.2082]); // Default: Quebec center
    const [mapZoom, setMapZoom] = useState(6);
    const [mapBounds, setMapBounds] = useState(null); // NEW: For fitBounds instead of fixed zoom
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { switchMunicipality } = useMunicipality();

    // Helper to calculate bounding box from coordinates
    const calculateBounds = (coordinates, geometryType) => {
        let allCoords = [];

        if (geometryType === 'Polygon') {
            allCoords = coordinates;
        } else if (geometryType === 'MultiPolygon') {
            // Flatten MultiPolygon coordinates
            coordinates.forEach(polygon => {
                allCoords = allCoords.concat(polygon);
            });
        }

        if (allCoords.length === 0) return null;

        const lats = allCoords.map(coord => coord[0]);
        const lngs = allCoords.map(coord => coord[1]);

        return [
            [Math.min(...lats), Math.min(...lngs)], // Southwest corner
            [Math.max(...lats), Math.max(...lngs)]  // Northeast corner
        ];
    };

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

                    // Calculate bounding box for better zoom level
                    const bounds = calculateBounds(coordinates, geom.type);
                    if (bounds) {
                        setMapBounds(bounds);                    } else if (data.centroid) {
                        // Fallback: use centroid + fixed zoom if bounds fail
                        const centroid = [data.centroid.coordinates[1], data.centroid.coordinates[0]];
                        setMapCenter(centroid);
                        setMapZoom(10);
                        setMapBounds(null);
                    }

                    // Set centroid for marker (still needed for marker placement)
                    if (data.centroid) {
                        const centroid = [data.centroid.coordinates[1], data.centroid.coordinates[0]];
                        setDivisionCentroid(centroid);
                    }
                }
            } catch (error) {            } finally {
                setLoading(false);
            }
        };

        fetchDivisionGeometry();
    }, [selectedMunicipality]);

    // Fetch country boundary when country changes (for exploration visualization)
    useEffect(() => {
        const fetchCountryBoundary = async () => {
            // Only show country boundary if:
            // 1. A country is selected
            // 2. No level1 division is selected (would show region instead)
            // 3. No final division is selected (would show that instead)
            if (!selectedCountry || selectedLevel1 || selectedMunicipality) {
                setCountryBoundary(null);
                return;
            }
            // For now, just zoom to country's general area based on iso3
            // You can expand this to fetch actual country geometry if available
            const countryZooms = {
                'CAN': { center: [56.1304, -106.3468], zoom: 4 },  // Canada
                'USA': { center: [37.0902, -95.7129], zoom: 4 },   // USA
                'FRA': { center: [46.2276, 2.2137], zoom: 6 },     // France
                'BEN': { center: [9.3077, 2.3158], zoom: 7 },      // Benin
                'DEU': { center: [51.1657, 10.4515], zoom: 6 },    // Germany
                'GBR': { center: [55.3781, -3.4360], zoom: 6 },    // UK
            };

            const countryView = countryZooms[selectedCountry.iso3] || { center: [0, 0], zoom: 2 };
            setMapCenter(countryView.center);
            setMapZoom(countryView.zoom);
            setMapBounds(null); // Clear bounds - using center/zoom for countries
        };

        fetchCountryBoundary();
    }, [selectedCountry, selectedLevel1, selectedMunicipality]);

    // Fetch level1 boundary when level1 division changes (region/province visualization)
    useEffect(() => {
        const fetchLevel1Boundary = async () => {
            // Only show level1 boundary if:
            // 1. A level1 division is selected
            // 2. No final division is selected (would show that instead)
            if (!selectedLevel1 || selectedMunicipality) {
                setLevel1Boundary(null);
                return;
            }
            try {
                // Fetch level1 division geometry
                const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
                const response = await fetch(`${API_BASE_URL}/auth/divisions/${selectedLevel1.id}/geometry/`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.geometry) {
                    const geom = data.geometry;

                    // Convert geometry to Leaflet coordinates
                    let coordinates = null;
                    if (geom.type === 'Polygon') {
                        coordinates = geom.coordinates[0].map(coord => [coord[1], coord[0]]);
                    } else if (geom.type === 'MultiPolygon') {
                        coordinates = geom.coordinates.map(polygon =>
                            polygon[0].map(coord => [coord[1], coord[0]])
                        );
                    }

                    setLevel1Boundary({
                        type: geom.type,
                        coordinates
                    });

                    // Calculate and set bounding box for the region
                    const bounds = calculateBounds(coordinates, geom.type);
                    if (bounds) {
                        setMapBounds(bounds);                    } else {
                        // Fallback: use centroid if bounds calculation fails
                        if (data.centroid) {
                            const centroid = [data.centroid.coordinates[1], data.centroid.coordinates[0]];
                            setMapCenter(centroid);
                            setMapZoom(8);
                            setMapBounds(null); // Clear bounds to use center/zoom
                        }
                    }                }
            } catch (error) {            }
        };

        fetchLevel1Boundary();
    }, [selectedLevel1, selectedMunicipality]);

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
                <MapCenterController center={mapCenter} zoom={mapZoom} bounds={mapBounds} />

                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                {/* Display level1 boundary (region/province) - shown when level1 selected but no final division */}
                {level1Boundary && !divisionGeometry && (
                    <>
                        {level1Boundary.type === 'Polygon' ? (
                            <Polygon
                                positions={level1Boundary.coordinates}
                                pathOptions={{
                                    color: '#3b82f6',        // Blue stroke
                                    fillColor: '#3b82f6',    // Blue fill
                                    fillOpacity: 0.15,       // Light fill
                                    weight: 2
                                }}
                            />
                        ) : level1Boundary.type === 'MultiPolygon' ? (
                            level1Boundary.coordinates.map((polygon, index) => (
                                <Polygon
                                    key={`level1-${index}`}
                                    positions={polygon}
                                    pathOptions={{
                                        color: '#3b82f6',
                                        fillColor: '#3b82f6',
                                        fillOpacity: 0.15,
                                        weight: 2
                                    }}
                                />
                            ))
                        ) : null}
                    </>
                )}

                {/* Display division polygon - shown when final division is selected */}
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