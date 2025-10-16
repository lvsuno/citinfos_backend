import React, { useState, useEffect } from 'react';
import {
    Box,
    Container,
    Paper,
    Typography,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormControlLabel,
    Checkbox,
    Grid,
    Alert,
    Stepper,
    Step,
    StepLabel,
    Card,
    CardContent,
    Divider,
    Chip,
    CircularProgress,
    InputAdornment,
    IconButton,
    Autocomplete
} from '@mui/material';
import {
    Person as PersonIcon,
    Email as EmailIcon,
    Phone as PhoneIcon,
    Visibility,
    VisibilityOff,
    LocationOn as LocationIcon,
    Security as SecurityIcon,
    AdminPanelSettings as AdminIcon,
    Gavel as ModeratorIcon,
    Save as SaveIcon,
    Cancel as CancelIcon,
    CalendarToday as CalendarIcon
} from '@mui/icons-material';
import AdminLayout from '../../components/admin/AdminLayout';
import { useAuth } from '../../contexts/AuthContext';
import { generatePassword } from '../../utils/passwordUtils';
import { validateUserForm, generateEmployeeId } from '../../utils/userValidation';
import styles from './UserCreation.module.css';

const steps = ['Informations de base', 'Rôle et permissions', 'Confirmation'];

const UserCreation = () => {
    const { user } = useAuth();
    const [activeStep, setActiveStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [divisions, setDivisions] = useState([]);
    const [loadingDivisions, setLoadingDivisions] = useState(false);

    // Form data state
    const [formData, setFormData] = useState({
        // Informations de base
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone_number: '',
        date_of_birth: null,
        bio: '',
        administrative_division: null,

        // Rôle et permissions
        role: 'moderator',

        // Admin specific
        admin_level: 'system_admin',
        department: '',
        employee_id: '',
        access_level: 5,
        can_manage_users: true,
        can_manage_content: true,
        can_view_analytics: true,

        // Moderator specific
        moderator_level: 'junior',
        specialization: 'general',
        can_remove_posts: true,
        can_remove_comments: true,
        can_ban_users: false,
        can_suspend_users: false,
        can_manage_reports: true,

        // Options
        send_welcome_email: true
    });

    const [errors, setErrors] = useState({});
    const [alert, setAlert] = useState({ show: false, type: 'info', message: '' });

    // Load administrative divisions
    useEffect(() => {
        checkAuthentication();
        fetchDivisions();
    }, []);

    const checkAuthentication = () => {
        const token = localStorage.getItem('access_token'); // Correction de la clé
        if (!token) {
            setAlert({
                show: true,
                type: 'error',
                message: 'Vous devez être connecté pour accéder à cette page. Redirection vers la page de connexion...'
            });

            // Redirection automatique vers la page de login après 2 secondes
            setTimeout(() => {
                window.location.href = '/login';
            }, 2000);

            return false;
        }
        return true;
    };

    const fetchDivisions = async () => {
        if (!checkAuthentication()) return;

        setLoadingDivisions(true);
        try {
            const response = await fetch('http://localhost:8000/api/auth/search-divisions/?country=CAN&q=qu', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                }
            });

            if (response.status === 401) {
                setAlert({
                    show: true,
                    type: 'error',
                    message: 'Session expirée. Veuillez vous reconnecter.'
                });
                return;
            }

            if (response.ok) {
                const data = await response.json();
                setDivisions(data.results || []);
            }
        } catch (error) {
            console.error('Erreur lors du chargement des divisions:', error);
        } finally {
            setLoadingDivisions(false);
        }
    };

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));

        // Clear error for this field
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: ''
            }));
        }
    };

    const generateRandomPassword = () => {
        const newPassword = generatePassword(12, true, true, true, true);
        handleInputChange('password', newPassword);
        setAlert({
            show: true,
            type: 'info',
            message: 'Mot de passe généré automatiquement. Assurez-vous de le communiquer à l\'utilisateur.'
        });
    };

    const validateStep = (step) => {
        if (step === 0) {
            // Validation complète du formulaire pour l'étape 1
            const validation = validateUserForm(formData);
            setErrors(validation.errors);
            return validation.isValid;
        }

        // Autres étapes n'ont pas de validation spécifique pour l'instant
        return true;
    };

    const handleNext = () => {
        if (validateStep(activeStep)) {
            setActiveStep(prev => prev + 1);
        }
    };

    const handleBack = () => {
        setActiveStep(prev => prev - 1);
    };

    const handleSubmit = async () => {
        // Vérifier l'authentification avant la soumission
        if (!checkAuthentication()) {
            return;
        }

        // Validation finale complète
        const validation = validateUserForm(formData);
        if (!validation.isValid) {
            setErrors(validation.errors);
            setAlert({
                show: true,
                type: 'error',
                message: 'Veuillez corriger les erreurs dans le formulaire'
            });
            return;
        }

        setLoading(true);
        try {
            // Préparer les données pour l'API
            const submitData = {
                ...formData,
                date_of_birth: formData.date_of_birth || null,
                administrative_division: formData.administrative_division?.id || null,
                // Générer automatiquement un ID employé s'il n'y en a pas
                employee_id: formData.employee_id || (formData.role === 'admin' ? generateEmployeeId('admin') : undefined)
            };

            const response = await fetch('http://localhost:8000/api/admin/users/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify(submitData)
            });

            const data = await response.json();

            if (response.ok) {
                setAlert({
                    show: true,
                    type: 'success',
                    message: `Utilisateur ${formData.role} créé avec succès ! ${data.email_sent ? 'Email de bienvenue envoyé.' : ''}`
                });

                // Reset form après succès
                setTimeout(() => {
                    resetForm();
                    setActiveStep(0);
                }, 2000);
            } else {
                // Gestion des erreurs spécifiques du serveur
                let errorMessage = 'Erreur lors de la création de l\'utilisateur';

                // Gestion erreur 401 (non autorisé)
                if (response.status === 401) {
                    errorMessage = 'Session expirée ou permissions insuffisantes. Veuillez vous reconnecter.';
                    setAlert({
                        show: true,
                        type: 'error',
                        message: errorMessage
                    });
                    // Optionnel : rediriger vers la page de login
                    // window.location.href = '/login';
                    return;
                }

                if (data.error) {
                    if (data.error.includes('email')) {
                        setErrors({ email: 'Un utilisateur avec cet email existe déjà' });
                        errorMessage = 'Email déjà utilisé';
                    } else if (data.error.includes('username')) {
                        setErrors({ username: 'Un utilisateur avec ce nom d\'utilisateur existe déjà' });
                        errorMessage = 'Nom d\'utilisateur déjà pris';
                    } else {
                        errorMessage = data.error;
                    }
                }

                if (data.missing_fields) {
                    const fieldErrors = {};
                    data.missing_fields.forEach(field => {
                        fieldErrors[field] = 'Ce champ est requis';
                    });
                    setErrors(fieldErrors);
                    errorMessage = 'Veuillez remplir tous les champs requis';
                }

                setAlert({
                    show: true,
                    type: 'error',
                    message: errorMessage
                });

                // Retourner à la première étape si il y a des erreurs de champs
                if (data.missing_fields || data.error.includes('email') || data.error.includes('username')) {
                    setActiveStep(0);
                }
            }
        } catch (error) {
            console.error('Erreur lors de la création:', error);
            setAlert({
                show: true,
                type: 'error',
                message: 'Erreur de connexion. Veuillez vérifier votre connexion internet et réessayer.'
            });
        } finally {
            setLoading(false);
        }
    };

    const resetForm = () => {
        setFormData({
            username: '',
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            phone_number: '',
            date_of_birth: null,
            bio: '',
            administrative_division: null,
            role: 'moderator',
            admin_level: 'system_admin',
            department: '',
            employee_id: '',
            access_level: 5,
            can_manage_users: true,
            can_manage_content: true,
            can_view_analytics: true,
            moderator_level: 'junior',
            specialization: 'general',
            can_remove_posts: true,
            can_remove_comments: true,
            can_ban_users: false,
            can_suspend_users: false,
            can_manage_reports: true,
            send_welcome_email: true
        });
        setErrors({});
    };

    const renderStepContent = (step) => {
        switch (step) {
            case 0:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <PersonIcon />
                            Informations personnelles
                        </Typography>

                        <Grid container spacing={3}>
                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Nom d'utilisateur"
                                    value={formData.username}
                                    onChange={(e) => handleInputChange('username', e.target.value)}
                                    error={!!errors.username}
                                    helperText={errors.username}
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <PersonIcon />
                                            </InputAdornment>
                                        )
                                    }}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Email"
                                    type="email"
                                    value={formData.email}
                                    onChange={(e) => handleInputChange('email', e.target.value)}
                                    error={!!errors.email}
                                    helperText={errors.email}
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <EmailIcon />
                                            </InputAdornment>
                                        )
                                    }}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Prénom"
                                    value={formData.first_name}
                                    onChange={(e) => handleInputChange('first_name', e.target.value)}
                                    error={!!errors.first_name}
                                    helperText={errors.first_name}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Nom"
                                    value={formData.last_name}
                                    onChange={(e) => handleInputChange('last_name', e.target.value)}
                                    error={!!errors.last_name}
                                    helperText={errors.last_name}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Téléphone"
                                    value={formData.phone_number}
                                    onChange={(e) => handleInputChange('phone_number', e.target.value)}
                                    error={!!errors.phone_number}
                                    helperText={errors.phone_number}
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <PhoneIcon />
                                            </InputAdornment>
                                        )
                                    }}
                                />
                            </Grid>

                            <Grid item xs={12} md={6}>
                                <TextField
                                    fullWidth
                                    label="Date de naissance"
                                    type="date"
                                    value={formData.date_of_birth ?
                                        (typeof formData.date_of_birth === 'string' ?
                                            formData.date_of_birth :
                                            formData.date_of_birth.toISOString().split('T')[0]
                                        ) : ''
                                    }
                                    onChange={(e) => handleInputChange('date_of_birth', e.target.value)}
                                    error={!!errors.date_of_birth}
                                    helperText={errors.date_of_birth}
                                    InputLabelProps={{
                                        shrink: true,
                                    }}
                                    InputProps={{
                                        startAdornment: (
                                            <InputAdornment position="start">
                                                <CalendarIcon />
                                            </InputAdornment>
                                        )
                                    }}
                                />
                            </Grid>

                            <Grid item xs={12}>
                                <Box sx={{ position: 'relative' }}>
                                    <TextField
                                        fullWidth
                                        label="Mot de passe"
                                        type={showPassword ? 'text' : 'password'}
                                        value={formData.password}
                                        onChange={(e) => handleInputChange('password', e.target.value)}
                                        error={!!errors.password}
                                        helperText={errors.password}
                                        InputProps={{
                                            endAdornment: (
                                                <InputAdornment position="end">
                                                    <IconButton
                                                        onClick={() => setShowPassword(!showPassword)}
                                                        edge="end"
                                                    >
                                                        {showPassword ? <VisibilityOff /> : <Visibility />}
                                                    </IconButton>
                                                </InputAdornment>
                                            )
                                        }}
                                    />
                                    <Button
                                        variant="outlined"
                                        size="small"
                                        onClick={generateRandomPassword}
                                        sx={{ mt: 1 }}
                                    >
                                        Générer un mot de passe
                                    </Button>
                                </Box>
                            </Grid>

                            <Grid item xs={12}>
                                <Autocomplete
                                    options={divisions}
                                    getOptionLabel={(option) =>
                                        `${option.name}${option.parent ? `, ${option.parent.name}` : ''}`
                                    }
                                    value={formData.administrative_division}
                                    onChange={(event, newValue) => handleInputChange('administrative_division', newValue)}
                                    loading={loadingDivisions}
                                    renderInput={(params) => (
                                        <TextField
                                            {...params}
                                            label="Division administrative (optionnel)"
                                            InputProps={{
                                                ...params.InputProps,
                                                startAdornment: (
                                                    <InputAdornment position="start">
                                                        <LocationIcon />
                                                    </InputAdornment>
                                                ),
                                                endAdornment: (
                                                    <>
                                                        {loadingDivisions ? <CircularProgress size={20} /> : null}
                                                        {params.InputProps.endAdornment}
                                                    </>
                                                )
                                            }}
                                        />
                                    )}
                                />
                            </Grid>

                            <Grid item xs={12}>
                                <TextField
                                    fullWidth
                                    label="Bio (optionnel)"
                                    multiline
                                    rows={3}
                                    value={formData.bio}
                                    onChange={(e) => handleInputChange('bio', e.target.value)}
                                    helperText="Description courte de l'utilisateur"
                                />
                            </Grid>
                        </Grid>
                    </Box>
                );

            case 1:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <SecurityIcon />
                            Rôle et permissions
                        </Typography>

                        <Grid container spacing={3}>
                            <Grid item xs={12}>
                                <FormControl fullWidth>
                                    <InputLabel>Rôle</InputLabel>
                                    <Select
                                        value={formData.role}
                                        label="Rôle"
                                        onChange={(e) => handleInputChange('role', e.target.value)}
                                    >
                                        <MenuItem value="moderator">
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <ModeratorIcon />
                                                Modérateur
                                            </Box>
                                        </MenuItem>
                                        <MenuItem value="admin">
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <AdminIcon />
                                                Administrateur
                                            </Box>
                                        </MenuItem>
                                    </Select>
                                </FormControl>
                            </Grid>

                            {formData.role === 'admin' && (
                                <>
                                    <Grid item xs={12} md={6}>
                                        <FormControl fullWidth>
                                            <InputLabel>Niveau administrateur</InputLabel>
                                            <Select
                                                value={formData.admin_level}
                                                label="Niveau administrateur"
                                                onChange={(e) => handleInputChange('admin_level', e.target.value)}
                                            >
                                                <MenuItem value="system_admin">Administrateur système</MenuItem>
                                                <MenuItem value="content_admin">Administrateur contenu</MenuItem>
                                                <MenuItem value="user_admin">Administrateur utilisateurs</MenuItem>
                                                <MenuItem value="support_admin">Administrateur support</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </Grid>

                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="Département (optionnel)"
                                            value={formData.department}
                                            onChange={(e) => handleInputChange('department', e.target.value)}
                                        />
                                    </Grid>

                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="ID employé (optionnel)"
                                            value={formData.employee_id}
                                            onChange={(e) => handleInputChange('employee_id', e.target.value)}
                                        />
                                    </Grid>

                                    <Grid item xs={12} md={6}>
                                        <TextField
                                            fullWidth
                                            label="Niveau d'accès"
                                            type="number"
                                            inputProps={{ min: 1, max: 10 }}
                                            value={formData.access_level}
                                            onChange={(e) => handleInputChange('access_level', parseInt(e.target.value))}
                                            helperText="1-10 (plus élevé = plus d'accès)"
                                        />
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Permissions administrateur:
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_manage_users}
                                                        onChange={(e) => handleInputChange('can_manage_users', e.target.checked)}
                                                    />
                                                }
                                                label="Gérer les utilisateurs"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_manage_content}
                                                        onChange={(e) => handleInputChange('can_manage_content', e.target.checked)}
                                                    />
                                                }
                                                label="Gérer le contenu"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_view_analytics}
                                                        onChange={(e) => handleInputChange('can_view_analytics', e.target.checked)}
                                                    />
                                                }
                                                label="Voir les analytiques"
                                            />
                                        </Box>
                                    </Grid>
                                </>
                            )}

                            {formData.role === 'moderator' && (
                                <>
                                    <Grid item xs={12} md={6}>
                                        <FormControl fullWidth>
                                            <InputLabel>Niveau modérateur</InputLabel>
                                            <Select
                                                value={formData.moderator_level}
                                                label="Niveau modérateur"
                                                onChange={(e) => handleInputChange('moderator_level', e.target.value)}
                                            >
                                                <MenuItem value="junior">Modérateur junior</MenuItem>
                                                <MenuItem value="senior">Modérateur senior</MenuItem>
                                                <MenuItem value="lead">Modérateur principal</MenuItem>
                                                <MenuItem value="community_mod">Modérateur communauté</MenuItem>
                                                <MenuItem value="content_mod">Modérateur contenu</MenuItem>
                                                <MenuItem value="global_mod">Modérateur global</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </Grid>

                                    <Grid item xs={12} md={6}>
                                        <FormControl fullWidth>
                                            <InputLabel>Spécialisation</InputLabel>
                                            <Select
                                                value={formData.specialization}
                                                label="Spécialisation"
                                                onChange={(e) => handleInputChange('specialization', e.target.value)}
                                            >
                                                <MenuItem value="general">Modération générale</MenuItem>
                                                <MenuItem value="content">Modération contenu</MenuItem>
                                                <MenuItem value="community">Gestion communauté</MenuItem>
                                                <MenuItem value="spam">Détection spam</MenuItem>
                                                <MenuItem value="safety">Sécurité et confiance</MenuItem>
                                            </Select>
                                        </FormControl>
                                    </Grid>

                                    <Grid item xs={12}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Permissions modérateur:
                                        </Typography>
                                        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_remove_posts}
                                                        onChange={(e) => handleInputChange('can_remove_posts', e.target.checked)}
                                                    />
                                                }
                                                label="Supprimer les posts"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_remove_comments}
                                                        onChange={(e) => handleInputChange('can_remove_comments', e.target.checked)}
                                                    />
                                                }
                                                label="Supprimer les commentaires"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_ban_users}
                                                        onChange={(e) => handleInputChange('can_ban_users', e.target.checked)}
                                                    />
                                                }
                                                label="Bannir les utilisateurs"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_suspend_users}
                                                        onChange={(e) => handleInputChange('can_suspend_users', e.target.checked)}
                                                    />
                                                }
                                                label="Suspendre les utilisateurs"
                                            />
                                            <FormControlLabel
                                                control={
                                                    <Checkbox
                                                        checked={formData.can_manage_reports}
                                                        onChange={(e) => handleInputChange('can_manage_reports', e.target.checked)}
                                                    />
                                                }
                                                label="Gérer les signalements"
                                            />
                                        </Box>
                                    </Grid>
                                </>
                            )}

                            <Grid item xs={12}>
                                <Divider sx={{ my: 2 }} />
                                <FormControlLabel
                                    control={
                                        <Checkbox
                                            checked={formData.send_welcome_email}
                                            onChange={(e) => handleInputChange('send_welcome_email', e.target.checked)}
                                        />
                                    }
                                    label="Envoyer un email de bienvenue"
                                />
                            </Grid>
                        </Grid>
                    </Box>
                );

            case 2:
                return (
                    <Box>
                        <Typography variant="h6" gutterBottom>
                            Confirmation de création
                        </Typography>

                        <Card sx={{ mb: 3 }}>
                            <CardContent>
                                <Typography variant="subtitle1" gutterBottom>
                                    Informations utilisateur:
                                </Typography>
                                <Grid container spacing={2}>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Nom d'utilisateur:</strong> {formData.username}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Email:</strong> {formData.email}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Nom complet:</strong> {formData.first_name} {formData.last_name}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={6}>
                                        <Typography variant="body2">
                                            <strong>Téléphone:</strong> {formData.phone_number}
                                        </Typography>
                                    </Grid>
                                    <Grid item xs={12}>
                                        <Box display="flex" alignItems="center" gap={1}>
                                            <Typography variant="body2" component="span">
                                                <strong>Rôle:</strong>
                                            </Typography>
                                            <Chip
                                                label={formData.role === 'admin' ? 'Administrateur' : 'Modérateur'}
                                                color={formData.role === 'admin' ? 'primary' : 'secondary'}
                                                size="small"
                                            />
                                        </Box>
                                    </Grid>
                                </Grid>
                            </CardContent>
                        </Card>

                        {formData.role === 'admin' && (
                            <Card sx={{ mb: 3 }}>
                                <CardContent>
                                    <Typography variant="subtitle1" gutterBottom>
                                        Configuration administrateur:
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Niveau:</strong> {formData.admin_level}
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Niveau d'accès:</strong> {formData.access_level}/10
                                    </Typography>
                                    {formData.department && (
                                        <Typography variant="body2">
                                            <strong>Département:</strong> {formData.department}
                                        </Typography>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        {formData.role === 'moderator' && (
                            <Card sx={{ mb: 3 }}>
                                <CardContent>
                                    <Typography variant="subtitle1" gutterBottom>
                                        Configuration modérateur:
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Niveau:</strong> {formData.moderator_level}
                                    </Typography>
                                    <Typography variant="body2">
                                        <strong>Spécialisation:</strong> {formData.specialization}
                                    </Typography>
                                </CardContent>
                            </Card>
                        )}

                        <Alert severity="info">
                            L'utilisateur sera créé avec les informations ci-dessus.
                            {formData.send_welcome_email && ' Un email de bienvenue sera envoyé.'}
                        </Alert>
                    </Box>
                );

            default:
                return null;
        }
    };

    return (
        <AdminLayout activeSection="user-creation">
            <Container maxWidth="lg" sx={{ py: 4 }}>
                <Paper sx={{ p: 4 }}>
                    <Typography variant="h4" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <PersonIcon />
                        Créer un utilisateur Admin/Modérateur
                    </Typography>

                    {alert.show && (
                        <Alert
                            severity={alert.type}
                            sx={{ mb: 3 }}
                            onClose={() => setAlert({ ...alert, show: false })}
                        >
                            {alert.message}
                        </Alert>
                    )}

                    <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
                        {steps.map((label) => (
                            <Step key={label}>
                                <StepLabel>{label}</StepLabel>
                            </Step>
                        ))}
                    </Stepper>

                    <Box sx={{ minHeight: '400px', mb: 4 }}>
                        {renderStepContent(activeStep)}
                    </Box>

                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Button
                            disabled={activeStep === 0}
                            onClick={handleBack}
                            startIcon={<CancelIcon />}
                        >
                            Retour
                        </Button>

                        <Box sx={{ display: 'flex', gap: 2 }}>
                            {activeStep === steps.length - 1 ? (
                                <Button
                                    variant="contained"
                                    onClick={handleSubmit}
                                    disabled={loading}
                                    startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                                >
                                    {loading ? 'Création...' : 'Créer l\'utilisateur'}
                                </Button>
                            ) : (
                                <Button
                                    variant="contained"
                                    onClick={handleNext}
                                >
                                    Suivant
                                </Button>
                            )}
                        </Box>
                    </Box>
                </Paper>
            </Container>
        </AdminLayout>
    );
};

export default UserCreation;