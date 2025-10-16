import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Paper,
    Typography,
    Avatar,
    Grid,
    Card,
    CardContent,
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    Chip,
    Divider,
    LinearProgress,
    Tab,
    Tabs,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    Person as PersonIcon,
    Email as EmailIcon,
    CalendarToday as CalendarIcon,
    Security as SecurityIcon,
    TrendingUp as TrendingUpIcon,
    Assignment as TaskIcon,
    CheckCircle as CheckCircleIcon,
    Warning as WarningIcon,
    Info as InfoIcon,
    Visibility as ViewIcon
} from '@mui/icons-material';
import AdminLayout from '../../components/admin/AdminLayout';
import { useAuth } from '../../contexts/AuthContext';
import styles from './AdminProfile.module.css';

const AdminProfile = () => {
    const { user } = useAuth();
    const [currentTab, setCurrentTab] = useState(0);
    const [profileStats, setProfileStats] = useState({
        totalActions: 156,
        usersManaged: 45,
        municipalitiesManaged: 12,
        supportTicketsResolved: 23,
        completionRate: 92.5
    });

    const [recentActivities, setRecentActivities] = useState([
        {
            id: 1,
            action: 'Création utilisateur',
            description: 'Nouvel utilisateur créé: marie.dupont@email.com',
            timestamp: '2024-01-15 14:30',
            type: 'user',
            icon: <PersonIcon />,
            status: 'completed'
        },
        {
            id: 2,
            action: 'Modération municipalité',
            description: 'Validation de la municipalité de Saint-Jean',
            timestamp: '2024-01-15 13:15',
            type: 'municipality',
            icon: <CheckCircleIcon />,
            status: 'completed'
        },
        {
            id: 3,
            action: 'Support résolu',
            description: 'Ticket #456 - Problème de connexion résolu',
            timestamp: '2024-01-15 11:45',
            type: 'support',
            icon: <TaskIcon />,
            status: 'completed'
        },
        {
            id: 4,
            action: 'Mise à jour sécurité',
            description: 'Révision des permissions utilisateur',
            timestamp: '2024-01-15 10:20',
            type: 'security',
            icon: <SecurityIcon />,
            status: 'in-progress'
        },
        {
            id: 5,
            action: 'Analyse statistiques',
            description: 'Génération du rapport mensuel',
            timestamp: '2024-01-15 09:00',
            type: 'analytics',
            icon: <TrendingUpIcon />,
            status: 'completed'
        }
    ]);

    const handleTabChange = (event, newValue) => {
        setCurrentTab(newValue);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return '#22c55e';
            case 'in-progress':
                return '#f59e0b';
            case 'pending':
                return '#3b82f6';
            default:
                return '#6b7280';
        }
    };

    const getStatusLabel = (status) => {
        switch (status) {
            case 'completed':
                return 'Terminé';
            case 'in-progress':
                return 'En cours';
            case 'pending':
                return 'En attente';
            default:
                return 'Inconnu';
        }
    };

    const StatCard = ({ title, value, subtitle, icon, color = '#06b6d4' }) => (
        <Card sx={{ height: '100%', background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)' }}>
            <CardContent>
                <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box sx={{ color: color }}>
                        {icon}
                    </Box>
                    <Typography variant="h4" fontWeight="bold" color={color}>
                        {value}
                    </Typography>
                </Box>
                <Typography variant="h6" gutterBottom>
                    {title}
                </Typography>
                {subtitle && (
                    <Typography variant="body2" color="text.secondary">
                        {subtitle}
                    </Typography>
                )}
            </CardContent>
        </Card>
    );

    return (
        <AdminLayout activeSection="profile">
            <Container maxWidth="xl" sx={{ py: 4 }}>
                {/* Header avec info profil */}
                <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)', color: 'white' }}>
                    <Box display="flex" alignItems="center" gap={3}>
                        <Avatar
                            src={user?.profile_picture}
                            sx={{ 
                                width: 80, 
                                height: 80, 
                                border: '3px solid rgba(255, 255, 255, 0.2)' 
                            }}
                        >
                            {user?.username?.charAt(0).toUpperCase()}
                        </Avatar>
                        <Box flex={1}>
                            <Typography variant="h4" fontWeight="bold" gutterBottom>
                                {user?.first_name} {user?.last_name}
                            </Typography>
                            <Box display="flex" alignItems="center" gap={2} mb={1}>
                                <Chip
                                    label="Administrateur"
                                    sx={{
                                        background: 'linear-gradient(45deg, #06b6d4, #0891b2)',
                                        color: 'white',
                                        fontWeight: 600
                                    }}
                                />
                                <Box display="flex" alignItems="center" gap={1}>
                                    <EmailIcon sx={{ fontSize: 16 }} />
                                    <Typography variant="body2">
                                        {user?.email}
                                    </Typography>
                                </Box>
                            </Box>
                            <Box display="flex" alignItems="center" gap={1}>
                                <CalendarIcon sx={{ fontSize: 16 }} />
                                <Typography variant="body2">
                                    Membre depuis: {new Date(user?.date_joined).toLocaleDateString('fr-FR')}
                                </Typography>
                            </Box>
                        </Box>
                    </Box>
                </Paper>

                {/* Statistiques */}
                <Grid container spacing={3} mb={3}>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Total Actions"
                            value={profileStats.totalActions}
                            subtitle="Actions administratives"
                            icon={<TaskIcon />}
                            color="#06b6d4"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Utilisateurs"
                            value={profileStats.usersManaged}
                            subtitle="Utilisateurs gérés"
                            icon={<PersonIcon />}
                            color="#10b981"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Municipalités"
                            value={profileStats.municipalitiesManaged}
                            subtitle="Municipalités validées"
                            icon={<CheckCircleIcon />}
                            color="#f59e0b"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Support"
                            value={profileStats.supportTicketsResolved}
                            subtitle="Tickets résolus"
                            icon={<TaskIcon />}
                            color="#8b5cf6"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Efficacité"
                            value={`${profileStats.completionRate}%`}
                            subtitle="Taux de réussite"
                            icon={<TrendingUpIcon />}
                            color="#ef4444"
                        />
                    </Grid>
                </Grid>

                {/* Tabs pour différentes vues */}
                <Paper sx={{ mb: 3 }}>
                    <Tabs 
                        value={currentTab} 
                        onChange={handleTabChange}
                        sx={{
                            borderBottom: 1,
                            borderColor: 'divider',
                            '& .MuiTab-root': {
                                textTransform: 'none',
                                fontWeight: 600
                            }
                        }}
                    >
                        <Tab label="Activité Récente" />
                        <Tab label="Statistiques Détaillées" />
                        <Tab label="Permissions" />
                    </Tabs>
                </Paper>

                {/* Contenu des tabs */}
                {currentTab === 0 && (
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Activité Récente
                        </Typography>
                        <List>
                            {recentActivities.map((activity, index) => (
                                <React.Fragment key={activity.id}>
                                    <ListItem
                                        sx={{
                                            border: '1px solid #e2e8f0',
                                            borderRadius: 2,
                                            mb: 1,
                                            background: '#f8fafc'
                                        }}
                                    >
                                        <ListItemIcon sx={{ color: getStatusColor(activity.status) }}>
                                            {activity.icon}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={
                                                <Box display="flex" alignItems="center" gap={2}>
                                                    <Typography variant="subtitle1" fontWeight="bold">
                                                        {activity.action}
                                                    </Typography>
                                                    <Chip
                                                        label={getStatusLabel(activity.status)}
                                                        size="small"
                                                        sx={{
                                                            backgroundColor: getStatusColor(activity.status),
                                                            color: 'white',
                                                            fontSize: '0.7rem'
                                                        }}
                                                    />
                                                </Box>
                                            }
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {activity.description}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {activity.timestamp}
                                                    </Typography>
                                                </Box>
                                            }
                                        />
                                        <Tooltip title="Voir détails">
                                            <IconButton>
                                                <ViewIcon />
                                            </IconButton>
                                        </Tooltip>
                                    </ListItem>
                                </React.Fragment>
                            ))}
                        </List>
                    </Paper>
                )}

                {currentTab === 1 && (
                    <Grid container spacing={3}>
                        <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="h6" gutterBottom>
                                    Performance Mensuelle
                                </Typography>
                                <Box mb={2}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Actions réalisées ce mois
                                    </Typography>
                                    <LinearProgress 
                                        variant="determinate" 
                                        value={75} 
                                        sx={{ height: 8, borderRadius: 4 }}
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                        75% de l'objectif atteint
                                    </Typography>
                                </Box>
                                <Box mb={2}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Tickets de support traités
                                    </Typography>
                                    <LinearProgress 
                                        variant="determinate" 
                                        value={92} 
                                        sx={{ height: 8, borderRadius: 4 }}
                                        color="success"
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                        92% de réussite
                                    </Typography>
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="h6" gutterBottom>
                                    Répartition des Tâches
                                </Typography>
                                <List dense>
                                    <ListItem>
                                        <ListItemText primary="Gestion des utilisateurs" secondary="45%" />
                                        <Typography variant="body2" color="primary">
                                            45%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Support technique" secondary="30%" />
                                        <Typography variant="body2" color="secondary">
                                            30%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Modération contenu" secondary="15%" />
                                        <Typography variant="body2" color="warning.main">
                                            15%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Maintenance système" secondary="10%" />
                                        <Typography variant="body2" color="error.main">
                                            10%
                                        </Typography>
                                    </ListItem>
                                </List>
                            </Paper>
                        </Grid>
                    </Grid>
                )}

                {currentTab === 2 && (
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Permissions et Accès
                        </Typography>
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Module</TableCell>
                                        <TableCell>Niveau d'accès</TableCell>
                                        <TableCell>Permissions</TableCell>
                                        <TableCell>Statut</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    <TableRow>
                                        <TableCell>Gestion Utilisateurs</TableCell>
                                        <TableCell>Administrateur</TableCell>
                                        <TableCell>Lecture, Écriture, Suppression</TableCell>
                                        <TableCell>
                                            <Chip label="Actif" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Municipalités</TableCell>
                                        <TableCell>Administrateur</TableCell>
                                        <TableCell>Lecture, Écriture, Validation</TableCell>
                                        <TableCell>
                                            <Chip label="Actif" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Support</TableCell>
                                        <TableCell>Administrateur</TableCell>
                                        <TableCell>Lecture, Écriture, Résolution</TableCell>
                                        <TableCell>
                                            <Chip label="Actif" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Système</TableCell>
                                        <TableCell>Super Admin</TableCell>
                                        <TableCell>Tous droits</TableCell>
                                        <TableCell>
                                            <Chip label="Actif" color="primary" size="small" />
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                )}
            </Container>
        </AdminLayout>
    );
};

export default AdminProfile;