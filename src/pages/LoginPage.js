import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Container, Row, Col, Form, Button, Alert } from 'react-bootstrap';
import {
    Email as EmailIcon,
    Lock as LockIcon,
    Visibility as VisibilityIcon,
    VisibilityOff as VisibilityOffIcon,
    ArrowForwardOutlined,
    AutoAwesomeOutlined,
    LoginOutlined
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { getUserRedirectUrl, getMunicipalityBySlug } from '../data/municipalitiesUtils';
import { getSmartRedirectUrl, shouldRedirectFromUrl } from '../utils/navigationTracker';
import styles from './LoginPage.module.css';

const LoginPage = () => {
    const navigate = useNavigate();
    const { login } = useAuth();
    const [formData, setFormData] = useState({
        usernameOrEmail: '',
        password: '',
        rememberMe: false
    });
    const [showPassword, setShowPassword] = useState(false);
    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [isVisible, setIsVisible] = useState(false);
    const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

    useEffect(() => {
        setIsVisible(true);

        const handleMouseMove = (e) => {
            setMousePosition({
                x: (e.clientX / window.innerWidth) * 100,
                y: (e.clientY / window.innerHeight) * 100
            });
        };

        window.addEventListener('mousemove', handleMouseMove);
        return () => window.removeEventListener('mousemove', handleMouseMove);
    }, []);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;

        // Handle checkbox inputs differently
        const inputValue = type === 'checkbox' ? checked : value;

        // Debug log for checkbox changes
        if (type === 'checkbox') {
            console.log(`Checkbox ${name} changed to:`, inputValue);
        }

        setFormData(prev => ({
            ...prev,
            [name]: inputValue
        }));

        // Clear errors when user starts typing
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    const validateForm = () => {
        const newErrors = {};

        if (!formData.usernameOrEmail) {
            newErrors.usernameOrEmail = 'Nom d\'utilisateur ou email requis';
        }

        if (!formData.password) {
            newErrors.password = 'Le mot de passe est requis';
        } else if (formData.password.length < 6) {
            newErrors.password = 'Le mot de passe doit contenir au moins 6 caractères';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!validateForm()) return;

        setIsLoading(true);

        try {
            console.log('Login attempt with rememberMe:', formData.rememberMe);
            const result = await login(formData.usernameOrEmail, formData.password, formData.rememberMe);
            if (result.success) {
                // Always redirect to success page first (session is created)
                console.log('🔍 DEBUG: User data received from server:', result.user);
                console.log('🔍 DEBUG: user.location:', result.user?.location);
                console.log('🔍 DEBUG: user.municipality:', result.user?.municipality);
                console.log('🔍 DEBUG: user.profile:', result.user?.profile);
                console.log('🔍 DEBUG: Full user object keys:', Object.keys(result.user || {}));
                console.log('🔍 DEBUG: Session data:', result.session);

                // Get user's home division URL (fallback/default)
                const userHomeUrl = getUserRedirectUrl(result.user);
                console.log('🔍 DEBUG: User home URL:', userHomeUrl);

                // Check if backend provided last visited URL from previous session
                let redirectUrl;
                let reason;
                
                if (result.session?.last_visited_url) {
                    const lastVisitedTime = result.session.last_visited_time;
                    const timeSinceVisit = lastVisitedTime 
                        ? (Date.now() - new Date(lastVisitedTime).getTime()) / 1000 / 60  // minutes
                        : null;
                    
                    // If session was recent (< 30 min), use last visited URL
                    if (timeSinceVisit !== null && timeSinceVisit < 30) {
                        redirectUrl = result.session.last_visited_url;
                        reason = `Backend session: last visit ${timeSinceVisit.toFixed(1)} min ago`;
                        console.log('✅ Using last visited URL from backend session:', redirectUrl);
                    } else {
                        redirectUrl = userHomeUrl;
                        reason = `Backend session: old visit (${timeSinceVisit?.toFixed(1) || 'unknown'} min ago)`;
                        console.log('⏰ Session too old, going to home division');
                    }
                } else {
                    // Fallback to localStorage-based smart redirect if no backend data
                    const smartRedirect = getSmartRedirectUrl(userHomeUrl);
                    redirectUrl = smartRedirect.url;
                    reason = `LocalStorage fallback: ${smartRedirect.reason}`;
                    console.log('📦 No backend session data, using localStorage');
                }
                
                console.log('🎯 Smart redirect decision:', { redirectUrl, reason });

                // Validate that the municipality route exists before redirecting
                if (redirectUrl !== '/dashboard') {
                    const urlParts = redirectUrl.split('/');
                    if (urlParts.length >= 3) {
                        const municipalitySlug = urlParts[2];
                        console.log('🔍 DEBUG: Municipality slug to validate:', municipalitySlug);

                        // Check if this municipality exists in our data
                        const municipalityExists = getMunicipalityBySlug(municipalitySlug);
                        console.log('🔍 DEBUG: Municipality exists:', !!municipalityExists);

                        if (!municipalityExists) {
                            console.warn('⚠️ Municipality not found in data, falling back to dashboard');
                            navigate('/dashboard');
                            return;
                        }
                    }
                }

                // Pass verification info if needed
                if (result.verification_required) {
                    navigate(redirectUrl, {
                        state: {
                            showVerificationModal: true,
                            verificationMessage: result.verification_message || result.message
                        }
                    });
                } else {
                    navigate(redirectUrl);
                }
            } else {
                setErrors({ submit: result.error || 'Email ou mot de passe incorrect' });
            }
        } catch (error) {
            setErrors({ submit: 'Erreur lors de la connexion' });
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.loginPage}>
            {/* Arrière-plan animé */}
            <div
                className={styles.animatedBackground}
                style={{
                    background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(6, 182, 212, 0.1) 0%, rgba(132, 204, 22, 0.05) 50%, transparent 100%)`
                }}
            />

            {/* Particules flottantes */}
            <div className={styles.particles}>
                {[...Array(15)].map((_, i) => (
                    <div
                        key={i}
                        className={styles.particle}
                        style={{
                            left: `${Math.random() * 100}%`,
                            animationDelay: `${Math.random() * 20}s`,
                            animationDuration: `${15 + Math.random() * 10}s`
                        }}
                    />
                ))}
            </div>

            <Container className="h-100">
                <Row className="h-100 align-items-center justify-content-center">
                    <Col lg={5} md={7} sm={9}>
                        <div className={`${styles.loginCard} ${isVisible ? styles.visible : ''}`}>
                            {/* Header */}
                            <div className={styles.cardHeader}>
                                <div className={styles.welcomeBadge}>
                                    <LoginOutlined className={styles.badgeIcon} />
                                    <span>Bon retour !</span>
                                </div>
                                <h1 className={styles.cardTitle}>
                                    Connectez-vous à votre
                                    <span className={styles.gradientText}> communauté</span>
                                </h1>
                                <p className={styles.cardSubtitle}>
                                    Retrouvez votre espace personnel et participez à la vie locale
                                </p>
                            </div>

                            {/* Formulaire */}
                            <Form onSubmit={handleSubmit} className={styles.loginForm}>
                                {errors.submit && (
                                    <Alert variant="danger" className={styles.errorAlert}>
                                        {errors.submit}
                                    </Alert>
                                )}

                                {/* Nom d'utilisateur ou Email */}
                                <div className={styles.inputGroup}>
                                    <div className={styles.inputWrapper}>
                                        <EmailIcon className={styles.inputIcon} />
                                        <Form.Control
                                            type="text"
                                            name="usernameOrEmail"
                                            placeholder="Nom d'utilisateur ou email"
                                            value={formData.usernameOrEmail}
                                            onChange={handleChange}
                                            className={`${styles.formInput} ${errors.usernameOrEmail ? styles.error : ''}`}
                                            autoComplete="username"
                                        />
                                    </div>
                                    {errors.usernameOrEmail && <div className={styles.errorText}>{errors.usernameOrEmail}</div>}
                                </div>

                                {/* Mot de passe */}
                                <div className={styles.inputGroup}>
                                    <div className={styles.inputWrapper}>
                                        <LockIcon className={styles.inputIcon} />
                                        <Form.Control
                                            type={showPassword ? 'text' : 'password'}
                                            name="password"
                                            placeholder="Votre mot de passe"
                                            value={formData.password}
                                            onChange={handleChange}
                                            className={`${styles.formInput} ${errors.password ? styles.error : ''}`}
                                            autoComplete="current-password"
                                        />
                                        <button
                                            type="button"
                                            className={styles.passwordToggle}
                                            onClick={() => setShowPassword(!showPassword)}
                                        >
                                            {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                        </button>
                                    </div>
                                    {errors.password && <div className={styles.errorText}>{errors.password}</div>}
                                </div>

                                {/* Options */}
                                <div className={styles.formOptions}>
                                    <Form.Check
                                        type="checkbox"
                                        id="remember-me"
                                        name="rememberMe"
                                        label="Se souvenir de moi"
                                        checked={formData.rememberMe}
                                        onChange={handleChange}
                                        className={styles.customCheckbox}
                                    />
                                    <Link to="/forgot-password" className={styles.forgotLink}>
                                        Mot de passe oublié ?
                                    </Link>
                                </div>

                                {/* Bouton de connexion */}
                                <Button
                                    type="submit"
                                    className={styles.loginButton}
                                    disabled={isLoading}
                                    size="lg"
                                >
                                    {isLoading ? (
                                        <div className={styles.loadingSpinner} />
                                    ) : (
                                        <>
                                            <span>Se connecter</span>
                                            <ArrowForwardOutlined className={styles.buttonIcon} />
                                        </>
                                    )}
                                </Button>

                                {/* Divider */}
                                <div className={styles.divider}>
                                    <span>ou</span>
                                </div>

                                {/* Lien inscription */}
                                <div className={styles.signupLink}>
                                    <span>Pas encore de compte ? </span>
                                    <Link to="/signup" className={styles.link}>
                                        Créer un compte
                                        <AutoAwesomeOutlined className={styles.linkIcon} />
                                    </Link>
                                </div>
                            </Form>
                        </div>
                    </Col>
                </Row>
            </Container>

            {/* Retour à l'accueil */}
            <Link to="/" className={styles.backToHome}>
                ← Retour à l'accueil
            </Link>
        </div>
    );
};

export default LoginPage;