import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Alert } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import AdminLayout from '../../components/admin/AdminLayout';
import UserManagement from './UserManagement';
import styles from './AdminDashboard.module.css';

const AdminDashboard = () => {
    const { user, isRole } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Vérifier si l'utilisateur est un admin
        if (!user) {
            navigate('/login');
            return;
        }

        if (!isRole('admin')) {
            navigate('/dashboard');
            return;
        }

        setLoading(false);
    }, [user, isRole, navigate]);

    if (loading) {
        return (
            <Box className={styles.loadingContainer}>
                <Typography variant="h6">Chargement du dashboard administrateur...</Typography>
            </Box>
        );
    }

    if (!user || !isRole('admin')) {
        return (
            <Container maxWidth="md" className={styles.errorContainer}>
                <Alert severity="error">
                    Accès refusé. Vous devez être administrateur pour accéder à cette page.
                </Alert>
            </Container>
        );
    }

    const renderContent = () => {
        return (
            <Paper sx={{ p: 3 }}>
                <Typography variant="h4" gutterBottom>
                    Tableau de bord administrateur
                </Typography>
                <Typography variant="body1" color="text.secondary" paragraph>
                    Bienvenue, {user.username}. Utilisez le menu latéral pour naviguer entre les différentes sections administratives.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                    Fonctionnalités disponibles :
                </Typography>
                <Box component="ul" sx={{ mt: 2 }}>
                    <li>Gestion des utilisateurs</li>
                    <li>Gestion des municipalités</li>
                    <li>Support utilisateurs</li>
                    <li>Analytiques du système (à venir)</li>
                    <li>Modération de contenu (à venir)</li>
                    <li>Configuration système (à venir)</li>
                </Box>
            </Paper>
        );
    };

    return (
        <AdminLayout activeSection="overview">
            <Container maxWidth="xl" sx={{ p: 3 }}>
                {renderContent()}
            </Container>
        </AdminLayout>
    );
};

export default AdminDashboard;