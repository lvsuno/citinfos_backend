import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Avatar,
    Grid,
    Chip,
    Divider,
    List,
    ListItem,
    ListItemText,
    Button,
    Paper,
    IconButton,
    Tooltip,
    Alert,
    CircularProgress
} from '@mui/material';
import {
    ArrowBack as ArrowBackIcon,
    Email as EmailIcon,
    Phone as PhoneIcon,
    LocationOn as LocationIcon,
    CalendarToday as CalendarIcon,
    Verified as VerifiedIcon,
    Block as BlockIcon,
    Edit as EditIcon,
    AdminPanelSettings as AdminIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';
import apiService from '../../services/apiService';
import AdminSidebar from '../../components/admin/AdminSidebar';
import SuspendUserModal from '../../components/admin/SuspendUserModal';

const UserProfile = () => {
    const { userId } = useParams();
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [suspendModalOpen, setSuspendModalOpen] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        fetchUserProfile();
    }, [userId]);

    const fetchUserProfile = async () => {
        try {
            setLoading(true);
            setError(null);

            // Récupérer les détails de l'utilisateur
            const userResponse = await apiService.getAdminUser(userId);
            setUser(userResponse.data);

            // Récupérer les statistiques de l'utilisateur
            try {
                const statsResponse = await apiService.getAdminUserDetailStats(userId);
                setStats(statsResponse.data);
            } catch (statsError) {
                console.warn('Erreur lors du chargement des statistiques:', statsError);
                setStats(null);
            }

        } catch (err) {
            console.error('Erreur lors du chargement du profil:', err);
            setError('Impossible de charger le profil de l\'utilisateur');
        } finally {
            setLoading(false);
        }
    };

    const handleAction = async (action, data = {}) => {
        try {
            setActionLoading(true);
            await apiService.performAdminUserAction(userId, action, data);
            // Recharger les données après l'action
            await fetchUserProfile();
        } catch (err) {
            console.error('Erreur lors de l\'action:', err);
            setError(`Erreur lors de l'action: ${err.message}`);
        } finally {
            setActionLoading(false);
        }
    };

    const handleSuspendUser = async (suspensionData) => {
        try {
            setActionLoading(true);
            await handleAction('suspend', suspensionData);
            setSuspendModalOpen(false);
        } catch (err) {
            console.error('Erreur lors de la suspension:', err);
        }
    };

    const getRoleColor = (role) => {
        switch (role) {
            case 'admin': return 'error';
            case 'moderator': return 'warning';
            case 'premium': return 'secondary';
            default: return 'default';
        }
    };

    const getRoleIcon = (role) => {
        switch (role) {
            case 'admin': return <AdminIcon fontSize="small" />;
            default: return null;
        }
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    if (error) {
        return (
            <Box p={3}>
                <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
                <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/admin/dashboard')}>
                    Retour au dashboard
                </Button>
            </Box>
        );
    }

    if (!user) {
        return (
            <Box p={3}>
                <Alert severity="warning">Utilisateur non trouvé</Alert>
            </Box>
        );
    }

    return (
        <Box display="flex" minHeight="100vh">
            <AdminSidebar
                activeSection="users"
                onSectionChange={() => { }} // Fonction vide car pas besoin de changer de section ici
                user={user}
            />
            <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
                {/* Header avec navigation */}
                <Box display="flex" alignItems="center" mb={3}>
                    <IconButton onClick={() => navigate('/admin/users')} sx={{ mr: 1 }}>
                        <ArrowBackIcon />
                    </IconButton>
                    <Typography variant="h4" component="h1">
                        Profil utilisateur
                    </Typography>
                </Box>

                <Grid container spacing={3}>
                    {/* Informations principales */}
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center', pb: 2 }}>
                                <Avatar
                                    src={user.profile_picture}
                                    sx={{
                                        width: 120,
                                        height: 120,
                                        mx: 'auto',
                                        mb: 2,
                                        fontSize: '3rem'
                                    }}
                                >
                                    {user.first_name?.[0]}{user.last_name?.[0]}
                                </Avatar>

                                <Typography variant="h5" gutterBottom>
                                    {user.full_name || `${user.first_name} ${user.last_name}`}
                                </Typography>

                                <Typography variant="body2" color="text.secondary" gutterBottom>
                                    @{user.username}
                                </Typography>

                                <Box display="flex" justifyContent="center" gap={1} mb={2}>
                                    <Chip
                                        icon={getRoleIcon(user.role)}
                                        label={user.role}
                                        color={getRoleColor(user.role)}
                                        size="small"
                                    />
                                    {user.is_verified && (
                                        <Chip
                                            icon={<VerifiedIcon />}
                                            label="Vérifié"
                                            color="success"
                                            size="small"
                                        />
                                    )}
                                    {user.is_suspended && (
                                        <Chip
                                            icon={<BlockIcon />}
                                            label="Suspendu"
                                            color="error"
                                            size="small"
                                        />
                                    )}
                                </Box>

                                {/* Actions rapides */}
                                <Box display="flex" justifyContent="center" gap={1}>
                                    <Tooltip title="Modifier le profil">
                                        <IconButton color="primary">
                                            <EditIcon />
                                        </IconButton>
                                    </Tooltip>

                                    {!user.is_verified && (
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            color="success"
                                            onClick={() => handleAction('verify')}
                                        >
                                            Vérifier
                                        </Button>
                                    )}

                                    {!user.is_suspended ? (
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            color="error"
                                            onClick={() => setSuspendModalOpen(true)}
                                            disabled={actionLoading}
                                        >
                                            Suspendre
                                        </Button>
                                    ) : (
                                        <Button
                                            size="small"
                                            variant="outlined"
                                            color="success"
                                            onClick={() => handleAction('unsuspend')}
                                            disabled={actionLoading}
                                        >
                                            Lever suspension
                                        </Button>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>

                        {/* Statistiques rapides */}
                        {stats && (
                            <Card sx={{ mt: 2 }}>
                                <CardContent>
                                    <Typography variant="h6" gutterBottom>
                                        Statistiques
                                    </Typography>
                                    <List dense>
                                        <ListItem>
                                            <ListItemText
                                                primary="Publications"
                                                secondary={stats.posts_count || 0}
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemText
                                                primary="Abonnés"
                                                secondary={stats.followers_count || 0}
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemText
                                                primary="Abonnements"
                                                secondary={stats.following_count || 0}
                                            />
                                        </ListItem>
                                        <ListItem>
                                            <ListItemText
                                                primary="Score d'engagement"
                                                secondary={`${stats.engagement_score || 0}/100`}
                                            />
                                        </ListItem>
                                    </List>
                                </CardContent>
                            </Card>
                        )}
                    </Grid>

                    {/* Détails du profil */}
                    <Grid item xs={12} md={8}>
                        <Card>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Informations détaillées
                                </Typography>

                                <Grid container spacing={2}>
                                    <Grid item xs={12} sm={6}>
                                        <Paper variant="outlined" sx={{ p: 2 }}>
                                            <Box display="flex" alignItems="center" mb={1}>
                                                <EmailIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                                <Typography variant="subtitle2">Email</Typography>
                                            </Box>
                                            <Typography variant="body2">{user.email}</Typography>
                                        </Paper>
                                    </Grid>

                                    {user.phone_number && (
                                        <Grid item xs={12} sm={6}>
                                            <Paper variant="outlined" sx={{ p: 2 }}>
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <PhoneIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                                    <Typography variant="subtitle2">Téléphone</Typography>
                                                </Box>
                                                <Typography variant="body2">{user.phone_number}</Typography>
                                            </Paper>
                                        </Grid>
                                    )}

                                    <Grid item xs={12} sm={6}>
                                        <Paper variant="outlined" sx={{ p: 2 }}>
                                            <Box display="flex" alignItems="center" mb={1}>
                                                <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                                <Typography variant="subtitle2">Membre depuis</Typography>
                                            </Box>
                                            <Typography variant="body2">
                                                {format(new Date(user.date_joined), 'dd MMMM yyyy', { locale: fr })}
                                            </Typography>
                                        </Paper>
                                    </Grid>

                                    {user.last_login && (
                                        <Grid item xs={12} sm={6}>
                                            <Paper variant="outlined" sx={{ p: 2 }}>
                                                <Box display="flex" alignItems="center" mb={1}>
                                                    <CalendarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                                                    <Typography variant="subtitle2">Dernière connexion</Typography>
                                                </Box>
                                                <Typography variant="body2">
                                                    {format(new Date(user.last_login), 'dd MMMM yyyy à HH:mm', { locale: fr })}
                                                </Typography>
                                            </Paper>
                                        </Grid>
                                    )}
                                </Grid>

                                {/* Biographie */}
                                {user.bio && (
                                    <>
                                        <Divider sx={{ my: 3 }} />
                                        <Typography variant="h6" gutterBottom>
                                            Biographie
                                        </Typography>
                                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                            {user.bio}
                                        </Typography>
                                    </>
                                )}

                                {/* Informations système */}
                                <Divider sx={{ my: 3 }} />
                                <Typography variant="h6" gutterBottom>
                                    Informations système
                                </Typography>

                                <Grid container spacing={2}>
                                    <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            ID utilisateur
                                        </Typography>
                                        <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
                                            {user.id}
                                        </Typography>
                                    </Grid>

                                    <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Statut du compte
                                        </Typography>
                                        <Typography variant="body2">
                                            {user.is_active ? 'Actif' : 'Inactif'}
                                        </Typography>
                                    </Grid>

                                    <Grid item xs={12} sm={6}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Dernière activité
                                        </Typography>
                                        <Typography variant="body2">
                                            {user.last_active
                                                ? format(new Date(user.last_active), 'dd MMMM yyyy à HH:mm', { locale: fr })
                                                : 'Jamais'
                                            }
                                        </Typography>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>
            </Box>

            {/* Modal de suspension */}
            <SuspendUserModal
                open={suspendModalOpen}
                onClose={() => setSuspendModalOpen(false)}
                onConfirm={handleSuspendUser}
                user={user}
                loading={actionLoading}
            />
        </Box>
    );
};

export default UserProfile;