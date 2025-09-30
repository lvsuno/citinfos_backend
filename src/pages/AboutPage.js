import React, { useEffect, useState } from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import {
    Home as HomeIcon,
    LocationOn as LocationOnIcon,
    People as PeopleIcon,
    TrendingUp as TrendingUpIcon,
    Public as PublicIcon
} from '@mui/icons-material';
import { getMunicipalitiesStats, getMunicipalitiesByRegion } from '../data/municipalitiesUtils';
import styles from './AboutPage.module.css';

const AboutPage = () => {
    const [stats, setStats] = useState(null);
    const [regionalData, setRegionalData] = useState({});

    useEffect(() => {
        const municipalitiesStats = getMunicipalitiesStats();
        const regionData = getMunicipalitiesByRegion();

        setStats(municipalitiesStats);
        setRegionalData(regionData);
    }, []);

    if (!stats) {
        return <div>Chargement...</div>;
    }

    return (
        <div className={styles.aboutPage}>
            {/* Retour à l'accueil */}
            <Link to="/" className={styles.backToHome}>
                <HomeIcon /> Retour à l'accueil
            </Link>

            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col lg={10} xl={9}>
                        {/* Header */}
                        <div className={styles.header}>
                            <div className={styles.iconBadge}>
                                <PublicIcon className={styles.headerIcon} />
                            </div>
                            <h1 className={styles.title}>À propos de notre plateforme</h1>
                            <p className={styles.subtitle}>
                                Connecter toutes les municipalités du Québec avec leurs citoyens
                            </p>
                        </div>

                        {/* Statistiques principales */}
                        <Row className="mb-5">
                            <Col md={3} sm={6} className="mb-4">
                                <Card className={styles.statCard}>
                                    <Card.Body className={styles.statBody}>
                                        <div className={styles.statIcon}>
                                            <LocationOnIcon />
                                        </div>
                                        <div className={styles.statValue}>{stats.totalMunicipalities}</div>
                                        <div className={styles.statLabel}>Municipalités</div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            <Col md={3} sm={6} className="mb-4">
                                <Card className={styles.statCard}>
                                    <Card.Body className={styles.statBody}>
                                        <div className={styles.statIcon}>
                                            <PeopleIcon />
                                        </div>
                                        <div className={styles.statValue}>
                                            {(stats.totalPopulation / 1000000).toFixed(1)}M
                                        </div>
                                        <div className={styles.statLabel}>Habitants</div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            <Col md={3} sm={6} className="mb-4">
                                <Card className={styles.statCard}>
                                    <Card.Body className={styles.statBody}>
                                        <div className={styles.statIcon}>
                                            <PublicIcon />
                                        </div>
                                        <div className={styles.statValue}>{stats.regions.length}</div>
                                        <div className={styles.statLabel}>Régions</div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            <Col md={3} sm={6} className="mb-4">
                                <Card className={styles.statCard}>
                                    <Card.Body className={styles.statBody}>
                                        <div className={styles.statIcon}>
                                            <TrendingUpIcon />
                                        </div>
                                        <div className={styles.statValue}>100%</div>
                                        <div className={styles.statLabel}>Couverture</div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>

                        {/* Plus grandes villes */}
                        <Row>
                            <Col lg={6} className="mb-4">
                                <Card className={styles.contentCard}>
                                    <Card.Body>
                                        <h3 className={styles.cardTitle}>Les 10 plus grandes villes</h3>
                                        <div className={styles.cityList}>
                                            {stats.largestCities.map((city, index) => (
                                                <div key={city.nom} className={styles.cityItem}>
                                                    <div className={styles.cityRank}>{index + 1}</div>
                                                    <div className={styles.cityInfo}>
                                                        <div className={styles.cityName}>{city.nom}</div>
                                                        <div className={styles.cityDetails}>
                                                            {city.region} • {city.population.toLocaleString('fr-CA')} hab.
                                                        </div>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>

                            {/* Régions */}
                            <Col lg={6} className="mb-4">
                                <Card className={styles.contentCard}>
                                    <Card.Body>
                                        <h3 className={styles.cardTitle}>Régions du Québec</h3>
                                        <div className={styles.regionList}>
                                            {stats.regions.map(region => (
                                                <div key={region} className={styles.regionItem}>
                                                    <div className={styles.regionName}>{region}</div>
                                                    <div className={styles.regionCount}>
                                                        {regionalData[region]?.length || 0} municipalités
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>

                        {/* Mission */}
                        <Row>
                            <Col>
                                <Card className={styles.contentCard}>
                                    <Card.Body>
                                        <h3 className={styles.cardTitle}>Notre Mission</h3>
                                        <div className={styles.missionContent}>
                                            <p>
                                                Notre plateforme vise à révolutionner la communication entre les citoyens et leurs
                                                administrations municipales à travers tout le Québec. En connectant <strong>{stats.totalMunicipalities}</strong> municipalités
                                                réparties sur <strong>{stats.regions.length}</strong> régions, nous facilitons l'engagement citoyen et
                                                la participation démocratique locale.
                                            </p>
                                            <p>
                                                Avec plus de <strong>{(stats.totalPopulation / 1000000).toFixed(1)} millions</strong> d'habitants
                                                potentiellement connectés, notre plateforme représente une opportunité unique de moderniser
                                                les services publics municipaux et de créer un dialogue constructif entre les citoyens et
                                                leurs élus.
                                            </p>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </Col>
                        </Row>

                        {/* Footer Actions */}
                        <div className={styles.footerActions}>
                            <Link to="/signup" className={styles.primaryButton}>
                                Rejoindre la communauté
                            </Link>
                            <Link to="/login" className={styles.secondaryButton}>
                                Se connecter
                            </Link>
                        </div>
                    </Col>
                </Row>
            </Container>
        </div>
    );
};

export default AboutPage;