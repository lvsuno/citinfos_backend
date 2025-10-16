import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Alert,
    Divider,
    Paper,
    Container
} from '@mui/material';
import {
    Block as BlockIcon,
    Email as EmailIcon,
    Info as InfoIcon,
    Home as HomeIcon
} from '@mui/icons-material';
import { format } from 'date-fns';
import { fr } from 'date-fns/locale';

const AccountSuspended = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // Récupérer les données de suspension depuis l'état de navigation ou localStorage
    const suspensionData = location.state?.suspensionData ||
        JSON.parse(localStorage.getItem('suspensionData') || '{}');

    const handleGoHome = () => {
        // Nettoyer les données de suspension et rediriger vers l'accueil
        localStorage.removeItem('suspensionData');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        navigate('/');
    };

    const handleContactSupport = () => {
        const subject = encodeURIComponent(`Contestation suspension - ${suspensionData.username || 'Utilisateur'}`);
        const body = encodeURIComponent(`
Bonjour,

Je souhaite contester la suspension de mon compte.

Informations de mon compte :
- Email : ${suspensionData.email || 'Non disponible'}
- Date de suspension : ${suspensionData.suspended_at ? format(new Date(suspensionData.suspended_at), 'dd MMMM yyyy à HH:mm', { locale: fr }) : 'Non disponible'}
- Raison indiquée : ${suspensionData.suspension_reason || 'Non spécifiée'}

Merci de bien vouloir examiner mon cas.

Cordialement,
        `);

        window.open(`mailto:support@citinfos.com?subject=${subject}&body=${body}`, '_blank');
    };

    return (
        <Container maxWidth="md" sx={{ py: 4 }}>
            <Box display="flex" flexDirection="column" alignItems="center" gap={3}>
                {/* Icône principale */}
                <Box
                    sx={{
                        width: 100,
                        height: 100,
                        borderRadius: '50%',
                        bgcolor: 'error.light',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        mb: 2
                    }}
                >
                    <BlockIcon sx={{ fontSize: 60, color: 'error.contrastText' }} />
                </Box>

                {/* Titre principal */}
                <Typography variant="h3" component="h1" textAlign="center" color="error.main">
                    Compte Suspendu
                </Typography>

                {/* Carte principale */}
                <Card sx={{ width: '100%', maxWidth: 600 }}>
                    <CardContent sx={{ p: 4 }}>
                        <Alert severity="error" sx={{ mb: 3 }}>
                            <Typography variant="body1">
                                Votre compte a été temporairement suspendu par un administrateur.
                            </Typography>
                        </Alert>

                        <Typography variant="body1" paragraph>
                            Nous vous informons que votre accès à la plateforme CitInfos a été temporairement restreint.
                        </Typography>

                        {/* Informations de suspension */}
                        {suspensionData.email && (
                            <>
                                <Divider sx={{ my: 3 }} />
                                <Typography variant="h6" gutterBottom>
                                    <InfoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                                    Informations sur la suspension
                                </Typography>

                                <Box sx={{ pl: 4 }}>
                                    {suspensionData.email && (
                                        <Typography variant="body2" paragraph>
                                            <strong>Email du compte :</strong> {suspensionData.email}
                                        </Typography>
                                    )}

                                    {suspensionData.suspended_at && (
                                        <Typography variant="body2" paragraph>
                                            <strong>Date de suspension :</strong>{' '}
                                            {format(new Date(suspensionData.suspended_at), 'dd MMMM yyyy à HH:mm', { locale: fr })}
                                        </Typography>
                                    )}

                                    {suspensionData.suspension_reason && (
                                        <Paper variant="outlined" sx={{ p: 2, bgcolor: 'grey.50' }}>
                                            <Typography variant="subtitle2" gutterBottom>
                                                Raison de la suspension :
                                            </Typography>
                                            <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                                                {suspensionData.suspension_reason}
                                            </Typography>
                                        </Paper>
                                    )}
                                </Box>
                            </>
                        )}

                        <Divider sx={{ my: 3 }} />

                        {/* Section email de notification */}
                        <Alert severity="info" sx={{ mb: 3 }}>
                            <Box display="flex" alignItems="center" gap={1}>
                                <EmailIcon />
                                <Typography variant="body2">
                                    Un email de notification détaillé a été envoyé à votre adresse{' '}
                                    {suspensionData.email && <strong>{suspensionData.email}</strong>}
                                </Typography>
                            </Box>
                        </Alert>

                        {/* Que faire maintenant */}
                        <Typography variant="h6" gutterBottom>
                            Que faire maintenant ?
                        </Typography>

                        <Box component="ul" sx={{ pl: 2, color: 'text.secondary' }}>
                            <li>
                                <Typography variant="body2" paragraph>
                                    <strong>Vérifiez vos emails :</strong> Consultez votre boîte de réception pour plus de détails sur la suspension.
                                </Typography>
                            </li>
                            <li>
                                <Typography variant="body2" paragraph>
                                    <strong>Contactez le support :</strong> Si vous pensez qu'il s'agit d'une erreur, vous pouvez contester cette décision.
                                </Typography>
                            </li>
                            <li>
                                <Typography variant="body2" paragraph>
                                    <strong>Respectez les règles :</strong> Assurez-vous de bien comprendre nos conditions d'utilisation pour éviter de futures suspensions.
                                </Typography>
                            </li>
                        </Box>

                        {/* Actions */}
                        <Box display="flex" gap={2} mt={4} flexWrap="wrap">
                            <Button
                                variant="contained"
                                color="primary"
                                onClick={handleContactSupport}
                                startIcon={<EmailIcon />}
                            >
                                Contacter le support
                            </Button>

                            <Button
                                variant="outlined"
                                onClick={handleGoHome}
                                startIcon={<HomeIcon />}
                            >
                                Retour à l'accueil
                            </Button>
                        </Box>
                    </CardContent>
                </Card>

                {/* Note importante */}
                <Alert severity="warning" sx={{ maxWidth: 600 }}>
                    <Typography variant="body2">
                        <strong>Important :</strong> Toute tentative de contournement de cette suspension pourrait
                        entraîner une fermeture définitive de votre compte.
                    </Typography>
                </Alert>
            </Box>
        </Container>
    );
};

export default AccountSuspended;