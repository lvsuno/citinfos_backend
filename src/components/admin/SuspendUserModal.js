import React, { useState } from 'react';
import {
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Button,
    Typography,
    Alert,
    Box,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Checkbox,
    FormControlLabel
} from '@mui/material';
import { Warning as WarningIcon } from '@mui/icons-material';

const SuspendUserModal = ({ open, onClose, onConfirm, user, loading = false }) => {
    const [formData, setFormData] = useState({
        reason: '',
        details: '',
        duration: 'indefinite',
        notifyUser: true
    });
    const [errors, setErrors] = useState({});

    const suspensionReasons = [
        'Violation des conditions d\'utilisation',
        'Contenu inapproprié',
        'Harcèlement ou intimidation',
        'Spam ou comportement abusif',
        'Fausse identité',
        'Activité suspecte',
        'Violation de la propriété intellectuelle',
        'Autre'
    ];

    const durationOptions = [
        { value: 'indefinite', label: 'Indéfinie' },
        { value: '1', label: '1 jour' },
        { value: '3', label: '3 jours' },
        { value: '7', label: '7 jours' },
        { value: '14', label: '14 jours' },
        { value: '30', label: '30 jours' }
    ];

    const handleChange = (field) => (event) => {
        setFormData(prev => ({
            ...prev,
            [field]: event.target.value
        }));

        // Effacer l'erreur pour ce champ
        if (errors[field]) {
            setErrors(prev => ({
                ...prev,
                [field]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.reason.trim()) {
            newErrors.reason = 'La raison de la suspension est obligatoire';
        }

        if (!formData.details.trim()) {
            newErrors.details = 'Les détails de la suspension sont obligatoires';
        } else if (formData.details.trim().length < 10) {
            newErrors.details = 'Les détails doivent contenir au moins 10 caractères';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = () => {
        if (validateForm()) {
            onConfirm(formData);
        }
    };

    const handleClose = () => {
        if (!loading) {
            setFormData({
                reason: '',
                details: '',
                duration: 'indefinite',
                notifyUser: true
            });
            setErrors({});
            onClose();
        }
    };

    return (
        <Dialog
            open={open}
            onClose={handleClose}
            maxWidth="md"
            fullWidth
            PaperProps={{
                sx: { borderRadius: 2 }
            }}
        >
            <DialogTitle sx={{ pb: 1 }}>
                <Box display="flex" alignItems="center" gap={1}>
                    <WarningIcon color="error" />
                    <Typography variant="h6" component="span">
                        Suspendre l'utilisateur
                    </Typography>
                </Box>
            </DialogTitle>

            <DialogContent>
                {user && (
                    <Alert severity="warning" sx={{ mb: 3 }}>
                        <Typography variant="body2">
                            Vous êtes sur le point de suspendre <strong>{user.full_name || user.username}</strong>.
                            Cette action empêchera l'utilisateur d'accéder à son compte et il recevra un email de notification.
                        </Typography>
                    </Alert>
                )}

                <Box display="flex" flexDirection="column" gap={3}>
                    {/* Raison de la suspension */}
                    <FormControl fullWidth error={!!errors.reason}>
                        <InputLabel>Raison de la suspension</InputLabel>
                        <Select
                            value={formData.reason}
                            onChange={handleChange('reason')}
                            label="Raison de la suspension"
                        >
                            {suspensionReasons.map((reason) => (
                                <MenuItem key={reason} value={reason}>
                                    {reason}
                                </MenuItem>
                            ))}
                        </Select>
                        {errors.reason && (
                            <Typography variant="caption" color="error" sx={{ mt: 0.5 }}>
                                {errors.reason}
                            </Typography>
                        )}
                    </FormControl>

                    {/* Durée de la suspension */}
                    <FormControl fullWidth>
                        <InputLabel>Durée de la suspension</InputLabel>
                        <Select
                            value={formData.duration}
                            onChange={handleChange('duration')}
                            label="Durée de la suspension"
                        >
                            {durationOptions.map((option) => (
                                <MenuItem key={option.value} value={option.value}>
                                    {option.label}
                                </MenuItem>
                            ))}
                        </Select>
                    </FormControl>

                    {/* Détails de la suspension */}
                    <TextField
                        label="Détails et explications"
                        multiline
                        rows={4}
                        fullWidth
                        value={formData.details}
                        onChange={handleChange('details')}
                        error={!!errors.details}
                        helperText={errors.details || 'Expliquez en détail les raisons de cette suspension'}
                        placeholder="Décrivez précisément les actions ou comportements qui ont motivé cette suspension..."
                    />

                    {/* Options supplémentaires */}
                    <Box>
                        <Typography variant="subtitle2" gutterBottom>
                            Options
                        </Typography>
                        <FormControlLabel
                            control={
                                <Checkbox
                                    checked={formData.notifyUser}
                                    onChange={(e) => setFormData(prev => ({ ...prev, notifyUser: e.target.checked }))}
                                    color="primary"
                                />
                            }
                            label="Notifier l'utilisateur par email"
                        />
                    </Box>
                </Box>
            </DialogContent>

            <DialogActions sx={{ p: 3, pt: 1 }}>
                <Button
                    onClick={handleClose}
                    disabled={loading}
                    color="inherit"
                >
                    Annuler
                </Button>
                <Button
                    onClick={handleSubmit}
                    variant="contained"
                    color="error"
                    disabled={loading || !formData.reason.trim() || !formData.details.trim()}
                >
                    {loading ? 'Suspension...' : 'Suspendre l\'utilisateur'}
                </Button>
            </DialogActions>
        </Dialog>
    );
};

export default SuspendUserModal;