import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { getDefaultDivisionUrl } from '../utils/defaultDivisionRedirect';
import Layout from '../components/Layout';
import VerifyAccount from '../components/VerifyAccount';
import styles from './Dashboard.module.css';

const Dashboard = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, loading, anonymousLocation } = useAuth();
    const [activeRubrique, setActiveRubrique] = useState('Accueil');
    const [showVerificationModal, setShowVerificationModal] = useState(false);
    const [verificationMessage, setVerificationMessage] = useState('');
    const [redirecting, setRedirecting] = useState(true);

    // Redirect to division page - Dashboard should NOT exist as a standalone page
    useEffect(() => {
        const redirectToDivision = async () => {
            if (loading) return; // Wait for auth to load

            console.log('🔄 Dashboard: Redirecting to division page...');

            try {
                const divisionUrl = await getDefaultDivisionUrl(user, anonymousLocation);
                console.log('✅ Redirecting to:', divisionUrl);

                // Preserve verification modal state if present
                if (location.state?.showVerificationModal) {
                    navigate(divisionUrl, {
                        replace: true,
                        state: {
                            showVerificationModal: true,
                            verificationMessage: location.state.verificationMessage || ''
                        }
                    });
                } else {
                    navigate(divisionUrl, { replace: true });
                }
            } catch (error) {
                console.error('❌ Error getting division URL:', error);
                // Fallback to Sherbrooke if error
                navigate('/municipality/sherbrooke/accueil', { replace: true });
            }
        };

        redirectToDivision();
    }, [user, loading, anonymousLocation, navigate, location.state]);

    const handleRubriqueChange = (rubrique) => {
        setActiveRubrique(rubrique);
        console.log('Rubrique sélectionnée:', rubrique);
    };

    // Show loading spinner while redirecting
    if (loading || redirecting) {
        return (
            <Layout>
                <div className={styles.loadingContainer}>
                    <div className={styles.spinner}>Redirection vers votre division...</div>
                </div>
            </Layout>
        );
    }

    // This should never be reached since we always redirect
    return null;
};

export default Dashboard;