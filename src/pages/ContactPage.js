import React, { useState } from 'react';
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
    Alert,
    CircularProgress,
    Grid,
    Card,
    CardContent
} from '@mui/material';
import {
    Email as EmailIcon,
    Phone as PhoneIcon,
    LocationOn as LocationIcon,
    Send as SendIcon,
    Support as SupportIcon,
    CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/apiService';

const ContactPage = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        subject: '',
        message: '',
        category: 'other'
    });
    const [submitting, setSubmitting] = useState(false);
    const [success, setSuccess] = useState(false);
    const [error, setError] = useState('');
    const [ticketNumber, setTicketNumber] = useState('');

    const categories = [
        { value: 'technical', label: 'Problème technique' },
        { value: 'account', label: 'Problème de compte' },
        { value: 'billing', label: 'Question de facturation' },
        { value: 'feature_request', label: 'Demande de fonctionnalité' },
        { value: 'report', label: 'Signalement' },
        { value: 'other', label: 'Autre' }
    ];

    const handleInputChange = (field, value) => {
        setFormData(prev => ({
            ...prev,
            [field]: value
        }));
        // Clear errors when user starts typing
        if (error) setError('');
    };

    const validateForm = () => {
        const { name, email, subject, message } = formData;
        
        if (!name.trim()) {
            setError('Le nom est requis');
            return false;
        }
        
        if (!email.trim()) {
            setError('L\'email est requis');
            return false;
        }
        
        // Basic email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            setError('Format d\'email invalide');
            return false;
        }
        
        if (!subject.trim()) {
            setError('Le sujet est requis');
            return false;
        }
        
        if (!message.trim()) {
            setError('Le message est requis');
            return false;
        }
        
        if (message.trim().length < 10) {
            setError('Le message doit contenir au moins 10 caractères');
            return false;
        }
        
        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) return;

        try {
            setSubmitting(true);
            setError('');
            
            const response = await apiService.post('/api/public/support/create-ticket/', formData);
            
            setSuccess(true);
            setTicketNumber(response.data.ticket_number);
            
            // Reset form
            setFormData({
                name: '',
                email: '',
                subject: '',
                message: '',
                category: 'other'
            });
            
        } catch (err) {
            console.error('Erreur lors de l\'envoi:', err);
            const errorMessage = err.response?.data?.error || 'Une erreur est survenue lors de l\'envoi de votre message';
            setError(errorMessage);
        } finally {
            setSubmitting(false);
        }
    };

    if (success) {
        return (
            <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50', py: 8 }}>
                <Container maxWidth="md">
                    <Paper sx={{ p: 4, textAlign: 'center' }}>
                        <CheckCircleIcon sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                        <Typography variant="h4" gutterBottom>
                            Demande envoyée avec succès !
                        </Typography>
                        <Typography variant="body1" color="text.secondary" paragraph>
                            Votre demande de support a été créée avec le numéro <strong>#{ticketNumber}</strong>.
                        </Typography>
                        <Typography variant="body2" color="text.secondary" paragraph>
                            Notre équipe vous répondra dans les plus brefs délais à l'adresse email fournie.
                            Vous pouvez conserver ce numéro de ticket pour référence.
                        </Typography>
                        <Box mt={3}>
                            <Button
                                variant="contained"
                                onClick={() => navigate('/')}
                                sx={{ mr: 2 }}
                            >
                                Retour à l'accueil
                            </Button>
                            <Button
                                variant="outlined"
                                onClick={() => {
                                    setSuccess(false);
                                    setTicketNumber('');
                                }}
                            >
                                Envoyer une autre demande
                            </Button>
                        </Box>
                    </Paper>
                </Container>
            </Box>
        );
    }

    return (
        <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50', py: 8 }}>
            <Container maxWidth="lg">
                <Box textAlign="center" mb={6}>
                    <Typography variant="h3" component="h1" gutterBottom>
                        Contactez-nous
                    </Typography>
                    <Typography variant="h6" color="text.secondary">
                        Notre équipe est là pour vous aider
                    </Typography>
                </Box>

                <Grid container spacing={4}>
                    {/* Contact Information */}
                    <Grid item xs={12} md={4}>
                        <Card sx={{ height: '100%' }}>
                            <CardContent>
                                <Typography variant="h6" gutterBottom>
                                    Informations de contact
                                </Typography>
                                
                                <Box display="flex" alignItems="center" mb={2}>
                                    <EmailIcon sx={{ mr: 2, color: 'primary.main' }} />
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Email
                                        </Typography>
                                        <Typography variant="body1">
                                            support@citinfos.com
                                        </Typography>
                                    </Box>
                                </Box>
                                
                                <Box display="flex" alignItems="center" mb={2}>
                                    <PhoneIcon sx={{ mr: 2, color: 'primary.main' }} />
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Téléphone
                                        </Typography>
                                        <Typography variant="body1">
                                            +1 (555) 123-4567
                                        </Typography>
                                    </Box>
                                </Box>
                                
                                <Box display="flex" alignItems="center" mb={3}>
                                    <LocationIcon sx={{ mr: 2, color: 'primary.main' }} />
                                    <Box>
                                        <Typography variant="body2" color="text.secondary">
                                            Adresse
                                        </Typography>
                                        <Typography variant="body1">
                                            Sherbrooke, QC, Canada
                                        </Typography>
                                    </Box>
                                </Box>
                                
                                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                                    Heures d'ouverture
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                    Lundi - Vendredi: 9h00 - 17h00<br />
                                    Samedi - Dimanche: 10h00 - 16h00
                                </Typography>
                            </CardContent>
                        </Card>
                    </Grid>

                    {/* Contact Form */}
                    <Grid item xs={12} md={8}>
                        <Paper sx={{ p: 4 }}>
                            <Box display="flex" alignItems="center" mb={3}>
                                <SupportIcon sx={{ mr: 2, color: 'primary.main' }} />
                                <Typography variant="h5">
                                    Envoyez-nous un message
                                </Typography>
                            </Box>

                            {error && (
                                <Alert severity="error" sx={{ mb: 3 }}>
                                    {error}
                                </Alert>
                            )}

                            <form onSubmit={handleSubmit}>
                                <Grid container spacing={3}>
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Nom complet"
                                            value={formData.name}
                                            onChange={(e) => handleInputChange('name', e.target.value)}
                                            required
                                            disabled={submitting}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12} sm={6}>
                                        <TextField
                                            fullWidth
                                            label="Adresse email"
                                            type="email"
                                            value={formData.email}
                                            onChange={(e) => handleInputChange('email', e.target.value)}
                                            required
                                            disabled={submitting}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12}>
                                        <FormControl fullWidth>
                                            <InputLabel>Catégorie</InputLabel>
                                            <Select
                                                value={formData.category}
                                                onChange={(e) => handleInputChange('category', e.target.value)}
                                                label="Catégorie"
                                                disabled={submitting}
                                            >
                                                {categories.map((category) => (
                                                    <MenuItem key={category.value} value={category.value}>
                                                        {category.label}
                                                    </MenuItem>
                                                ))}
                                            </Select>
                                        </FormControl>
                                    </Grid>
                                    
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Sujet"
                                            value={formData.subject}
                                            onChange={(e) => handleInputChange('subject', e.target.value)}
                                            required
                                            disabled={submitting}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12}>
                                        <TextField
                                            fullWidth
                                            label="Message"
                                            multiline
                                            rows={6}
                                            value={formData.message}
                                            onChange={(e) => handleInputChange('message', e.target.value)}
                                            required
                                            disabled={submitting}
                                            placeholder="Décrivez votre problème ou votre question en détail..."
                                            helperText={`${formData.message.length} caractères (minimum 10)`}
                                        />
                                    </Grid>
                                    
                                    <Grid item xs={12}>
                                        <Button
                                            type="submit"
                                            variant="contained"
                                            size="large"
                                            startIcon={submitting ? <CircularProgress size={20} /> : <SendIcon />}
                                            disabled={submitting}
                                            fullWidth
                                            sx={{ mt: 2 }}
                                        >
                                            {submitting ? 'Envoi en cours...' : 'Envoyer le message'}
                                        </Button>
                                    </Grid>
                                </Grid>
                            </form>
                        </Paper>
                    </Grid>
                </Grid>
            </Container>
        </Box>
    );
};

export default ContactPage;