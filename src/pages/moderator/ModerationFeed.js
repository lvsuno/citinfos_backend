import React, { useState } from 'react';
import {
    Box,
    Container,
    Typography,
    Paper,
    Card,
    CardContent,
    Button,
    Chip,
    Avatar,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    TextField,
    Grid,
    Divider,
    IconButton,
    Tooltip
} from '@mui/material';
import {
    CheckCircle as ApproveIcon,
    Cancel as RejectIcon,
    Visibility as ViewIcon,
    Flag as FlagIcon,
    Comment as CommentIcon,
    Article as PostIcon,
    Person as PersonIcon,
    Schedule as TimeIcon,
    Warning as WarningIcon
} from '@mui/icons-material';
import ModeratorLayout from '../../components/moderator/ModeratorLayout';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const ModerationFeed = () => {
    const [filter, setFilter] = useState('all');
    const [selectedItem, setSelectedItem] = useState(null);
    const [viewDialogOpen, setViewDialogOpen] = useState(false);
    const [actionDialogOpen, setActionDialogOpen] = useState(false);
    const [actionType, setActionType] = useState('');
    const [actionReason, setActionReason] = useState('');

    // Données statiques pour le fil de modération
    const [moderationItems] = useState([
        {
            id: 1,
            type: 'post',
            title: 'Événement culturel ce weekend au centre-ville',
            content: 'Salut tout le monde ! Il y aura un super événement culturel ce weekend au centre-ville. Venez nombreux ! 🎭🎨 Plus d\'infos sur mon site web perso.',
            author: {
                username: 'culture_lover',
                avatar: null,
                reputation: 85
            },
            reported_by: 'vigilant_user',
            reason: 'Contenu potentiellement promotionnel',
            priority: 'medium',
            created_at: '2024-10-10T10:30:00Z',
            reported_at: '2024-10-10T11:45:00Z',
            community: 'Événements Locaux',
            status: 'pending',
            reports_count: 1
        },
        {
            id: 2,
            type: 'comment',
            title: 'Commentaire sur "Nouveau restaurant en ville"',
            content: 'Ce restaurant est vraiment nul, la bouffe est dégueulasse et le service est horrible. Je recommande personne d\'y aller, c\'est de l\'arnaque pure !',
            parent_post: {
                title: 'Nouveau restaurant en ville - vos avis ?',
                author: 'foodie123'
            },
            author: {
                username: 'angry_customer',
                avatar: null,
                reputation: 12
            },
            reported_by: 'restaurant_owner',
            reason: 'Langage inapproprié et attaque personnelle',
            priority: 'high',
            created_at: '2024-10-10T09:15:00Z',
            reported_at: '2024-10-10T09:30:00Z',
            community: 'Restaurants & Cuisine',
            status: 'pending',
            reports_count: 2
        },
        {
            id: 3,
            type: 'post',
            title: 'URGENT - Gagnez de l\'argent rapidement !!!',
            content: 'OPPORTUNITÉ UNIQUE !!! Gagnez 500$ par jour en travaillant depuis chez vous ! Aucune expérience requise ! Cliquez ici maintenant : suspicious-link.com/get-rich-quick',
            author: {
                username: 'money_maker2024',
                avatar: null,
                reputation: 3
            },
            reported_by: 'community_guardian',
            reason: 'Spam évident avec liens suspects',
            priority: 'urgent',
            created_at: '2024-10-10T08:45:00Z',
            reported_at: '2024-10-10T08:50:00Z',
            community: 'Général',
            status: 'pending',
            reports_count: 5
        },
        {
            id: 4,
            type: 'comment',
            title: 'Commentaire sur "Débat politique local"',
            content: 'Tous ces politiciens sont des menteurs et des voleurs. Il faudrait les pendre tous en public pour montrer l\'exemple !',
            parent_post: {
                title: 'Débat sur les prochaines élections municipales',
                author: 'civic_minded'
            },
            author: {
                username: 'extreme_voter',
                avatar: null,
                reputation: 45
            },
            reported_by: 'peaceful_citizen',
            reason: 'Incitation à la violence',
            priority: 'urgent',
            created_at: '2024-10-10T07:20:00Z',
            reported_at: '2024-10-10T07:25:00Z',
            community: 'Politique Locale',
            status: 'pending',
            reports_count: 3
        },
        {
            id: 5,
            type: 'post',
            title: 'Vente de vélo d\'occasion',
            content: 'Je vends mon vélo de montagne en excellent état. Prix: 300$. Contactez-moi en MP si intéressé.',
            author: {
                username: 'bike_seller',
                avatar: null,
                reputation: 67
            },
            reported_by: 'rule_follower',
            reason: 'Vente dans une section non-commerciale',
            priority: 'low',
            created_at: '2024-10-09T18:30:00Z',
            reported_at: '2024-10-10T06:15:00Z',
            community: 'Général',
            status: 'pending',
            reports_count: 1
        }
    ]);

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
        return type === 'post' ? <PostIcon /> : <CommentIcon />;
    };

    const getTypeColor = (type) => {
        return type === 'post' ? 'primary' : 'secondary';
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

    const filteredItems = moderationItems.filter(item => {
        if (filter === 'all') return true;
        if (filter === 'posts') return item.type === 'post';
        if (filter === 'comments') return item.type === 'comment';
        if (filter === 'urgent') return item.priority === 'urgent';
        return true;
    });

    const handleViewContent = (item) => {
        setSelectedItem(item);
        setViewDialogOpen(true);
    };

    const handleAction = (item, action) => {
        setSelectedItem(item);
        setActionType(action);
        setActionDialogOpen(true);
    };

    const handleActionSubmit = () => {
        console.log(`Action ${actionType} sur l'item ${selectedItem.id} avec raison: ${actionReason}`);
        setActionDialogOpen(false);
        setActionReason('');
        setSelectedItem(null);
        setActionType('');
    };

    return (
        <ModeratorLayout activeSection="moderation-feed">
            <Container maxWidth="xl" sx={{ p: 3 }}>
                {/* Header */}
                <Box mb={3}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Fil de Modération
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Contenu signalé nécessitant une révision
                    </Typography>
                </Box>

                {/* Filters */}
                <Paper sx={{ p: 2, mb: 3 }}>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>Filtrer par type</InputLabel>
                                <Select
                                    value={filter}
                                    onChange={(e) => setFilter(e.target.value)}
                                    label="Filtrer par type"
                                >
                                    <MenuItem value="all">Tout</MenuItem>
                                    <MenuItem value="posts">Publications</MenuItem>
                                    <MenuItem value="comments">Commentaires</MenuItem>
                                    <MenuItem value="urgent">Urgent seulement</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} md={9}>
                            <Typography variant="body2" color="text.secondary">
                                {filteredItems.length} élément{filteredItems.length !== 1 ? 's' : ''} à modérer
                            </Typography>
                        </Grid>
                    </Grid>
                </Paper>

                {/* Moderation Items */}
                <Grid container spacing={3}>
                    {filteredItems.map((item) => (
                        <Grid item xs={12} key={item.id}>
                            <Card sx={{ border: item.priority === 'urgent' ? '2px solid #f44336' : 'none' }}>
                                <CardContent>
                                    <Box display="flex" justifyContent="between" alignItems="flex-start" mb={2}>
                                        <Box display="flex" alignItems="center" gap={1} mb={2}>
                                            {getTypeIcon(item.type)}
                                            <Chip
                                                label={item.type === 'post' ? 'Publication' : 'Commentaire'}
                                                color={getTypeColor(item.type)}
                                                size="small"
                                            />
                                            <Chip
                                                label={getPriorityLabel(item.priority)}
                                                color={getPriorityColor(item.priority)}
                                                size="small"
                                                variant="outlined"
                                            />
                                            {item.reports_count > 1 && (
                                                <Chip
                                                    label={`${item.reports_count} signalements`}
                                                    color="error"
                                                    size="small"
                                                    icon={<FlagIcon />}
                                                />
                                            )}
                                        </Box>
                                    </Box>

                                    <Typography variant="h6" gutterBottom>
                                        {item.title}
                                    </Typography>

                                    <Box display="flex" alignItems="center" gap={2} mb={2}>
                                        <Avatar sx={{ width: 32, height: 32 }}>
                                            {item.author.username.charAt(0).toUpperCase()}
                                        </Avatar>
                                        <Box>
                                            <Typography variant="body2">
                                                @{item.author.username}
                                            </Typography>
                                            <Typography variant="caption" color="text.secondary">
                                                Réputation: {item.author.reputation}
                                            </Typography>
                                        </Box>
                                        <Typography variant="body2" color="text.secondary">
                                            dans {item.community}
                                        </Typography>
                                    </Box>

                                    <Paper sx={{ p: 2, backgroundColor: 'grey.50', mb: 2 }}>
                                        <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                                            {item.content.length > 200 
                                                ? `${item.content.substring(0, 200)}...` 
                                                : item.content
                                            }
                                        </Typography>
                                    </Paper>

                                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                                        <WarningIcon color="warning" fontSize="small" />
                                        <Typography variant="body2" color="text.secondary">
                                            <strong>Signalé par @{item.reported_by}:</strong> {item.reason}
                                        </Typography>
                                    </Box>

                                    <Box display="flex" alignItems="center" gap={1} mb={3}>
                                        <TimeIcon fontSize="small" color="action" />
                                        <Typography variant="caption" color="text.secondary">
                                            Publié {formatTimeAgo(item.created_at)} • 
                                            Signalé {formatTimeAgo(item.reported_at)}
                                        </Typography>
                                    </Box>

                                    {item.type === 'comment' && item.parent_post && (
                                        <Paper sx={{ p: 2, backgroundColor: 'info.light', mb: 2 }}>
                                            <Typography variant="body2" color="info.dark">
                                                <strong>Post parent:</strong> "{item.parent_post.title}" par @{item.parent_post.author}
                                            </Typography>
                                        </Paper>
                                    )}

                                    <Divider sx={{ my: 2 }} />

                                    <Box display="flex" gap={2} flexWrap="wrap">
                                        <Button
                                            variant="outlined"
                                            startIcon={<ViewIcon />}
                                            onClick={() => handleViewContent(item)}
                                        >
                                            Voir le contenu complet
                                        </Button>
                                        
                                        {item.type === 'comment' && (
                                            <Button
                                                variant="outlined"
                                                startIcon={<PostIcon />}
                                                onClick={() => handleViewContent({...item, viewType: 'parent'})}
                                            >
                                                Voir le post parent
                                            </Button>
                                        )}

                                        <Button
                                            variant="contained"
                                            color="success"
                                            startIcon={<ApproveIcon />}
                                            onClick={() => handleAction(item, 'approve')}
                                        >
                                            Approuver
                                        </Button>

                                        <Button
                                            variant="contained"
                                            color="error"
                                            startIcon={<RejectIcon />}
                                            onClick={() => handleAction(item, 'reject')}
                                        >
                                            Rejeter
                                        </Button>
                                    </Box>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>

                {/* View Content Dialog */}
                <Dialog
                    open={viewDialogOpen}
                    onClose={() => setViewDialogOpen(false)}
                    maxWidth="md"
                    fullWidth
                >
                    {selectedItem && (
                        <>
                            <DialogTitle>
                                {selectedItem.viewType === 'parent' 
                                    ? `Post parent: ${selectedItem.parent_post?.title}`
                                    : `Contenu complet: ${selectedItem.title}`
                                }
                            </DialogTitle>
                            <DialogContent>
                                {selectedItem.viewType === 'parent' ? (
                                    <Box>
                                        <Typography variant="body1" paragraph>
                                            <strong>Titre:</strong> {selectedItem.parent_post?.title}
                                        </Typography>
                                        <Typography variant="body1" paragraph>
                                            <strong>Auteur:</strong> @{selectedItem.parent_post?.author}
                                        </Typography>
                                        <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                                            <Typography variant="body2">
                                                [Contenu du post parent - données statiques simulées]
                                            </Typography>
                                        </Paper>
                                    </Box>
                                ) : (
                                    <Box>
                                        <Typography variant="body2" color="text.secondary" gutterBottom>
                                            Par @{selectedItem.author.username} dans {selectedItem.community}
                                        </Typography>
                                        <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                                            <Typography variant="body1" style={{ whiteSpace: 'pre-wrap' }}>
                                                {selectedItem.content}
                                            </Typography>
                                        </Paper>
                                        <Box mt={2}>
                                            <Typography variant="body2" color="text.secondary">
                                                <strong>Raison du signalement:</strong> {selectedItem.reason}
                                            </Typography>
                                            <Typography variant="body2" color="text.secondary">
                                                <strong>Signalé par:</strong> @{selectedItem.reported_by}
                                            </Typography>
                                        </Box>
                                    </Box>
                                )}
                            </DialogContent>
                            <DialogActions>
                                <Button onClick={() => setViewDialogOpen(false)}>
                                    Fermer
                                </Button>
                            </DialogActions>
                        </>
                    )}
                </Dialog>

                {/* Action Dialog */}
                <Dialog
                    open={actionDialogOpen}
                    onClose={() => setActionDialogOpen(false)}
                    maxWidth="sm"
                    fullWidth
                >
                    <DialogTitle>
                        {actionType === 'approve' ? 'Approuver le contenu' : 'Rejeter le contenu'}
                    </DialogTitle>
                    <DialogContent>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                            {selectedItem?.title}
                        </Typography>
                        <TextField
                            fullWidth
                            multiline
                            rows={3}
                            label="Raison (optionnelle)"
                            value={actionReason}
                            onChange={(e) => setActionReason(e.target.value)}
                            placeholder={
                                actionType === 'approve' 
                                    ? "Pourquoi approuvez-vous ce contenu ?" 
                                    : "Pourquoi rejetez-vous ce contenu ?"
                            }
                            sx={{ mt: 2 }}
                        />
                    </DialogContent>
                    <DialogActions>
                        <Button onClick={() => setActionDialogOpen(false)}>
                            Annuler
                        </Button>
                        <Button 
                            onClick={handleActionSubmit}
                            variant="contained"
                            color={actionType === 'approve' ? 'success' : 'error'}
                        >
                            {actionType === 'approve' ? 'Approuver' : 'Rejeter'}
                        </Button>
                    </DialogActions>
                </Dialog>
            </Container>
        </ModeratorLayout>
    );
};

export default ModerationFeed;