import React, { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
    TextField,
    InputAdornment,
    Chip,
    Avatar,
    CircularProgress,
    Alert,
    Button,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    IconButton,
    Tooltip,
    List,
    ListItem,
    ListItemText,
    ListItemAvatar,
    Divider,
    Badge,
    TablePagination
} from '@mui/material';
import {
    Search as SearchIcon,
    Support as SupportIcon,
    Email as EmailIcon,
    Priority as PriorityIcon,
    Assignment as AssignmentIcon,
    Message as MessageIcon,
    Send as SendIcon,
    Close as CloseIcon,
    Refresh as RefreshIcon,
    Warning as WarningIcon,
    CheckCircle as CheckCircleIcon,
    Schedule as ScheduleIcon,
    Person as PersonIcon
} from '@mui/icons-material';
import AdminLayout from '../../components/admin/AdminLayout';
import apiService from '../../services/apiService';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const SupportManagement = () => {
    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [detailsOpen, setDetailsOpen] = useState(false);
    const [replyMessage, setReplyMessage] = useState('');
    const [isInternal, setIsInternal] = useState(false);
    const [submittingReply, setSubmittingReply] = useState(false);
    
    // Filters
    const [statusFilter, setStatusFilter] = useState('');
    const [priorityFilter, setPriorityFilter] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('');
    const [assignedFilter, setAssignedFilter] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    
    // Pagination
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [totalCount, setTotalCount] = useState(0);
    
    // Statistics
    const [stats, setStats] = useState({});

    useEffect(() => {
        fetchTickets();
        fetchStats();
    }, [page, rowsPerPage, statusFilter, priorityFilter, categoryFilter, assignedFilter, searchTerm]);

    const fetchTickets = async () => {
        try {
            setLoading(true);
            setError(null);

            const params = {
                page: page + 1, // API uses 1-based pagination
                page_size: rowsPerPage,
                ...(statusFilter && { status: statusFilter }),
                ...(priorityFilter && { priority: priorityFilter }),
                ...(categoryFilter && { category: categoryFilter }),
                ...(assignedFilter && { assigned: assignedFilter }),
                ...(searchTerm && { search: searchTerm })
            };

            const response = await apiService.getAdminSupportTickets(params);
            setTickets(response.data.results || []);
            setTotalCount(response.data.total || 0);
        } catch (err) {
            console.error('Erreur lors du chargement des tickets:', err);
            setError('Impossible de charger les tickets de support');
        } finally {
            setLoading(false);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await apiService.getAdminSupportStats();
            setStats(response.data || {});
        } catch (err) {
            console.error('Erreur lors du chargement des statistiques:', err);
        }
    };

    const fetchTicketDetails = async (ticketId) => {
        try {
            const response = await apiService.getAdminSupportTicketDetail(ticketId);
            setSelectedTicket(response.data);
            setDetailsOpen(true);
        } catch (err) {
            console.error('Erreur lors du chargement des détails:', err);
        }
    };

    const handleSendReply = async () => {
        if (!replyMessage.trim() || !selectedTicket) return;

        try {
            setSubmittingReply(true);
            await apiService.sendAdminSupportReply(selectedTicket.id, {
                content: replyMessage,
                is_internal: isInternal
            });

            // Refresh ticket details
            await fetchTicketDetails(selectedTicket.id);
            await fetchTickets(); // Refresh list

            setReplyMessage('');
            setIsInternal(false);
        } catch (err) {
            console.error('Erreur lors de l\'envoi de la réponse:', err);
        } finally {
            setSubmittingReply(false);
        }
    };

    const handleUpdateTicket = async (updates) => {
        if (!selectedTicket) return;

        try {
            await apiService.updateAdminSupportTicket(selectedTicket.id, updates);
            
            // Refresh ticket details and list
            await fetchTicketDetails(selectedTicket.id);
            await fetchTickets();
            await fetchStats();
        } catch (err) {
            console.error('Erreur lors de la mise à jour:', err);
        }
    };

    const getStatusColor = (status) => {
        const colors = {
            'open': 'error',
            'in_progress': 'warning',
            'waiting_user': 'info',
            'resolved': 'success',
            'closed': 'default'
        };
        return colors[status] || 'default';
    };

    const getPriorityColor = (priority) => {
        const colors = {
            'urgent': 'error',
            'high': 'warning',
            'medium': 'info',
            'low': 'default'
        };
        return colors[priority] || 'default';
    };

    const getStatusLabel = (status) => {
        const labels = {
            'open': 'Ouvert',
            'in_progress': 'En cours',
            'waiting_user': 'En attente utilisateur',
            'resolved': 'Résolu',
            'closed': 'Fermé'
        };
        return labels[status] || status;
    };

    const getPriorityLabel = (priority) => {
        const labels = {
            'urgent': 'Urgente',
            'high': 'Élevée',
            'medium': 'Moyenne',
            'low': 'Faible'
        };
        return labels[priority] || priority;
    };

    const getCategoryLabel = (category) => {
        const labels = {
            'technical': 'Problème technique',
            'account': 'Problème de compte',
            'billing': 'Facturation',
            'feature_request': 'Demande de fonctionnalité',
            'report': 'Signalement',
            'other': 'Autre'
        };
        return labels[category] || category;
    };

    if (loading && tickets.length === 0) {
        return (
            <AdminLayout activeSection="support">
                <Box sx={{ p: 3 }}>
                    <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                        <CircularProgress />
                    </Box>
                </Box>
            </AdminLayout>
        );
    }

    if (error) {
        return (
            <AdminLayout activeSection="support">
                <Box sx={{ p: 3 }}>
                    <Alert severity="error">{error}</Alert>
                </Box>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout activeSection="support">
            <Box sx={{ p: 3 }}>
                {/* Header */}
                <Box mb={3}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Gestion du Support
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Gérez les demandes de support et répondez aux utilisateurs
                    </Typography>
                </Box>

                {/* Statistics Cards */}
                <Grid container spacing={3} mb={3}>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <SupportIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.total_tickets || 0}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Total tickets
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <ScheduleIcon color="warning" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.open_tickets || 0}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Tickets ouverts
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <WarningIcon color="error" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">{stats.overdue_count || 0}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                    En retard
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Card>
                            <CardContent sx={{ textAlign: 'center' }}>
                                <CheckCircleIcon color="success" sx={{ fontSize: 40, mb: 1 }} />
                                <Typography variant="h4">
                                    {Math.round(((stats.total_tickets - stats.open_tickets) / Math.max(stats.total_tickets, 1)) * 100)}%
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Taux de résolution
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>
                </Grid>

                {/* Filters */}
                <Paper sx={{ p: 2, mb: 3 }}>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={3}>
                            <TextField
                                fullWidth
                                placeholder="Rechercher un ticket..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                InputProps={{
                                    startAdornment: (
                                        <InputAdornment position="start">
                                            <SearchIcon />
                                        </InputAdornment>
                                    )
                                }}
                            />
                        </Grid>
                        <Grid item xs={6} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>Statut</InputLabel>
                                <Select
                                    value={statusFilter}
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    label="Statut"
                                >
                                    <MenuItem value="">Tous</MenuItem>
                                    <MenuItem value="open">Ouvert</MenuItem>
                                    <MenuItem value="in_progress">En cours</MenuItem>
                                    <MenuItem value="waiting_user">En attente</MenuItem>
                                    <MenuItem value="resolved">Résolu</MenuItem>
                                    <MenuItem value="closed">Fermé</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={6} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>Priorité</InputLabel>
                                <Select
                                    value={priorityFilter}
                                    onChange={(e) => setPriorityFilter(e.target.value)}
                                    label="Priorité"
                                >
                                    <MenuItem value="">Toutes</MenuItem>
                                    <MenuItem value="urgent">Urgente</MenuItem>
                                    <MenuItem value="high">Élevée</MenuItem>
                                    <MenuItem value="medium">Moyenne</MenuItem>
                                    <MenuItem value="low">Faible</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={6} md={2}>
                            <FormControl fullWidth>
                                <InputLabel>Assignation</InputLabel>
                                <Select
                                    value={assignedFilter}
                                    onChange={(e) => setAssignedFilter(e.target.value)}
                                    label="Assignation"
                                >
                                    <MenuItem value="">Tous</MenuItem>
                                    <MenuItem value="unassigned">Non assignés</MenuItem>
                                    <MenuItem value="assigned">Assignés</MenuItem>
                                    <MenuItem value="me">Mes tickets</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={6} md={3}>
                            <Button
                                variant="outlined"
                                startIcon={<RefreshIcon />}
                                onClick={() => {
                                    fetchTickets();
                                    fetchStats();
                                }}
                                disabled={loading}
                            >
                                Actualiser
                            </Button>
                        </Grid>
                    </Grid>
                </Paper>

                {/* Tickets Table */}
                <Paper>
                    <TableContainer>
                        <Table>
                            <TableHead>
                                <TableRow>
                                    <TableCell>Ticket</TableCell>
                                    <TableCell>Sujet</TableCell>
                                    <TableCell>Utilisateur</TableCell>
                                    <TableCell>Statut</TableCell>
                                    <TableCell>Priorité</TableCell>
                                    <TableCell>Assigné à</TableCell>
                                    <TableCell>Messages</TableCell>
                                    <TableCell>Créé</TableCell>
                                    <TableCell>Actions</TableCell>
                                </TableRow>
                            </TableHead>
                            <TableBody>
                                {tickets.map((ticket) => (
                                    <TableRow 
                                        key={ticket.id}
                                        sx={{ 
                                            backgroundColor: ticket.is_overdue ? 'error.light' : 'inherit',
                                            opacity: ticket.is_overdue ? 0.9 : 1
                                        }}
                                    >
                                        <TableCell>
                                            <Box display="flex" alignItems="center" gap={1}>
                                                <Typography variant="body2" fontWeight="bold">
                                                    #{ticket.ticket_number}
                                                </Typography>
                                                {ticket.is_overdue && (
                                                    <Tooltip title="Ticket en retard">
                                                        <WarningIcon color="error" fontSize="small" />
                                                    </Tooltip>
                                                )}
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                                                {ticket.subject}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Box>
                                                <Typography variant="body2">{ticket.user_name}</Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    {ticket.user_email}
                                                </Typography>
                                            </Box>
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={getStatusLabel(ticket.status)}
                                                color={getStatusColor(ticket.status)}
                                                size="small"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            <Chip
                                                label={getPriorityLabel(ticket.priority)}
                                                color={getPriorityColor(ticket.priority)}
                                                size="small"
                                                variant="outlined"
                                            />
                                        </TableCell>
                                        <TableCell>
                                            {ticket.assigned_to ? (
                                                <Typography variant="body2">
                                                    {ticket.assigned_to.full_name || ticket.assigned_to.username}
                                                </Typography>
                                            ) : (
                                                <Typography variant="caption" color="text.secondary">
                                                    Non assigné
                                                </Typography>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Badge badgeContent={ticket.unread_messages} color="error">
                                                <Typography variant="body2">
                                                    {ticket.total_messages}
                                                </Typography>
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Typography variant="caption">
                                                {format(new Date(ticket.created_at), 'dd/MM/yyyy HH:mm', { locale: fr })}
                                            </Typography>
                                        </TableCell>
                                        <TableCell>
                                            <Button
                                                size="small"
                                                variant="outlined"
                                                onClick={() => fetchTicketDetails(ticket.id)}
                                            >
                                                Voir
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </TableContainer>
                    
                    <TablePagination
                        component="div"
                        count={totalCount}
                        page={page}
                        onPageChange={(event, newPage) => setPage(newPage)}
                        rowsPerPage={rowsPerPage}
                        onRowsPerPageChange={(event) => {
                            setRowsPerPage(parseInt(event.target.value, 10));
                            setPage(0);
                        }}
                        labelRowsPerPage="Tickets par page:"
                        labelDisplayedRows={({ from, to, count }) => 
                            `${from}–${to} sur ${count !== -1 ? count : `plus de ${to}`}`
                        }
                    />
                </Paper>

                {/* Ticket Details Dialog */}
                <Dialog
                    open={detailsOpen}
                    onClose={() => setDetailsOpen(false)}
                    maxWidth="md"
                    fullWidth
                >
                    {selectedTicket && (
                        <>
                            <DialogTitle>
                                <Box display="flex" justifyContent="space-between" alignItems="center">
                                    <Box>
                                        <Typography variant="h6">
                                            Ticket #{selectedTicket.ticket_number}
                                        </Typography>
                                        <Typography variant="subtitle2" color="text.secondary">
                                            {selectedTicket.subject}
                                        </Typography>
                                    </Box>
                                    <Box display="flex" gap={1}>
                                        <FormControl size="small" sx={{ minWidth: 120 }}>
                                            <InputLabel>Statut</InputLabel>
                                            <Select
                                                value={selectedTicket.status}
                                                onChange={(e) => handleUpdateTicket({ status: e.target.value })}
                                                label="Statut"
                                            >
                                                <MenuItem value="open">Ouvert</MenuItem>
                                                <MenuItem value="in_progress">En cours</MenuItem>
                                                <MenuItem value="waiting_user">En attente</MenuItem>
                                                <MenuItem value="resolved">Résolu</MenuItem>
                                                <MenuItem value="closed">Fermé</MenuItem>
                                            </Select>
                                        </FormControl>
                                        <IconButton onClick={() => setDetailsOpen(false)}>
                                            <CloseIcon />
                                        </IconButton>
                                    </Box>
                                </Box>
                            </DialogTitle>
                            
                            <DialogContent>
                                {/* Ticket Info */}
                                <Grid container spacing={2} mb={3}>
                                    <Grid item xs={6}>
                                        <Typography variant="caption" color="text.secondary">
                                            Utilisateur
                                        </Typography>
                                        <Typography variant="body2">
                                            {selectedTicket.user_name} ({selectedTicket.user_email})
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">
                                            Priorité
                                        </Typography>
                                        <br />
                                        <Chip
                                            label={getPriorityLabel(selectedTicket.priority)}
                                            color={getPriorityColor(selectedTicket.priority)}
                                            size="small"
                                        />
                                    </Grid>
                                    <Grid item xs={3}>
                                        <Typography variant="caption" color="text.secondary">
                                            Catégorie
                                        </Typography>
                                        <Typography variant="body2">
                                            {getCategoryLabel(selectedTicket.category)}
                                        </Typography>
                                    </Grid>
                                </Grid>

                                {/* Original Description */}
                                <Box mb={3}>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Description initiale
                                    </Typography>
                                    <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                                        <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                                            {selectedTicket.description}
                                        </Typography>
                                    </Paper>
                                </Box>

                                {/* Messages */}
                                <Typography variant="subtitle2" gutterBottom>
                                    Conversation
                                </Typography>
                                <List sx={{ maxHeight: 400, overflow: 'auto', mb: 3 }}>
                                    {selectedTicket.messages.map((message, index) => (
                                        <React.Fragment key={message.id}>
                                            <ListItem alignItems="flex-start">
                                                <ListItemAvatar>
                                                    <Avatar>
                                                        {message.sender ? (
                                                            message.sender.is_admin ? (
                                                                <SupportIcon />
                                                            ) : (
                                                                <PersonIcon />
                                                            )
                                                        ) : (
                                                            'S'
                                                        )}
                                                    </Avatar>
                                                </ListItemAvatar>
                                                <ListItemText
                                                    primary={
                                                        <Box display="flex" justifyContent="space-between" alignItems="center">
                                                            <Typography variant="subtitle2">
                                                                {message.sender ? 
                                                                    (message.sender.full_name || message.sender.username) : 
                                                                    'Système'
                                                                }
                                                                {message.is_internal && (
                                                                    <Chip label="Interne" size="small" color="warning" sx={{ ml: 1 }} />
                                                                )}
                                                            </Typography>
                                                            <Typography variant="caption" color="text.secondary">
                                                                {format(new Date(message.created_at), 'dd/MM HH:mm', { locale: fr })}
                                                            </Typography>
                                                        </Box>
                                                    }
                                                    secondary={
                                                        <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                                                            {message.content}
                                                        </Typography>
                                                    }
                                                />
                                            </ListItem>
                                            {index < selectedTicket.messages.length - 1 && <Divider />}
                                        </React.Fragment>
                                    ))}
                                </List>

                                {/* Reply Form */}
                                <Box>
                                    <Typography variant="subtitle2" gutterBottom>
                                        Ajouter une réponse
                                    </Typography>
                                    <TextField
                                        fullWidth
                                        multiline
                                        rows={4}
                                        placeholder="Tapez votre réponse..."
                                        value={replyMessage}
                                        onChange={(e) => setReplyMessage(e.target.value)}
                                        sx={{ mb: 2 }}
                                    />
                                    <Box display="flex" justifyContent="space-between" alignItems="center">
                                        <FormControl>
                                            <Box display="flex" alignItems="center">
                                                <input
                                                    type="checkbox"
                                                    id="internal-note"
                                                    checked={isInternal}
                                                    onChange={(e) => setIsInternal(e.target.checked)}
                                                    style={{ marginRight: 8 }}
                                                />
                                                <label htmlFor="internal-note">
                                                    <Typography variant="body2">
                                                        Note interne (non visible par l'utilisateur)
                                                    </Typography>
                                                </label>
                                            </Box>
                                        </FormControl>
                                        <Button
                                            variant="contained"
                                            startIcon={<SendIcon />}
                                            onClick={handleSendReply}
                                            disabled={!replyMessage.trim() || submittingReply}
                                        >
                                            {submittingReply ? 'Envoi...' : 'Envoyer'}
                                        </Button>
                                    </Box>
                                </Box>
                            </DialogContent>
                        </>
                    )}
                </Dialog>
            </Box>
        </AdminLayout>
    );
};

export default SupportManagement;