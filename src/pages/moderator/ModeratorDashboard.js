import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Alert, Grid, Card, CardContent, Chip, IconButton } from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import ModeratorLayout from '../../components/moderator/ModeratorLayout';
import {
    Assignment as TaskIcon,
    Flag as FlagIcon,
    Visibility as ReviewIcon,
    CheckCircle as ApprovedIcon,
    Cancel as RejectedIcon,
    Schedule as PendingIcon,
    TrendingUp as TrendingIcon,
    NavigateNext as NextIcon
} from '@mui/icons-material';

const ModeratorDashboard = () => {
    const { user, isRole } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);

    // Données statiques pour les statistiques
    const [stats] = useState({
        pending_items: 12,
        reported_content: 5,
        approved_today: 8,
        rejected_today: 3,
        total_moderated: 156,
        accuracy_rate: 94.5
    });

    // Données statiques pour les tâches récentes
    const [recentTasks] = useState([
        {
            id: 1,
            type: 'post',
            title: 'Publication suspecte sur les événements locaux',
            author: 'user123',
            priority: 'high',
            created_at: '2024-10-10T10:30:00Z',
            status: 'pending'
        },
        {
            id: 2,
            type: 'comment',
            title: 'Commentaire signalé pour langage inapproprié',
            author: 'john_doe',
            priority: 'medium',
            created_at: '2024-10-10T09:15:00Z',
            status: 'pending'
        },
        {
            id: 3,
            type: 'post',
            title: 'Contenu potentiellement spam',
            author: 'spammer_user',
            priority: 'urgent',
            created_at: '2024-10-10T08:45:00Z',
            status: 'pending'
        },
        {
            id: 4,
            type: 'comment',
            title: 'Commentaire avec liens suspects',
            author: 'suspicious_account',
            priority: 'high',
            created_at: '2024-10-10T07:20:00Z',
            status: 'pending'
        },
        {
            id: 5,
            type: 'post',
            title: 'Publication avec contenu dupliqué',
            author: 'repeat_poster',
            priority: 'low',
            created_at: '2024-10-09T18:30:00Z',
            status: 'pending'
        }
    ]);

    useEffect(() => {
        // Vérifier si l'utilisateur est un modérateur
        if (!user) {
            navigate('/login');
            return;
        }

        if (!isRole('moderator')) {
            navigate('/dashboard');
            return;
        }

        setLoading(false);
    }, [user, isRole, navigate]);

    const getPriorityColor = (priority) => {
        const colors = {
            'urgent': 'error',
            'high': 'warning',
            'medium': 'info',
            'low': 'default'
        };
        return colors[priority] || 'default';
    };

    const getPriorityLabel = (priority) => {
        const labels = {
            'urgent': 'Urgent',
            'high': 'Élevée',
            'medium': 'Moyenne',
            'low': 'Faible'
        };
        return labels[priority] || priority;
    };

    const getTypeIcon = (type) => {
        return type === 'post' ? '📝' : '💬';
    };

    const formatTimeAgo = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInHours = Math.floor((now - date) / (1000 * 60 * 60));
        
        if (diffInHours < 1) return 'Il y a quelques minutes';
        if (diffInHours === 1) return 'Il y a 1 heure';
        if (diffInHours < 24) return `Il y a ${diffInHours} heures`;
        
        const diffInDays = Math.floor(diffInHours / 24);
        if (diffInDays === 1) return 'Il y a 1 jour';
        return `Il y a ${diffInDays} jours`;
    };

    if (loading) {
        return (
            <ModeratorLayout activeSection="overview">
                <Box sx={{ p: 3 }}>
                    <Typography variant="h6">Chargement du dashboard modérateur...</Typography>
                </Box>
            </ModeratorLayout>
        );
    }

    if (!user || !isRole('moderator')) {
        return (
            <ModeratorLayout activeSection="overview">
                <Container maxWidth="md" sx={{ p: 3 }}>
                    <Alert severity="error">
                        Accès refusé. Vous devez être modérateur pour accéder à cette page.
                    </Alert>
                </Container>
            </ModeratorLayout>
        );
    }

    return (
        <ModeratorLayout activeSection="overview">
            <Container maxWidth="xl" sx={{ p: 3 }}>
                {/* Header */}
                <Box mb={3}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Dashboard Modérateur
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Bienvenue, {user.username}. Voici un aperçu de vos tâches de modération.
                    </Typography>
                </Box>

                {/* Statistics Cards */}
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <PendingIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.pending_items}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    En attente de modération
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <FlagIcon color="error" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.reported_content}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Contenu signalé
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={4}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <TrendingIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.accuracy_rate}%</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Taux de précision
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Statistics Today */}
                <Grid container spacing={3} mb={4}>
                    <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                <ApprovedIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
                                <Typography variant="h5">{stats.approved_today}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Approuvés aujourd'hui
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                <RejectedIcon color="error" sx={{ fontSize: 32, mb: 1 }} />
                                <Typography variant="h5">{stats.rejected_today}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Rejetés aujourd'hui
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                <TaskIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
                                <Typography variant="h5">{stats.total_moderated}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Total modéré
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card variant="outlined">
                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                <ReviewIcon color="info" sx={{ fontSize: 32, mb: 1 }} />
                                <Typography variant="h5">{stats.pending_items + stats.reported_content}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Nécessitent attention
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Recent Tasks */}
                <Paper sx={{ p: 3 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
                        <Typography variant="h6">
                            Tâches récentes nécessitant une modération
                        </Typography>
                        <IconButton 
                            onClick={() => navigate('/moderator/feed')}
                            color="primary"
                        >
                            <NextIcon />
                        </IconButton>
                    </Box>
                    
                    <Grid container spacing={2}>
                        {recentTasks.map((task) => (
                            <Grid item xs={12} key={task.id}>
                                <Paper 
                                    variant="outlined" 
                                    sx={{ 
                                        p: 2, 
                                        display: 'flex', 
                                        alignItems: 'center', 
                                        gap: 2,
                                        cursor: 'pointer',
                                        '&:hover': {
                                            backgroundColor: 'action.hover'
                                        }
                                    }}
                                    onClick={() => navigate('/moderator/feed')}
                                >
                                    <Box sx={{ fontSize: '1.5rem' }}>
                                        {getTypeIcon(task.type)}
                                    </Box>
                                    
                                    <Box sx={{ flexGrow: 1 }}>
                                        <Typography variant="subtitle1" gutterBottom>
                                            {task.title}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            Par @{task.author} • {formatTimeAgo(task.created_at)}
                                        </Typography>
                                    </Box>
                                    
                                    <Chip
                                        label={getPriorityLabel(task.priority)}
                                        color={getPriorityColor(task.priority)}
                                        size="small"
                                        variant="outlined"
                                    />
                                    
                                    <Chip
                                        label={task.type === 'post' ? 'Publication' : 'Commentaire'}
                                        size="small"
                                        variant="filled"
                                        sx={{ backgroundColor: 'primary.light', color: 'white' }}
                                    />
                                </Paper>
                            </Grid>
                        ))}
                    </Grid>
                </Paper>
            </Container>
        </ModeratorLayout>
    );
};

export default ModeratorDashboard;