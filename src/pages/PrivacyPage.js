import React from 'react';
import { Container, Row, Col, Card } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import { Home as HomeIcon, PrivacyTip as PrivacyTipIcon } from '@mui/icons-material';
import styles from './PrivacyPage.module.css';

const PrivacyPage = () => {
    return (
        <div className={styles.privacyPage}>
            {/* Retour à l'accueil */}
            <Link to="/" className={styles.backToHome}>
                <HomeIcon /> Retour à l'accueil
            </Link>

            <Container className="py-5">
                <Row className="justify-content-center">
                    <Col lg={8} xl={7}>
                        <Card className={styles.privacyCard}>
                            <Card.Body className={styles.cardBody}>
                                {/* Header */}
                                <div className={styles.header}>
                                    <div className={styles.iconBadge}>
                                        <PrivacyTipIcon className={styles.headerIcon} />
                                    </div>
                                    <h1 className={styles.title}>Politique de confidentialité</h1>
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
                                        <h2>1. Introduction</h2>
                                        <p>
                                            Chez Communauté, nous nous engageons à protéger votre vie privée et vos données personnelles.
                                            Cette politique explique comment nous collectons, utilisons et protégeons vos informations
                                            lorsque vous utilisez notre plateforme.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>2. Informations que nous collectons</h2>
                                        <h3>Informations que vous nous fournissez</h3>
                                        <ul>
                                            <li>Nom et prénom</li>
                                            <li>Adresse email</li>
                                            <li>Municipalité de résidence</li>
                                            <li>Messages et communications sur la plateforme</li>
                                            <li>Préférences de notification</li>
                                        </ul>

                                        <h3>Informations collectées automatiquement</h3>
                                        <ul>
                                            <li>Adresse IP et données de localisation générale</li>
                                            <li>Type de navigateur et système d'exploitation</li>
                                            <li>Pages visitées et temps passé sur la plateforme</li>
                                            <li>Données d'utilisation et interactions</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>3. Comment nous utilisons vos informations</h2>
                                        <p>Nous utilisons vos données personnelles pour :</p>
                                        <ul>
                                            <li>Vous fournir l'accès à notre plateforme et ses fonctionnalités</li>
                                            <li>Faciliter la communication avec votre municipalité</li>
                                            <li>Personnaliser votre expérience utilisateur</li>
                                            <li>Envoyer des notifications importantes</li>
                                            <li>Améliorer nos services et développer de nouvelles fonctionnalités</li>
                                            <li>Assurer la sécurité et prévenir les fraudes</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>4. Partage de vos informations</h2>
                                        <p>
                                            Nous ne vendons jamais vos données personnelles. Nous pouvons partager vos informations
                                            uniquement dans les cas suivants :
                                        </p>
                                        <ul>
                                            <li><strong>Avec votre municipalité :</strong> Pour faciliter les communications et services municipaux</li>
                                            <li><strong>Prestataires de services :</strong> Partenaires de confiance qui nous aident à opérer la plateforme</li>
                                            <li><strong>Obligations légales :</strong> Lorsque requis par la loi ou pour protéger nos droits</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>5. Sécurité des données</h2>
                                        <p>
                                            Nous mettons en place des mesures de sécurité techniques et organisationnelles pour protéger
                                            vos données personnelles :
                                        </p>
                                        <ul>
                                            <li>Chiffrement des données en transit et au repos</li>
                                            <li>Contrôles d'accès stricts</li>
                                            <li>Surveillance continue de la sécurité</li>
                                            <li>Audits de sécurité réguliers</li>
                                            <li>Formation du personnel sur la protection des données</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>6. Conservation des données</h2>
                                        <p>
                                            Nous conservons vos données personnelles aussi longtemps que nécessaire pour :
                                        </p>
                                        <ul>
                                            <li>Fournir nos services</li>
                                            <li>Respecter nos obligations légales</li>
                                            <li>Résoudre les litiges</li>
                                            <li>Faire respecter nos accords</li>
                                        </ul>
                                        <p>
                                            Vous pouvez demander la suppression de votre compte et de vos données à tout moment.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>7. Vos droits</h2>
                                        <p>
                                            Conformément aux lois applicables sur la protection des données, vous avez le droit de :
                                        </p>
                                        <ul>
                                            <li><strong>Accès :</strong> Demander une copie de vos données personnelles</li>
                                            <li><strong>Rectification :</strong> Corriger les données inexactes ou incomplètes</li>
                                            <li><strong>Suppression :</strong> Demander la suppression de vos données</li>
                                            <li><strong>Portabilité :</strong> Recevoir vos données dans un format portable</li>
                                            <li><strong>Opposition :</strong> Vous opposer au traitement de vos données</li>
                                            <li><strong>Limitation :</strong> Demander la limitation du traitement</li>
                                        </ul>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>8. Cookies et technologies similaires</h2>
                                        <p>
                                            Nous utilisons des cookies et technologies similaires pour :
                                        </p>
                                        <ul>
                                            <li>Maintenir votre session utilisateur</li>
                                            <li>Mémoriser vos préférences</li>
                                            <li>Analyser l'utilisation de la plateforme</li>
                                            <li>Améliorer la performance et la sécurité</li>
                                        </ul>
                                        <p>
                                            Vous pouvez contrôler l'utilisation des cookies via les paramètres de votre navigateur.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>9. Modifications de cette politique</h2>
                                        <p>
                                            Nous pouvons mettre à jour cette politique de confidentialité occasionnellement.
                                            Les changements importants vous seront notifiés par email ou via un avis sur la plateforme.
                                            La date de dernière mise à jour sera toujours indiquée en haut de cette page.
                                        </p>
                                    </section>

                                    <section className={styles.section}>
                                        <h2>10. Contact et réclamations</h2>
                                        <p>
                                            Pour toute question concernant cette politique de confidentialité ou pour exercer vos droits,
                                            contactez-nous :
                                        </p>
                                        <div className={styles.contactInfo}>
                                            <p><strong>Email :</strong> privacy@communaute-platform.ca</p>
                                            <p><strong>Responsable de la protection des données :</strong> dpo@communaute-platform.ca</p>
                                            <p><strong>Adresse :</strong> 123 Rue de la Municipalité, Sherbrooke, QC J1H 2R3</p>
                                        </div>
                                        <p>
                                            Si vous n'êtes pas satisfait de notre réponse, vous pouvez déposer une plainte auprès
                                            de la Commission d'accès à l'information du Québec.
                                        </p>
                                    </section>
                                </div>

                                {/* Footer */}
                                <div className={styles.footer}>
                                    <p>
                                        Cette politique est conforme aux lois québécoises et canadiennes sur la protection des données.
                                    </p>
                                    <div className={styles.actions}>
                                        <Link to="/signup" className={styles.primaryButton}>
                                            J'accepte et je m'inscris
                                        </Link>
                                        <Link to="/terms" className={styles.secondaryButton}>
                                            Conditions d'utilisation
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

export default PrivacyPage;