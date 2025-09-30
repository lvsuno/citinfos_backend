import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Layout from '../components/Layout';
import styles from './Dashboard.module.css';

const Dashboard = () => {
    const navigate = useNavigate();
    const { user } = useAuth();
    const [activeRubrique, setActiveRubrique] = useState('Art');

    // Si pas d'utilisateur connecté, rediriger vers la page de connexion
    useEffect(() => {
        if (!user) {
            navigate('/login');
        }
    }, [user, navigate]);

    const handleRubriqueChange = (rubrique) => {
        setActiveRubrique(rubrique);
        console.log('Rubrique sélectionnée:', rubrique);
    };

    if (!user) {
        return null; // Évite le flash pendant la redirection
    }

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
        </Layout>
    );
};

export default Dashboard;