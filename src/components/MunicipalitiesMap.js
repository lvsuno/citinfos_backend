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
    height = '500px',
    showAllMunicipalities = false  // NEW: Option to show all municipalities
}) => {
    const [divisionGeometry, setDivisionGeometry] = useState(null);
    const [divisionCentroid, setDivisionCentroid] = useState(null);
    const [countryBoundary, setCountryBoundary] = useState(null); // NEW: Country boundary
    const [level1Boundary, setLevel1Boundary] = useState(null); // NEW: Level 1 boundary
    const [allMunicipalities, setAllMunicipalities] = useState(null); // NEW: All municipalities
    const [mapCenter, setMapCenter] = useState([46.8139, -71.2082]); // Default: Quebec center
    const [mapZoom, setMapZoom] = useState(6);
    const [mapBounds, setMapBounds] = useState(null); // NEW: For fitBounds instead of fixed zoom
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { switchMunicipality, getMunicipalitySlug } = useMunicipality();

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
                        setMapBounds(bounds);
                        console.log('✅ Division boundary loaded, fitting to bounds');
                    } else if (data.centroid) {
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
            } catch (error) {
                console.error('Error fetching division geometry:', error);
            } finally {
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

            console.log('🌍 Fetching country boundary for:', selectedCountry.name);

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
            console.log('✅ Zoomed to country:', selectedCountry.name);
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

            console.log('🗺️ Fetching level1 boundary for:', selectedLevel1.name);

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
                        setMapBounds(bounds);
                        console.log('✅ Level1 boundary loaded, fitting to bounds:', selectedLevel1.name);
                    } else {
                        // Fallback: use centroid if bounds calculation fails
                        if (data.centroid) {
                            const centroid = [data.centroid.coordinates[1], data.centroid.coordinates[0]];
                            setMapCenter(centroid);
                            setMapZoom(8);
                            setMapBounds(null); // Clear bounds to use center/zoom
                        }
                    }

                    console.log('✅ Level1 boundary loaded for:', selectedLevel1.name);
                }
            } catch (error) {
                console.error('Error fetching level1 boundary:', error);
            }
        };

        fetchLevel1Boundary();
    }, [selectedLevel1, selectedMunicipality]);

    // NEW: Fetch all Quebec municipalities when showAllMunicipalities is true
    useEffect(() => {
        const fetchAllMunicipalities = async () => {
            if (!showAllMunicipalities) {
                setAllMunicipalities(null);
                return;
            }

            console.log('🏘️ Loading all Quebec municipalities...');
            setLoading(true);

            try {
                const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
                // Use simplification for better performance, limit to reasonable number
                const response = await fetch(`${API_BASE_URL}/auth/quebec-municipalities-geojson/?simplify=0.002&limit=500`);

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.features) {
                    setAllMunicipalities(data);
                    console.log(`✅ Loaded ${data.count} municipalities`);

                    // Set map view to Quebec province
                    setMapCenter([46.8139, -71.2082]);
                    setMapZoom(7);
                    setMapBounds(null);
                } else {
                    console.error('Failed to load municipalities:', data.error);
                }
            } catch (error) {
                console.error('Error loading all municipalities:', error);
            } finally {
                setLoading(false);
            }
        };

        fetchAllMunicipalities();
    }, [showAllMunicipalities]);

    // Helper function to change user location to selected municipality
    const handleChangeLocation = (municipalityData) => {
        if (municipalityData.name && municipalityData.id) {
            // Update municipality context with both name and ID
            switchMunicipality(municipalityData.name, municipalityData.id);

            // Create slug from municipality name
            const municipalitySlug = municipalityData.name
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

            let typeSlug = boundaryTypeMap['municipality'] || 'municipality';

            // Store as current active division
            const countryCode = 'CAN'; // Quebec municipalities are in Canada
            setCurrentDivision({
                id: municipalityData.id,
                name: municipalityData.name,
                slug: municipalitySlug,
                country: countryCode,
                parent: municipalityData.parent_name ? { name: municipalityData.parent_name } : null,
                boundary_type: 'Municipalité',
                admin_level: municipalityData.admin_level || 4,
                admin_code: municipalityData.admin_code
            });

            // Navigate to municipality page
            navigate(`/${typeSlug}/${municipalitySlug}`);
        }
    };

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

                {/* NEW: Display all Quebec municipalities */}
                {allMunicipalities && allMunicipalities.features.map((feature, index) => {
                    const { geometry, properties } = feature;

                    // Convert GeoJSON coordinates to Leaflet format
                    let coordinates = null;
                    if (geometry.type === 'Polygon') {
                        coordinates = geometry.coordinates[0].map(coord => [coord[1], coord[0]]);
                    } else if (geometry.type === 'MultiPolygon') {
                        coordinates = geometry.coordinates.map(polygon =>
                            polygon[0].map(coord => [coord[1], coord[0]])
                        );
                    }

                    if (!coordinates) return null;

                    const handleMunicipalityClick = () => {
                        if (onMunicipalitySelect) {
                            // Create municipality object compatible with existing interface
                            const municipality = {
                                id: properties.id,
                                name: properties.name,
                                admin_code: properties.admin_code,
                                admin_level: properties.admin_level,
                                parent_name: properties.parent_name,
                                boundary_type: 'Municipalité',
                                country: { iso3: 'CAN' }
                            };
                            onMunicipalitySelect(municipality);
                        }
                    };

                    if (geometry.type === 'Polygon') {
                        return (
                            <Polygon
                                key={`municipality-${index}`}
                                positions={coordinates}
                                pathOptions={{
                                    color: '#10b981',       // Green stroke
                                    fillColor: '#10b981',   // Green fill
                                    fillOpacity: 0.1,       // Very light fill
                                    weight: 1,              // Thin border
                                    opacity: 0.7
                                }}
                                eventHandlers={{
                                    click: handleMunicipalityClick,
                                    mouseover: (e) => {
                                        e.target.setStyle({
                                            fillOpacity: 0.3,
                                            weight: 2
                                        });
                                    },
                                    mouseout: (e) => {
                                        e.target.setStyle({
                                            fillOpacity: 0.1,
                                            weight: 1
                                        });
                                    }
                                }}
                            >
                                <Popup>
                                    <div className={styles.popupContent}>
                                        <h3 className={styles.municipalityName}>
                                            {properties.name}
                                        </h3>
                                        {properties.parent_name && (
                                            <p className={styles.regionInfo}>
                                                <strong>MRC:</strong> {properties.parent_name}
                                            </p>
                                        )}
                                        {properties.admin_code && (
                                            <p className={styles.codeInfo}>
                                                <strong>Code:</strong> {properties.admin_code}
                                            </p>
                                        )}
                                        <div className={styles.popupButtons}>
                                            <button
                                                className={styles.visitButton}
                                                onClick={handleMunicipalityClick}
                                            >
                                                Sélectionner {properties.name}
                                            </button>
                                            <button
                                                className={styles.locationButton}
                                                onClick={() => handleChangeLocation(properties)}
                                            >
                                                Me localiser ici
                                            </button>
                                        </div>
                                    </div>
                                </Popup>
                            </Polygon>
                        );
                    } else if (geometry.type === 'MultiPolygon') {
                        return coordinates.map((polygon, polyIndex) => (
                            <Polygon
                                key={`municipality-${index}-${polyIndex}`}
                                positions={polygon}
                                pathOptions={{
                                    color: '#10b981',
                                    fillColor: '#10b981',
                                    fillOpacity: 0.1,
                                    weight: 1,
                                    opacity: 0.7
                                }}
                                eventHandlers={{
                                    click: handleMunicipalityClick,
                                    mouseover: (e) => {
                                        e.target.setStyle({
                                            fillOpacity: 0.3,
                                            weight: 2
                                        });
                                    },
                                    mouseout: (e) => {
                                        e.target.setStyle({
                                            fillOpacity: 0.1,
                                            weight: 1
                                        });
                                    }
                                }}
                            >
                                {polyIndex === 0 && (
                                    <Popup>
                                        <div className={styles.popupContent}>
                                            <h3 className={styles.municipalityName}>
                                                {properties.name}
                                            </h3>
                                            {properties.parent_name && (
                                                <p className={styles.regionInfo}>
                                                    <strong>MRC:</strong> {properties.parent_name}
                                                </p>
                                            )}
                                            {properties.admin_code && (
                                                <p className={styles.codeInfo}>
                                                    <strong>Code:</strong> {properties.admin_code}
                                                </p>
                                            )}
                                            <div className={styles.popupButtons}>
                                                <button
                                                    className={styles.visitButton}
                                                    onClick={handleMunicipalityClick}
                                                >
                                                    Sélectionner {properties.name}
                                                </button>
                                                <button
                                                    className={styles.locationButton}
                                                    onClick={() => handleChangeLocation(properties)}
                                                >
                                                    Me localiser ici
                                                </button>
                                            </div>
                                        </div>
                                    </Popup>
                                )}
                            </Polygon>
                        ));
                    }

                    return null;
                })}

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
                                <div className={styles.popupButtons}>
                                    <button
                                        className={styles.visitButton}
                                        onClick={handleVisitDivision}
                                    >
                                        Visiter {selectedMunicipality.name}
                                    </button>
                                    <button
                                        className={styles.locationButton}
                                        onClick={() => handleChangeLocation(selectedMunicipality)}
                                    >
                                        Me localiser ici
                                    </button>
                                </div>
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

            {(divisionGeometry || allMunicipalities) && (
                <div className={styles.mapLegend}>
                    {divisionGeometry && (
                        <div className={styles.legendItem}>
                            <span className={styles.legendIconCyan}></span>
                            <span>{getDivisionTypeLabel()}</span>
                        </div>
                    )}
                    {allMunicipalities && (
                        <div className={styles.legendItem}>
                            <span className={styles.legendIconGreen}></span>
                            <span>Municipalités du Québec ({allMunicipalities.count})</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default MunicipalitiesMap;