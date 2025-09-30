import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { Home as HomeIcon, Gavel as GavelIcon } from '@mui/icons-material';
import styles from './TermsPage.module.css';

const TermsPage = () => {
    return (
        <div className={styles.termsPage}>
            {/* Retour à l'accueil */}
            <Link to="/" className={styles.backToHome}>
                <HomeIcon /> Retour à l'accueil
            </Link>

            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col lg={8} xl={7}>
                        <Card className={styles.termsCard}>
                            <Card.Body className={styles.cardBody}>
                                {/* Header */}
                                <div className={styles.header}>
                                    <div className={styles.iconBadge}>
                                        <GavelIcon className={styles.headerIcon} />
                                    </div>
                                    <h1 className={styles.title}>Conditions d'utilisation</h1>
                                    <p className={styles.subtitle}>
                                        Dernière mise à jour : {new Date().toLocaleDateString('fr-CA', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        })}
                                    </p>
                                </div>

                                {/* Contenu */}
                                <div className={styles.content}>
                                    <section className={styles.section}>
                                        <h2>1. Acceptation des conditions</h2>
                                        <p>
                                            En utilisant la plateforme Communauté, vous acceptez d'être lié par ces conditions d'utilisation.
                                            Si vous n'acceptez pas ces conditions, veuillez ne pas utiliser nos services.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>2. Description du service</h2>
                                        <p>
                                            Communauté est une plateforme numérique qui facilite les interactions entre les citoyens et leurs
                                            municipalités. Notre service permet :
                                        </p>
                                        <ul>
                                            <li>La communication directe avec les représentants municipaux</li>
                                            <li>L'accès aux informations et services municipaux</li>
                                            <li>La participation à la vie démocratique locale</li>
                                            <li>Le signalement de problèmes dans votre communauté</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>3. Inscription et compte utilisateur</h2>
                                        <p>
                                            Pour utiliser certaines fonctionnalités, vous devez créer un compte. Vous vous engagez à :
                                        </p>
                                        <ul>
                                            <li>Fournir des informations exactes et complètes</li>
                                            <li>Maintenir la sécurité de votre mot de passe</li>
                                            <li>Notifier immédiatement tout usage non autorisé de votre compte</li>
                                            <li>Être responsable de toutes les activités sous votre compte</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>4. Code de conduite</h2>
                                        <p>
                                            En utilisant notre plateforme, vous acceptez de :
                                        </p>
                                        <ul>
                                            <li>Respecter tous les utilisateurs et représentants municipaux</li>
                                            <li>Ne pas publier de contenu offensant, diffamatoire ou illégal</li>
                                            <li>Utiliser un langage approprié et constructif</li>
                                            <li>Ne pas partager d'informations personnelles d'autres utilisateurs</li>
                                            <li>Respecter les droits de propriété intellectuelle</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>5. Protection des données</h2>
                                        <p>
                                            Nous nous engageons à protéger vos données personnelles conformément à notre
                                            <Link to="/privacy" className={styles.link}> politique de confidentialité</Link>.
                                            Vos informations ne seront utilisées que pour améliorer votre expérience sur la plateforme
                                            et faciliter vos interactions avec votre municipalité.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>6. Propriété intellectuelle</h2>
                                        <p>
                                            Tout le contenu de la plateforme, incluant le design, les textes, les graphiques et les logos,
                                            est protégé par les lois sur la propriété intellectuelle. Vous ne pouvez pas reproduire,
                                            distribuer ou modifier ce contenu sans notre autorisation écrite.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>7. Limitation de responsabilité</h2>
                                        <p>
                                            Nous nous efforçons de maintenir la plateforme accessible et fonctionnelle, mais nous ne
                                            garantissons pas un service ininterrompu. Nous ne sommes pas responsables des dommages
                                            indirects ou consécutifs résultant de l'utilisation de nos services.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>8. Modifications des conditions</h2>
                                        <p>
                                            Nous nous réservons le droit de modifier ces conditions à tout moment. Les utilisateurs
                                            seront notifiés des changements importants par email ou via la plateforme. L'utilisation
                                            continue de nos services après modification constitue une acceptation des nouvelles conditions.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>9. Résiliation</h2>
                                        <p>
                                            Vous pouvez fermer votre compte à tout moment en nous contactant. Nous nous réservons le
                                            droit de suspendre ou fermer des comptes qui violent ces conditions d'utilisation.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>10. Contact</h2>
                                        <p>
                                            Pour toute question concernant ces conditions d'utilisation, veuillez nous contacter à :
                                        </p>
                                        <div className={styles.contactInfo}>
                                            <p><strong>Email :</strong> support@communaute-platform.ca</p>
                                            <p><strong>Adresse :</strong> 123 Rue de la Municipalité, Sherbrooke, QC J1H 2R3</p>
                                        </div>
                                    </section>
                                </div>

                                {/* Footer */}
                                <div className={styles.footer}>
                                    <p>
                                        Ces conditions d'utilisation sont régies par les lois du Québec, Canada.
                                    </p>
                                    <div className={styles.actions}>
                                        <Link to="/signup" className={styles.primaryButton}>
                                            J'accepte et je m'inscris
                                        </Link>
                                        <Link to="/privacy" className={styles.secondaryButton}>
                                            Politique de confidentialité
                                        </Link>
                                    </div>
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </Container>
        </div>
    );
};

export default TermsPage;