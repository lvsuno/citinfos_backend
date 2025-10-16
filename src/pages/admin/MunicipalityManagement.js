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
    List,
    ListItem,
    ListItemAvatar,
    ListItemText,
    CircularProgress,
    Alert,
    Accordion,
    AccordionSummary,
    AccordionDetails,
    Button,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    Tooltip,
    IconButton
} from '@mui/material';
import {
    Search as SearchIcon,
    ExpandMore as ExpandMoreIcon,
    LocationCity as LocationCityIcon,
    People as PeopleIcon,
    Article as PostIcon,
    TrendingUp as TrendingUpIcon,
    Visibility as ViewIcon,
    FilterList as FilterIcon,
    Map as MapIcon,
    ChevronLeft as ChevronLeftIcon,
    ChevronRight as ChevronRightIcon
} from '@mui/icons-material';
import AdminLayout from '../../components/admin/AdminLayout';
import apiService from '../../services/apiService';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const MunicipalityManagement = () => {
    const [municipalities, setMunicipalities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedProvince, setSelectedProvince] = useState('');
    const [municipalityStats, setMunicipalityStats] = useState({});
    const [activeUsers, setActiveUsers] = useState({});
    const [expandedMunicipality, setExpandedMunicipality] = useState(null);
    
    // Pagination states
    const [currentPage, setCurrentPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [totalCount, setTotalCount] = useState(0);
    const [totalPages, setTotalPages] = useState(0);

    useEffect(() => {
        fetchMunicipalities();
    }, [currentPage, pageSize]);

    useEffect(() => {
        // Recharger les municipalités quand les filtres changent
        setCurrentPage(1); // Reset à la première page
        const delayedSearch = setTimeout(() => {
            fetchMunicipalities();
        }, 500); // Délai pour éviter trop d'appels API

        return () => clearTimeout(delayedSearch);
    }, [searchTerm, selectedProvince]);

    const fetchMunicipalities = async () => {
        try {
            setLoading(true);
            setError(null);

            // Récupérer les municipalités réelles depuis l'API
            const response = await apiService.getAdminMunicipalities({
                search: searchTerm,
                province: selectedProvince,
                page: currentPage,
                page_size: pageSize
            });

            setMunicipalities(response.data.results || []);
            setTotalCount(response.data.total || 0);
            setTotalPages(Math.ceil((response.data.total || 0) / pageSize));
        } catch (err) {
            console.error('Erreur lors du chargement des municipalités:', err);
            setError('Impossible de charger les municipalités');
        } finally {
            setLoading(false);
        }
    };

    const fetchMunicipalityStats = async (municipalityId) => {
        try {
            const response = await apiService.getAdminMunicipalityStats(municipalityId);
            const stats = response.data.stats;

            setMunicipalityStats(prev => ({
                ...prev,
                [municipalityId]: stats
            }));
        } catch (err) {
            console.error('Erreur lors du chargement des stats:', err);
        }
    };

    const fetchActiveUsers = async (municipalityId) => {
        try {
            const response = await apiService.getAdminMunicipalityActiveUsers(municipalityId);
            const users = response.data.active_users;

            setActiveUsers(prev => ({
                ...prev,
                [municipalityId]: users
            }));
        } catch (err) {
            console.error('Erreur lors du chargement des utilisateurs actifs:', err);
        }
    };

    const handleMunicipalityExpand = async (municipalityId) => {
        if (expandedMunicipality === municipalityId) {
            setExpandedMunicipality(null);
        } else {
            setExpandedMunicipality(municipalityId);
            
            // Charger les données si pas encore chargées
            if (!municipalityStats[municipalityId]) {
                await fetchMunicipalityStats(municipalityId);
            }
            if (!activeUsers[municipalityId]) {
                await fetchActiveUsers(municipalityId);
            }
        }
    };

    // Récupérer les provinces uniques depuis les municipalités chargées
    const provinces = [...new Set(municipalities.map(m => m.province).filter(Boolean))];

    const getPopulationColor = (population) => {
        if (!population) return 'default';
        if (population > 1000000) return 'error';
        if (population > 500000) return 'warning';
        if (population > 100000) return 'info';
        return 'default';
    };

    const handlePageChange = (newPage) => {
        setCurrentPage(newPage);
    };

    const handlePageSizeChange = (event) => {
        setPageSize(event.target.value);
        setCurrentPage(1); // Reset à la première page
    };

    if (loading) {
        return (
            <AdminLayout activeSection="municipalities">
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
            <AdminLayout activeSection="municipalities">
                <Box sx={{ p: 3 }}>
                    <Alert severity="error">{error}</Alert>
                </Box>
            </AdminLayout>
        );
    }

    return (
        <AdminLayout activeSection="municipalities">
            <Box sx={{ p: 3 }}>
                {/* Header */}
                <Box mb={3}>
                    <Typography variant="h4" component="h1" gutterBottom>
                        Gestion des Municipalités
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Gérez et analysez les municipalités et leur activité
                    </Typography>
                </Box>

                {/* Filtres et recherche */}
                <Paper sx={{ p: 2, mb: 3 }}>
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <TextField
                                fullWidth
                                placeholder="Rechercher une municipalité ou région..."
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
                        <Grid item xs={12} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>Province</InputLabel>
                                <Select
                                    value={selectedProvince}
                                    onChange={(e) => setSelectedProvince(e.target.value)}
                                    label="Province"
                                >
                                    <MenuItem value="">Toutes les provinces</MenuItem>
                                    {provinces.map(province => (
                                        <MenuItem key={province} value={province}>
                                            {province}
                                        </MenuItem>
                                    ))}
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} md={3}>
                            <Box display="flex" alignItems="center" gap={2}>
                                <Typography variant="body2" color="text.secondary">
                                    {totalCount} municipalité{totalCount !== 1 ? 's' : ''} au total
                                </Typography>
                                <FormControl size="small" variant="outlined">
                                    <InputLabel>Par page</InputLabel>
                                    <Select
                                        value={pageSize}
                                        onChange={handlePageSizeChange}
                                        label="Par page"
                                        sx={{ minWidth: 100 }}
                                    >
                                        <MenuItem value={5}>5</MenuItem>
                                        <MenuItem value={10}>10</MenuItem>
                                        <MenuItem value={20}>20</MenuItem>
                                        <MenuItem value={50}>50</MenuItem>
                                    </Select>
                                </FormControl>
                            </Box>
                        </Grid>
                    </Grid>
                </Paper>

                {/* Liste des municipalités */}
                <Paper sx={{ overflow: 'hidden' }}>
                    {municipalities.map((municipality) => (
                        <Accordion 
                            key={municipality.id}
                            expanded={expandedMunicipality === municipality.id}
                            onChange={() => handleMunicipalityExpand(municipality.id)}
                        >
                            <AccordionSummary
                                expandIcon={<ExpandMoreIcon />}
                                aria-controls={`municipality-${municipality.id}-content`}
                                id={`municipality-${municipality.id}-header`}
                            >
                                <Box display="flex" alignItems="center" width="100%">
                                    <LocationCityIcon sx={{ mr: 2, color: 'primary.main' }} />
                                    <Box flexGrow={1}>
                                        <Typography variant="h6">
                                            {municipality.name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary">
                                            {municipality.region ? `${municipality.region}, ` : ''}{municipality.province || municipality.country?.name}
                                        </Typography>
                                    </Box>
                                    <Box display="flex" gap={1} mr={2}>
                                        <Chip
                                            label={municipality.type}
                                            size="small"
                                            color="primary"
                                            variant="outlined"
                                        />
                                        {municipality.population && (
                                            <Chip
                                                label={`${municipality.population.toLocaleString()} hab.`}
                                                size="small"
                                                color={getPopulationColor(municipality.population)}
                                            />
                                        )}
                                    </Box>
                                </Box>
                            </AccordionSummary>
                            
                            <AccordionDetails>
                                {expandedMunicipality === municipality.id && (
                                    <Grid container spacing={3}>
                                        {/* Statistiques */}
                                        <Grid item xs={12} md={8}>
                                            <Typography variant="h6" gutterBottom>
                                                Statistiques d'activité
                                            </Typography>
                                            {municipalityStats[municipality.id] ? (
                                                <Grid container spacing={2}>
                                                    <Grid item xs={6} md={3}>
                                                        <Card variant="outlined">
                                                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                                                <PostIcon color="primary" sx={{ fontSize: 32, mb: 1 }} />
                                                                <Typography variant="h5">
                                                                    {municipalityStats[municipality.id].posts_count}
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Publications
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                    <Grid item xs={6} md={3}>
                                                        <Card variant="outlined">
                                                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                                                <PeopleIcon color="success" sx={{ fontSize: 32, mb: 1 }} />
                                                                <Typography variant="h5">
                                                                    {municipalityStats[municipality.id].active_users_count}
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Utilisateurs actifs
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                    <Grid item xs={6} md={3}>
                                                        <Card variant="outlined">
                                                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                                                <PeopleIcon color="info" sx={{ fontSize: 32, mb: 1 }} />
                                                                <Typography variant="h5">
                                                                    {municipalityStats[municipality.id].total_users_count}
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Total utilisateurs
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                    <Grid item xs={6} md={3}>
                                                        <Card variant="outlined">
                                                            <CardContent sx={{ textAlign: 'center', py: 2 }}>
                                                                <TrendingUpIcon 
                                                                    color={municipalityStats[municipality.id].growth_rate >= 0 ? "success" : "error"} 
                                                                    sx={{ fontSize: 32, mb: 1 }} 
                                                                />
                                                                <Typography variant="h5">
                                                                    {municipalityStats[municipality.id].growth_rate}%
                                                                </Typography>
                                                                <Typography variant="body2" color="text.secondary">
                                                                    Croissance
                                                                </Typography>
                                                            </CardContent>
                                                        </Card>
                                                    </Grid>
                                                </Grid>
                                            ) : (
                                                <Box display="flex" justifyContent="center" py={3}>
                                                    <CircularProgress size={24} />
                                                </Box>
                                            )}
                                        </Grid>

                                        {/* Utilisateurs les plus actifs */}
                                        <Grid item xs={12} md={4}>
                                            <Typography variant="h6" gutterBottom>
                                                Utilisateurs les plus actifs
                                            </Typography>
                                            {activeUsers[municipality.id] ? (
                                                <List dense>
                                                    {activeUsers[municipality.id].slice(0, 5).map((user, index) => (
                                                        <ListItem key={user.id}>
                                                            <ListItemAvatar>
                                                                <Avatar
                                                                    src={user.profile_picture}
                                                                    sx={{ 
                                                                        width: 32, 
                                                                        height: 32,
                                                                        bgcolor: index === 0 ? 'gold' : index === 1 ? 'silver' : index === 2 ? '#CD7F32' : 'grey.300'
                                                                    }}
                                                                >
                                                                    {user.full_name?.charAt(0) || user.username.charAt(0)}
                                                                </Avatar>
                                                            </ListItemAvatar>
                                                            <ListItemText
                                                                primary={
                                                                    <Box display="flex" alignItems="center" gap={1}>
                                                                        <Typography variant="body2">
                                                                            {user.full_name || user.username}
                                                                        </Typography>
                                                                        {index < 3 && (
                                                                            <Chip
                                                                                label={`#${index + 1}`}
                                                                                size="small"
                                                                                color={index === 0 ? 'warning' : 'default'}
                                                                            />
                                                                        )}
                                                                    </Box>
                                                                }
                                                                secondary={`${user.posts_count} publications`}
                                                            />
                                                        </ListItem>
                                                    ))}
                                                </List>
                                            ) : (
                                                <Box display="flex" justifyContent="center" py={2}>
                                                    <CircularProgress size={20} />
                                                </Box>
                                            )}
                                        </Grid>
                                    </Grid>
                                )}
                            </AccordionDetails>
                        </Accordion>
                    ))}
                </Paper>

                {/* Contrôles de pagination */}
                {totalPages > 1 && (
                    <Paper sx={{ p: 2, mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Typography variant="body2" color="text.secondary">
                            Page {currentPage} sur {totalPages} ({totalCount} éléments au total)
                        </Typography>
                        
                        <Box display="flex" alignItems="center" gap={1}>
                            <Button
                                variant="outlined"
                                size="small"
                                startIcon={<ChevronLeftIcon />}
                                disabled={currentPage === 1}
                                onClick={() => handlePageChange(currentPage - 1)}
                            >
                                Précédent
                            </Button>
                            
                            {/* Numéros de pages */}
                            <Box display="flex" gap={0.5}>
                                {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                                    let pageNum;
                                    if (totalPages <= 5) {
                                        pageNum = i + 1;
                                    } else if (currentPage <= 3) {
                                        pageNum = i + 1;
                                    } else if (currentPage >= totalPages - 2) {
                                        pageNum = totalPages - 4 + i;
                                    } else {
                                        pageNum = currentPage - 2 + i;
                                    }
                                    
                                    return (
                                        <Button
                                            key={pageNum}
                                            variant={currentPage === pageNum ? "contained" : "outlined"}
                                            size="small"
                                            sx={{ minWidth: 40 }}
                                            onClick={() => handlePageChange(pageNum)}
                                        >
                                            {pageNum}
                                        </Button>
                                    );
                                })}
                            </Box>
                            
                            <Button
                                variant="outlined"
                                size="small"
                                endIcon={<ChevronRightIcon />}
                                disabled={currentPage === totalPages}
                                onClick={() => handlePageChange(currentPage + 1)}
                            >
                                Suivant
                            </Button>
                        </Box>
                    </Paper>
                )}

                {municipalities.length === 0 && !loading && (
                    <Paper sx={{ p: 4, textAlign: 'center' }}>
                        <LocationCityIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            Aucune municipalité trouvée
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            Essayez de modifier vos critères de recherche
                        </Typography>
                    </Paper>
                )}
            </Box>
        </AdminLayout>
    );
};

export default MunicipalityManagement;