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
    Gavel as ModerationIcon,
    TrendingUp as TrendingUpIcon,
    Assignment as TaskIcon,
    CheckCircle as CheckCircleIcon,
    Warning as WarningIcon,
    Block as BlockIcon,
    Visibility as ViewIcon,
    Flag as FlagIcon,
    ThumbUp as ApproveIcon,
    ThumbDown as RejectIcon
} from '@mui/icons-material';
import ModeratorLayout from '../../components/moderator/ModeratorLayout';
import { useAuth } from '../../contexts/AuthContext';
import styles from './ModeratorProfile.module.css';

const ModeratorProfile = () => {
    const { user } = useAuth();
    const [currentTab, setCurrentTab] = useState(0);
    const [profileStats, setProfileStats] = useState({
        totalModerations: 89,
        contentApproved: 67,
        contentRejected: 22,
        reportsHandled: 34,
        accuracyRate: 94.7
    });

    const [recentModerations, setRecentModerations] = useState([
        {
            id: 1,
            action: 'Contenu approuvé',
            description: 'Post de @jean_martin - Avis restaurant Le Coin Gourmand',
            timestamp: '2024-01-15 16:20',
            type: 'approve',
            icon: <ApproveIcon />,
            status: 'completed'
        },
        {
            id: 2,
            action: 'Contenu rejeté',
            description: 'Commentaire de @user123 - Langage inapproprié',
            timestamp: '2024-01-15 15:45',
            type: 'reject',
            icon: <RejectIcon />,
            status: 'completed'
        },
        {
            id: 3,
            action: 'Signalement traité',
            description: 'Signalement #789 - Spam détecté et supprimé',
            timestamp: '2024-01-15 14:30',
            type: 'report',
            icon: <FlagIcon />,
            status: 'completed'
        },
        {
            id: 4,
            action: 'En cours de révision',
            description: 'Post signalé par 3 utilisateurs - En analyse',
            timestamp: '2024-01-15 13:15',
            type: 'review',
            icon: <WarningIcon />,
            status: 'in-progress'
        },
        {
            id: 5,
            action: 'Utilisateur modéré',
            description: 'Avertissement envoyé à @problematic_user',
            timestamp: '2024-01-15 12:00',
            type: 'user-action',
            icon: <BlockIcon />,
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

    const getTypeColor = (type) => {
        switch (type) {
            case 'approve':
                return '#22c55e';
            case 'reject':
                return '#ef4444';
            case 'report':
                return '#f59e0b';
            case 'review':
                return '#3b82f6';
            case 'user-action':
                return '#8b5cf6';
            default:
                return '#6b7280';
        }
    };

    const StatCard = ({ title, value, subtitle, icon, color = '#7c3aed' }) => (
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
        <ModeratorLayout activeSection="profile">
            <Container maxWidth="xl" sx={{ py: 4 }}>
                {/* Header avec info profil */}
                <Paper sx={{ p: 3, mb: 3, background: 'linear-gradient(135deg, #2d1b69 0%, #1e1b4b 100%)', color: 'white' }}>
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
                                    label="Modérateur"
                                    sx={{
                                        background: 'linear-gradient(45deg, #7c3aed, #6366f1)',
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
                                    Modérateur depuis: {new Date(user?.date_joined).toLocaleDateString('fr-FR')}
                                </Typography>
                            </Box>
                        </Box>
                    </Box>
                </Paper>

                {/* Statistiques */}
                <Grid container spacing={3} mb={3}>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Total Modérations"
                            value={profileStats.totalModerations}
                            subtitle="Actions de modération"
                            icon={<ModerationIcon />}
                            color="#7c3aed"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Approuvé"
                            value={profileStats.contentApproved}
                            subtitle="Contenu validé"
                            icon={<CheckCircleIcon />}
                            color="#10b981"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Rejeté"
                            value={profileStats.contentRejected}
                            subtitle="Contenu refusé"
                            icon={<BlockIcon />}
                            color="#ef4444"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Signalements"
                            value={profileStats.reportsHandled}
                            subtitle="Rapports traités"
                            icon={<FlagIcon />}
                            color="#f59e0b"
                        />
                    </Grid>
                    <Grid item xs={12} sm={6} md={2.4}>
                        <StatCard
                            title="Précision"
                            value={`${profileStats.accuracyRate}%`}
                            subtitle="Taux de précision"
                            icon={<TrendingUpIcon />}
                            color="#06b6d4"
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
                        <Tab label="Modérations Récentes" />
                        <Tab label="Statistiques Détaillées" />
                        <Tab label="Spécialisations" />
                    </Tabs>
                </Paper>

                {/* Contenu des tabs */}
                {currentTab === 0 && (
                    <Paper sx={{ p: 3 }}>
                        <Typography variant="h6" gutterBottom>
                            Modérations Récentes
                        </Typography>
                        <List>
                            {recentModerations.map((moderation, index) => (
                                <React.Fragment key={moderation.id}>
                                    <ListItem
                                        sx={{
                                            border: '1px solid #e2e8f0',
                                            borderRadius: 2,
                                            mb: 1,
                                            background: '#f8fafc'
                                        }}
                                    >
                                        <ListItemIcon sx={{ color: getTypeColor(moderation.type) }}>
                                            {moderation.icon}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={
                                                <Box display="flex" alignItems="center" gap={2}>
                                                    <Typography variant="subtitle1" fontWeight="bold">
                                                        {moderation.action}
                                                    </Typography>
                                                    <Chip
                                                        label={getStatusLabel(moderation.status)}
                                                        size="small"
                                                        sx={{
                                                            backgroundColor: getStatusColor(moderation.status),
                                                            color: 'white',
                                                            fontSize: '0.7rem'
                                                        }}
                                                    />
                                                </Box>
                                            }
                                            secondary={
                                                <Box>
                                                    <Typography variant="body2" color="text.secondary">
                                                        {moderation.description}
                                                    </Typography>
                                                    <Typography variant="caption" color="text.secondary">
                                                        {moderation.timestamp}
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
                                    Performance de Modération
                                </Typography>
                                <Box mb={2}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Taux d'approbation
                                    </Typography>
                                    <LinearProgress 
                                        variant="determinate" 
                                        value={75} 
                                        sx={{ height: 8, borderRadius: 4 }}
                                        color="success"
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                        75% du contenu approuvé
                                    </Typography>
                                </Box>
                                <Box mb={2}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Rapidité de traitement
                                    </Typography>
                                    <LinearProgress 
                                        variant="determinate" 
                                        value={88} 
                                        sx={{ height: 8, borderRadius: 4 }}
                                        color="primary"
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                        88% traité en moins de 2h
                                    </Typography>
                                </Box>
                                <Box mb={2}>
                                    <Typography variant="body2" color="text.secondary" gutterBottom>
                                        Précision des décisions
                                    </Typography>
                                    <LinearProgress 
                                        variant="determinate" 
                                        value={95} 
                                        sx={{ height: 8, borderRadius: 4 }}
                                        color="success"
                                    />
                                    <Typography variant="caption" color="text.secondary">
                                        95% de précision
                                    </Typography>
                                </Box>
                            </Paper>
                        </Grid>
                        <Grid item xs={12} md={6}>
                            <Paper sx={{ p: 3 }}>
                                <Typography variant="h6" gutterBottom>
                                    Types de Contenu Modéré
                                </Typography>
                                <List dense>
                                    <ListItem>
                                        <ListItemText primary="Avis et commentaires" secondary="60%" />
                                        <Typography variant="body2" color="primary">
                                            60%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Publications d'événements" secondary="25%" />
                                        <Typography variant="body2" color="secondary">
                                            25%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Signalements d'utilisateurs" secondary="10%" />
                                        <Typography variant="body2" color="warning.main">
                                            10%
                                        </Typography>
                                    </ListItem>
                                    <ListItem>
                                        <ListItemText primary="Contenu multimédia" secondary="5%" />
                                        <Typography variant="body2" color="error.main">
                                            5%
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
                            Spécialisations et Formations
                        </Typography>
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>Spécialisation</TableCell>
                                        <TableCell>Niveau</TableCell>
                                        <TableCell>Formation</TableCell>
                                        <TableCell>Statut</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    <TableRow>
                                        <TableCell>Modération de contenu</TableCell>
                                        <TableCell>Expert</TableCell>
                                        <TableCell>Formation complète - 40h</TableCell>
                                        <TableCell>
                                            <Chip label="Certifié" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Gestion des signalements</TableCell>
                                        <TableCell>Avancé</TableCell>
                                        <TableCell>Formation spécialisée - 20h</TableCell>
                                        <TableCell>
                                            <Chip label="Certifié" color="success" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Médiation utilisateurs</TableCell>
                                        <TableCell>Intermédiaire</TableCell>
                                        <TableCell>Formation en cours - 15h</TableCell>
                                        <TableCell>
                                            <Chip label="En cours" color="warning" size="small" />
                                        </TableCell>
                                    </TableRow>
                                    <TableRow>
                                        <TableCell>Analyse de sentiment</TableCell>
                                        <TableCell>Débutant</TableCell>
                                        <TableCell>À programmer</TableCell>
                                        <TableCell>
                                            <Chip label="Planifié" color="primary" size="small" />
                                        </TableCell>
                                    </TableRow>
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </Paper>
                )}
            </Container>
        </ModeratorLayout>
    );
};

export default ModeratorProfile;