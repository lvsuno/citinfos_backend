import React, { useState, useEffect, useRef } from 'react';
import { Container, Row, Col, Form, Button, Alert, Card } from 'react-bootstrap';
import { Link, useNavigate } from 'react-router-dom';
import {
  PersonAdd as PersonAddIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  ArrowForward as ArrowForwardIcon,
  Home as HomeIcon,
  Email as EmailIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useMunicipality } from '../contexts/MunicipalityContext';
import MunicipalitySelector from '../components/MunicipalitySelector';
import styles from './SignUpPage.module.css';

const SignUpPage = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirmPassword: '',
    municipality: '',
    birthDate: '',
    acceptTerms: false
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isVisible, setIsVisible] = useState(false);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const { signUp } = useAuth();
  const { getMunicipalitySlug } = useMunicipality();
  const navigate = useNavigate();
  const backgroundRef = useRef(null);
  const particlesRef = useRef([]);

  useEffect(() => {
    setIsVisible(true);
    initializeParticles();

    return () => {
      // Cleanup des particules si nécessaire
      if (particlesRef.current) {
        particlesRef.current = [];
      }
    };
  }, []);

  const initializeParticles = () => {
    const particles = [];
    for (let i = 0; i < 15; i++) {
      particles.push({
        id: i,
        x: Math.random() * 100,
        y: Math.random() * 100,
        size: Math.random() * 3 + 1,
        speedX: (Math.random() - 0.5) * 0.5,
        speedY: (Math.random() - 0.5) * 0.5,
        duration: Math.random() * 20 + 10
      });
    }
    particlesRef.current = particles;
  };

  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePosition({
      x: ((e.clientX - rect.left) / rect.width) * 100,
      y: ((e.clientY - rect.top) / rect.height) * 100
    });
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = 'Le prénom est requis';
    }

    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Le nom est requis';
    }

    if (!formData.email.trim()) {
      newErrors.email = 'L\'email est requis';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Format d\'email invalide';
    }

    if (!formData.birthDate) {
      newErrors.birthDate = 'La date de naissance est requise';
    } else {
      const birthDate = new Date(formData.birthDate);
      const today = new Date();
      const age = today.getFullYear() - birthDate.getFullYear();
      const monthDiff = today.getMonth() - birthDate.getMonth();

      if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
        age--;
      }

      if (age < 18) {
        newErrors.birthDate = 'Vous devez avoir au moins 18 ans pour vous inscrire';
      }
    }

    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Le mot de passe doit contenir au moins 6 caractères';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'La confirmation du mot de passe est requise';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
    }

    if (!formData.municipality) {
      newErrors.municipality = 'Veuillez sélectionner votre municipalité';
    }

    if (!formData.acceptTerms) {
      newErrors.acceptTerms = 'Vous devez accepter les conditions d\'utilisation';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      await signUp(formData);

      // Rediriger vers le dashboard de la municipalité sélectionnée
      const municipalitySlug = getMunicipalitySlug(formData.municipality);
      navigate(`/municipality/${municipalitySlug}`, { replace: true });
    } catch (error) {
      setErrors({ general: error.message || 'Erreur lors de l\'inscription' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={styles.signupPage} onMouseMove={handleMouseMove}>
      {/* Lien retour à l'accueil */}
      <Link to="/" className={styles.backToHome}>
        <HomeIcon /> Retour à l'accueil
      </Link>

      {/* Arrière-plan animé */}
      <div
        ref={backgroundRef}
        className={styles.animatedBackground}
        style={{
          background: `radial-gradient(circle at ${mousePosition.x}% ${mousePosition.y}%, rgba(6, 182, 212, 0.15) 0%, transparent 50%)`
        }}
      />

      {/* Particules flottantes */}
      <div className={styles.particles}>
        {particlesRef.current.map(particle => (
          <div
            key={particle.id}
            className={styles.particle}
            style={{
              left: `${particle.x}%`,
              top: `${particle.y}%`,
              width: `${particle.size}px`,
              height: `${particle.size}px`,
              animationDuration: `${particle.duration}s`,
              animationDelay: `${particle.id * 0.5}s`
            }}
          />
        ))}
      </div>

      <Container className="position-relative" style={{ zIndex: 10 }}>
        <Row className="justify-content-center">
          <Col lg={6} md={8} sm={10}>
            <Card className={`${styles.signupCard} ${isVisible ? styles.visible : ''}`}>
              <Card.Body>
                {/* Header */}
                <div className={styles.cardHeader}>
                  <div className={styles.welcomeBadge}>
                    <PersonAddIcon className={styles.badgeIcon} />
                    Rejoignez votre communauté
                  </div>
                  <h1 className={styles.cardTitle}>
                    Créer un <span className={styles.gradientText}>compte</span>
                  </h1>
                  <p className={styles.cardSubtitle}>
                    Connectez-vous avec les citoyens de votre municipalité et participez à la vie communautaire
                  </p>
                </div>

                {/* Formulaire */}
                <Form onSubmit={handleSubmit} className={styles.signupForm}>
                  {errors.general && (
                    <Alert variant="danger" className={styles.errorAlert}>
                      {errors.general}
                    </Alert>
                  )}

                  <Row>
                    <Col md={6}>
                      <div className={styles.inputGroup}>
                        <div className={styles.inputWrapper}>
                          <Form.Control
                            type="text"
                            name="firstName"
                            placeholder="Prénom"
                            value={formData.firstName}
                            onChange={handleInputChange}
                            className={`${styles.formInput} ${errors.firstName ? styles.error : ''}`}
                            required
                          />
                          <PersonIcon className={styles.inputIcon} />
                        </div>
                        {errors.firstName && <div className={styles.errorText}>{errors.firstName}</div>}
                      </div>
                    </Col>
                    <Col md={6}>
                      <div className={styles.inputGroup}>
                        <div className={styles.inputWrapper}>
                          <Form.Control
                            type="text"
                            name="lastName"
                            placeholder="Nom"
                            value={formData.lastName}
                            onChange={handleInputChange}
                            className={`${styles.formInput} ${errors.lastName ? styles.error : ''}`}
                            required
                          />
                          <PersonIcon className={styles.inputIcon} />
                        </div>
                        {errors.lastName && <div className={styles.errorText}>{errors.lastName}</div>}
                      </div>
                    </Col>
                  </Row>

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type="email"
                        name="email"
                        placeholder="Adresse email"
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${errors.email ? styles.error : ''}`}
                        required
                      />
                      <EmailIcon className={styles.inputIcon} />
                    </div>
                    {errors.email && <div className={styles.errorText}>{errors.email}</div>}
                  </div>

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type="date"
                        name="birthDate"
                        placeholder="Date de naissance"
                        value={formData.birthDate}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${errors.birthDate ? styles.error : ''}`}
                        required
                        max={new Date(new Date().setFullYear(new Date().getFullYear() - 16)).toISOString().split('T')[0]}
                      />
                      <CalendarIcon className={styles.inputIcon} />
                    </div>
                    {errors.birthDate && <div className={styles.errorText}>{errors.birthDate}</div>}
                    <div className={styles.inputHint}>
                      Vous devez avoir au moins 18 ans pour vous inscrire
                    </div>
                  </div>

                  <div className={styles.inputGroup}>
                    <div className={styles.inputGroup}>
                      <MunicipalitySelector
                        value={formData.municipality}
                        onChange={(municipality) => {
                          setFormData(prev => ({ ...prev, municipality }));
                          setErrors(prev => ({ ...prev, municipality: '' }));
                        }}
                        placeholder="Rechercher votre municipalité..."
                        error={errors.municipality}
                        required
                      />
                    </div>
                    {errors.municipality && <div className={styles.errorText}>{errors.municipality}</div>}
                    {formData.municipality && (
                      <div className={styles.selectedMunicipality}>
                        ✓ Municipalité sélectionnée: <strong>{formData.municipality}</strong>
                      </div>
                    )}
                  </div>

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type={showPassword ? "text" : "password"}
                        name="password"
                        placeholder="Mot de passe"
                        value={formData.password}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${errors.password ? styles.error : ''}`}
                        required
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

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type={showConfirmPassword ? "text" : "password"}
                        name="confirmPassword"
                        placeholder="Confirmer le mot de passe"
                        value={formData.confirmPassword}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${errors.confirmPassword ? styles.error : ''}`}
                        required
                      />
                      <button
                        type="button"
                        className={styles.passwordToggle}
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </button>
                    </div>
                    {errors.confirmPassword && <div className={styles.errorText}>{errors.confirmPassword}</div>}
                  </div>

                  {/* Case à cocher pour accepter les conditions */}
                  <div className={styles.inputGroup}>
                    <div className={styles.checkboxWrapper}>
                      <Form.Check
                        type="checkbox"
                        name="acceptTerms"
                        id="acceptTerms"
                        checked={formData.acceptTerms}
                        onChange={handleInputChange}
                        className={`${styles.customCheckbox} ${errors.acceptTerms ? styles.error : ''}`}
                        required
                      />
                      <label htmlFor="acceptTerms" className={styles.checkboxLabel}>
                        J'accepte les{' '}
                        <Link to="/terms" target="_blank" className={styles.legalLink}>
                          Conditions d'utilisation
                        </Link>
                        {' '}et la{' '}
                        <Link to="/privacy" target="_blank" className={styles.legalLink}>
                          Politique de confidentialité
                        </Link>
                      </label>
                    </div>
                    {errors.acceptTerms && <div className={styles.errorText}>{errors.acceptTerms}</div>}
                  </div>

                  {/* Bouton d'inscription */}
                  <Button
                    type="submit"
                    disabled={isLoading}
                    className={styles.signupButton}
                  >
                    {isLoading ? (
                      <div className={styles.loadingSpinner} />
                    ) : (
                      <>
                        <PersonAddIcon className={styles.buttonIcon} />
                        Créer mon compte
                      </>
                    )}
                  </Button>
                </Form>

                {/* Divider */}
                <div className={styles.divider}>
                  <span>ou</span>
                </div>

                {/* Lien de connexion */}
                <div className={styles.loginLink}>
                  Vous avez déjà un compte ? {' '}
                  <Link to="/login" className={styles.link}>
                    Se connecter
                    <ArrowForwardIcon className={styles.linkIcon} />
                  </Link>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default SignUpPage;