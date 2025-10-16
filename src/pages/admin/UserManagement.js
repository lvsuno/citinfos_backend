import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Paper,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    TablePagination,
    TextField,
    InputAdornment,
    Chip,
    Avatar,
    IconButton,
    Menu,
    MenuItem,
    Alert,
    CircularProgress,
    FormControl,
    InputLabel,
    Select,
    Grid
} from '@mui/material';
import {
    Search as SearchIcon,
    MoreVert as MoreVertIcon,
    Person as PersonIcon,
    Email as EmailIcon,
    LocationOn as LocationIcon,
    CalendarToday as CalendarIcon
} from '@mui/icons-material';
import AdminLayout from '../../components/admin/AdminLayout';
import { apiService } from '../../services/apiService';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const UserManagement = () => {
    const navigate = useNavigate();
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(10);
    const [totalUsers, setTotalUsers] = useState(0);
    const [searchTerm, setSearchTerm] = useState('');
    const [roleFilter, setRoleFilter] = useState('');
    const [anchorEl, setAnchorEl] = useState(null);
    const [selectedUser, setSelectedUser] = useState(null);

    // Charger la liste des utilisateurs
    const fetchUsers = async () => {
        try {
            setLoading(true);
            setError(null);

            const params = {
                page: page + 1, // API utilise 1-indexed
                page_size: rowsPerPage,
                search: searchTerm,
                role: roleFilter
            };

            const response = await apiService.getAdminUsers(params);

            setUsers(response.data.results || response.data);
            setTotalUsers(response.data.count || response.data.length);
        } catch (err) {
            console.error('Erreur lors du chargement des utilisateurs:', err);
            setError('Impossible de charger la liste des utilisateurs');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, [page, rowsPerPage, searchTerm, roleFilter]);

    const handleSearchChange = (event) => {
        setSearchTerm(event.target.value);
        setPage(0); // Reset to first page
    };

    const handleRoleFilterChange = (event) => {
        setRoleFilter(event.target.value);
        setPage(0); // Reset to first page
    };

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    const handleMenuOpen = (event, user) => {
        setAnchorEl(event.currentTarget);
        setSelectedUser(user);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
        setSelectedUser(null);
    };

    const handleViewProfile = () => {
        if (selectedUser) {
            navigate(`/admin/users/${selectedUser.user_id}`);
        }
        handleMenuClose();
    };

    const getRoleColor = (role) => {
        const roleColors = {
            'admin': '#ef4444',
            'moderator': '#f59e0b',
            'professional': '#8b5cf6',
            'commercial': '#06b6d4',
            'normal': '#10b981'
        };
        return roleColors[role] || '#64748b';
    };

    const getRoleLabel = (role) => {
        const roleLabels = {
            'admin': 'Administrateur',
            'moderator': 'Modérateur',
            'professional': 'Professionnel',
            'commercial': 'Commercial',
            'normal': 'Utilisateur'
        };
        return roleLabels[role] || role;
    };

    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        try {
            return format(new Date(dateString), 'dd/MM/yyyy', { locale: fr });
        } catch {
            return 'Date invalide';
        }
    };

    if (loading && users.length === 0) {
        return (
            <AdminLayout activeSection="users">
                <Box sx={{ p: 3 }}>
                    <Box display="flex" flexDirection="column" alignItems="center" justifyContent="center" minHeight="400px">
                        <CircularProgress />
                        <Typography variant="h6" sx={{ mt: 2 }}>
                            Chargement des utilisateurs...
                        </Typography>
                    </Box>
                </Box>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout activeSection="users">
            <Box sx={{ p: 3 }}>
                <Paper sx={{ p: 3, mb: 3 }}>
                    <Typography variant="h4" gutterBottom>
                        Gestion des utilisateurs
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Gérez tous les utilisateurs de la plateforme
                    </Typography>
                </Paper>

                {error && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                        {error}
                    </Alert>
                )}

                {/* Filtres et recherche */}
                <Paper sx={{ p: 2, mb: 3 }}>
                    <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} md={6}>
                        <TextField
                            fullWidth
                            variant="outlined"
                            placeholder="Rechercher par nom, email ou nom d'utilisateur..."
                            value={searchTerm}
                            onChange={handleSearchChange}
                            InputProps={{
                                startAdornment: (
                                    <InputAdornment position="start">
                                        <SearchIcon />
                                    </InputAdornment>
                                ),
                            }}
                        />
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <FormControl fullWidth>
                            <InputLabel>Filtrer par rôle</InputLabel>
                            <Select
                                value={roleFilter}
                                label="Filtrer par rôle"
                                onChange={handleRoleFilterChange}
                            >
                                <MenuItem value="">Tous les rôles</MenuItem>
                                <MenuItem value="admin">Administrateur</MenuItem>
                                <MenuItem value="moderator">Modérateur</MenuItem>
                                <MenuItem value="professional">Professionnel</MenuItem>
                                <MenuItem value="commercial">Commercial</MenuItem>
                                <MenuItem value="normal">Utilisateur</MenuItem>
                            </Select>
                        </FormControl>
                    </Grid>
                    <Grid item xs={12} md={3}>
                        <Typography variant="body2" color="text.secondary">
                            Total: {totalUsers} utilisateur{totalUsers !== 1 ? 's' : ''}
                        </Typography>
                    </Grid>
                </Grid>
            </Paper>

            {/* Tableau des utilisateurs */}
            <Paper sx={{ overflow: 'hidden' }}>
                <TableContainer>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Utilisateur</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Rôle</TableCell>
                                <TableCell>Localisation</TableCell>
                                <TableCell>Date d'inscription</TableCell>
                                <TableCell>Statut</TableCell>
                                <TableCell align="center">Actions</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {users.map((user) => (
                                <TableRow key={user.id} hover>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <Avatar
                                                src={user.profile_picture}
                                                sx={{ width: 40, height: 40 }}
                                            >
                                                {user.username?.charAt(0).toUpperCase()}
                                            </Avatar>
                                            <Box>
                                                <Typography variant="subtitle2">
                                                    {user.display_name || user.username}
                                                </Typography>
                                                <Typography variant="body2" color="text.secondary">
                                                    @{user.username}
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <EmailIcon fontSize="small" color="action" />
                                            <Typography variant="body2">
                                                {user.email}
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <Chip
                                            label={getRoleLabel(user.role)}
                                            size="small"
                                            sx={{
                                                backgroundColor: getRoleColor(user.role),
                                                color: 'white',
                                                fontWeight: 600
                                            }}
                                        />
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <LocationIcon fontSize="small" color="action" />
                                            <Typography variant="body2">
                                                {user.location || 'Non spécifié'}
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                            <CalendarIcon fontSize="small" color="action" />
                                            <Typography variant="body2">
                                                {formatDate(user.date_joined)}
                                            </Typography>
                                        </Box>
                                    </TableCell>
                                    <TableCell>
                                        <Chip
                                            label={user.is_verified ? 'Vérifié' : 'Non vérifié'}
                                            size="small"
                                            color={user.is_verified ? 'success' : 'warning'}
                                            variant="outlined"
                                        />
                                    </TableCell>
                                    <TableCell align="center">
                                        <IconButton
                                            onClick={(e) => handleMenuOpen(e, user)}
                                            size="small"
                                        >
                                            <MoreVertIcon />
                                        </IconButton>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>

                <TablePagination
                    rowsPerPageOptions={[5, 10, 25, 50]}
                    component="div"
                    count={totalUsers}
                    rowsPerPage={rowsPerPage}
                    page={page}
                    onPageChange={handleChangePage}
                    onRowsPerPageChange={handleChangeRowsPerPage}
                    labelRowsPerPage="Lignes par page:"
                    labelDisplayedRows={({ from, to, count }) =>
                        `${from}-${to} sur ${count !== -1 ? count : `plus de ${to}`}`
                    }
                />
            </Paper>

            {/* Menu d'actions */}
            <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
            >
                <MenuItem onClick={handleViewProfile}>
                    <PersonIcon sx={{ mr: 1 }} />
                    Voir le profil
                </MenuItem>
                <MenuItem onClick={handleMenuClose}>
                    <EmailIcon sx={{ mr: 1 }} />
                    Envoyer un message
                </MenuItem>
            </Menu>
            </Box>
        </AdminLayout>
    );
};

export default UserManagement;