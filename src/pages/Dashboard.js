import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import VerifyAccount from '../components/VerifyAccount';
import styles from './Dashboard.module.css';

const Dashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, loading } = useAuth();
    const [activeRubrique, setActiveRubrique] = useState('Accueil');
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [verificationMessage, setVerificationMessage] = useState('');

    // No redirect for unauthenticated users - allow read-only access

    // Handle verification modal display from login navigation
    useEffect(() => {
        if (location.state?.showVerificationModal) {
            setShowVerificationModal(true);
            setVerificationMessage(location.state.verificationMessage || '');

            // Clear the state to prevent modal showing on refresh
            navigate(location.pathname, { replace: true, state: {} });
        }
    }, [location.state, navigate, location.pathname]);

    const handleRubriqueChange = (rubrique) => {
        setActiveRubrique(rubrique);
        console.log('Rubrique sélectionnée:', rubrique);
    };

    // Afficher un spinner pendant le chargement de l'authentification
    if (loading) {
        return (
            <Layout>
                <div className={styles.loadingContainer}>
                    <div className={styles.spinner}>Chargement...</div>
                </div>
            </Layout>
        );
    }

    // Allow access even without user authentication (read-only mode)

    const handleVerificationSuccess = () => {
        setShowVerificationModal(false);
        // Optionally refresh user data or show success message
    };

    const handleVerificationClose = () => {
        setShowVerificationModal(false);
    };

    return (
        <Layout
            activeRubrique={activeRubrique}
            onRubriqueChange={handleRubriqueChange}
            subtitle="Votre tableau de bord communautaire est en cours de développement. Utilisez le sidebar pour naviguer entre les différentes rubriques de Sherbrooke."
        >
            {/* Contenu principal du dashboard */}
            <div className={styles.emptyState}>
                <div className={styles.emptyIcon}>🚧</div>
                <p>
                    Rubrique active : <strong>{activeRubrique}</strong>
                </p>
                <p>Le contenu de cette section sera ajouté prochainement.</p>
            </div>

            {/* Verification Modal - shows after login if verification required */}
            {showVerificationModal && user && (
                <VerifyAccount
                    show={showVerificationModal}
                    onHide={handleVerificationClose}
                    onSuccess={handleVerificationSuccess}
                    userEmail={user.email}
                    message={verificationMessage}
                />
            )}
        </Layout>
    );
};

export default Dashboard;