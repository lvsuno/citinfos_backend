import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Form, Button, Alert, Card } from 'react-bootstrap';
import { Link } from 'react-router-dom';
import {
  Email as EmailIcon,
  Security as SecurityIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Home as HomeIcon
} from '@mui/icons-material';
import styles from './VerifyAccount.module.css';

const RESEND_TIMEOUT = 60; // seconds
const CODE_VALIDITY_MINUTES = 5; // Code expires after 5 minutes

const VerifyAccount = ({ onSuccess, initialEmail, onClose, show, message, userEmail, autoSendCode = false }) => {
  const [formData, setFormData] = useState({
    email: initialEmail || userEmail || '',
    code: ''
  });
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [resendTimer, setResendTimer] = useState(0);
  const [codeExpiryTime, setCodeExpiryTime] = useState(null);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [autoSendTriggered, setAutoSendTriggered] = useState(false);

  // Auto-send verification code when modal opens (for expired verification)
  useEffect(() => {
    const sendCodeAutomatically = async () => {
      if (autoSendCode && formData.email && !autoSendTriggered) {
        setAutoSendTriggered(true);

        try {
          const { apiService } = await import('../services/apiService');
          const result = await apiService.resendVerificationCode(formData.email);

          if (result.success) {
            setSuccess(result.message || 'Un nouveau code de vérification a été envoyé à votre email.');
            setResendTimer(RESEND_TIMEOUT);

            const newExpiryTime = new Date(Date.now() + CODE_VALIDITY_MINUTES * 60 * 1000);
            setCodeExpiryTime(newExpiryTime);
          }
        } catch (error) {
          setError(error.message || 'Erreur lors de l\'envoi du code. Veuillez réessayer.');
        }
      }
    };

    sendCodeAutomatically();
  }, [autoSendCode, formData.email, autoSendTriggered]);

  useEffect(() => {
    // Get verification details from localStorage
    const pendingVerification = localStorage.getItem('pendingVerification');
    if (pendingVerification) {
      try {
        const verificationData = JSON.parse(pendingVerification);
        if (verificationData.email) {
          setFormData(prev => ({ ...prev, email: verificationData.email }));
        }
        if (verificationData.verification_expiry) {
          setCodeExpiryTime(new Date(verificationData.verification_expiry));
        }
      } catch (error) {      }
    } else if (!initialEmail) {
      // Fallback to old pendingEmail format
      const savedEmail = localStorage.getItem('pendingEmail');
      if (savedEmail) {
        setFormData(prev => ({ ...prev, email: savedEmail }));
      }
      // Initialize default expiry time if no stored expiry
      const expiryTime = new Date(Date.now() + CODE_VALIDITY_MINUTES * 60 * 1000);
      setCodeExpiryTime(expiryTime);
    } else {
      // Initialize default expiry time if using initialEmail
      const expiryTime = new Date(Date.now() + CODE_VALIDITY_MINUTES * 60 * 1000);
      setCodeExpiryTime(expiryTime);
    }
  }, [initialEmail]);

  useEffect(() => {
    if (resendTimer > 0) {
      const timer = setTimeout(() => setResendTimer(resendTimer - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [resendTimer]);

  // Countdown timer for code expiry
  useEffect(() => {
    if (!codeExpiryTime) return;

    const updateTimer = () => {
      const now = new Date();
      const remaining = Math.max(0, Math.floor((codeExpiryTime - now) / 1000));
      setTimeRemaining(remaining);
    };

    updateTimer(); // Initial update
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [codeExpiryTime]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear error when user starts typing
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.email || !formData.code) {
      setError('Veuillez saisir votre email et le code de vérification');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');

    try {
      // Import apiService here to avoid circular dependency
      const { apiService } = await import('../services/apiService');

      const result = await apiService.verifyEmail(formData.email, formData.code);

      if (result.success) {
        localStorage.removeItem('pendingEmail');
        localStorage.removeItem('pendingVerification');
        setSuccess(result.message || 'Votre compte a été vérifié avec succès !');

        // Show closing message after 2 seconds, then call callback after 3 seconds total
        setTimeout(() => {
          setSuccess('Vérification réussie ! Redirection en cours...');
        }, 2000);

        if (onSuccess) {
          setTimeout(() => {
            onSuccess(result);
          }, 3000);
        }
      }
    } catch (error) {
      setError(error.message || 'Erreur lors de la vérification. Veuillez réessayer.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!formData.email) {
      setError('Veuillez saisir votre adresse email');
      return;
    }

    setResending(true);
    setError('');

    try {
      // Import apiService here to avoid circular dependency
      const { apiService } = await import('../services/apiService');

      const result = await apiService.resendVerificationCode(formData.email);

      if (result.success) {
        setSuccess(result.message || 'Code de vérification renvoyé !');
        setResendTimer(RESEND_TIMEOUT);

        // Reset countdown timer for new code
        const newExpiryTime = new Date(Date.now() + CODE_VALIDITY_MINUTES * 60 * 1000);
        setCodeExpiryTime(newExpiryTime);
      }
    } catch (error) {
      setError(error.message || 'Erreur lors du renvoi du code. Veuillez réessayer.');
    } finally {
      setResending(false);
    }
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const isCodeExpired = timeRemaining === 0;

  return (
    <div className={styles.verifyPage}>
      {/* Back to home link - only show when not in modal mode */}
      {!onSuccess && (
        <Link to="/" className={styles.backToHome}>
          <HomeIcon /> Retour à l'accueil
        </Link>
      )}

      <Container className="position-relative" style={{ zIndex: 10 }}>
        <Row className="justify-content-center min-vh-100 align-items-center">
          <Col lg={7} md={8} sm={10} xs={11}>
            <Card className={styles.verifyCard}>
              <Card.Body>
                {/* Header */}
                <div className={styles.cardHeader}>
                  <div className={styles.iconContainer}>
                    <EmailIcon className={styles.headerIcon} />
                  </div>
                  <h1 className={styles.cardTitle}>
                    Vérification <span className={styles.gradientText}>Email</span>
                  </h1>
                  <p className={styles.cardSubtitle}>
                    Nous avons envoyé un code de vérification à votre adresse email.
                    Veuillez saisir ce code pour activer votre compte.
                  </p>
                </div>

                {/* Form */}
                <Form onSubmit={handleSubmit} className={styles.verifyForm}>
                  {error && (
                    <Alert variant="danger" className={styles.errorAlert}>
                      {error}
                    </Alert>
                  )}

                  {success && (
                    <Alert variant="success" className={styles.successAlert}>
                      <CheckCircleIcon className={styles.successIcon} />
                      {success}
                    </Alert>
                  )}

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type="email"
                        name="email"
                        placeholder="Adresse email"
                        value={formData.email}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${error ? styles.error : ''}`}
                        disabled={!!initialEmail}
                        required
                      />
                      <EmailIcon className={styles.inputIcon} />
                    </div>
                    {formData.email && (
                      <div className={styles.inputHint}>
                        Code envoyé à cette adresse
                      </div>
                    )}
                  </div>

                  <div className={styles.inputGroup}>
                    <div className={styles.inputWrapper}>
                      <Form.Control
                        type="text"
                        name="code"
                        placeholder="Code de vérification"
                        value={formData.code}
                        onChange={handleInputChange}
                        className={`${styles.formInput} ${error ? styles.error : ''}`}
                        maxLength={8}
                        required
                      />
                      <SecurityIcon className={styles.inputIcon} />
                    </div>
                    <div className={styles.inputHint}>
                      Saisissez le code à 8 caractères reçu par email
                    </div>

                    {/* Countdown Timer */}
                    <div className={styles.countdownContainer}>
                      <div className={`${styles.countdownTimer} ${isCodeExpired ? styles.expired : ''}`}>
                        {isCodeExpired ? (
                          <span className={styles.expiredText}>
                            ⏰ Code expiré - Demandez un nouveau code
                          </span>
                        ) : (
                          <span className={styles.timerText}>
                            🕒 Code valide encore <strong>{formatTime(timeRemaining)}</strong>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Verify Button */}
                  <Button
                    type="submit"
                    disabled={loading || !formData.email || !formData.code || isCodeExpired}
                    className={styles.verifyButton}
                  >
                    {loading ? (
                      <div className={styles.loadingSpinner} />
                    ) : isCodeExpired ? (
                      <>
                        <SecurityIcon className={styles.buttonIcon} />
                        Code expiré - Obtenez un nouveau code
                      </>
                    ) : (
                      <>
                        <CheckCircleIcon className={styles.buttonIcon} />
                        Vérifier mon compte
                      </>
                    )}
                  </Button>

                  {/* Resend Code */}
                  <div className={styles.resendSection}>
                    <p className={styles.resendText}>
                      {isCodeExpired
                        ? "Votre code a expiré. Obtenez un nouveau code :"
                        : "Vous n'avez pas reçu le code ?"
                      }
                    </p>
                    <Button
                      type="button"
                      variant="outline-primary"
                      onClick={handleResend}
                      disabled={(!isCodeExpired && resendTimer > 0) || resending || !formData.email}
                      className={styles.resendButton}
                    >
                      {resending ? (
                        <>
                          <div className={styles.loadingSpinner} />
                          Envoi en cours...
                        </>
                      ) : isCodeExpired ? (
                        <>
                          <RefreshIcon className={styles.buttonIcon} />
                          Obtenir un nouveau code
                        </>
                      ) : resendTimer > 0 ? (
                        `Renvoyer dans ${resendTimer}s`
                      ) : (
                        <>
                          <RefreshIcon className={styles.buttonIcon} />
                          Renvoyer le code
                        </>
                      )}
                    </Button>
                  </div>
                </Form>

                {/* Information message */}
                <div className={styles.blockingNotice}>
                  <p className={styles.noticeText}>
                    ⚠️ Vous devez vérifier votre email pour continuer.
                    Cette fenêtre se fermera automatiquement après la vérification.
                  </p>
                </div>

                {/* Login link - only show when not in modal mode */}
                {!onSuccess && (
                  <div className={styles.loginLink}>
                    Déjà vérifié ? {' '}
                    <Link to="/login" className={styles.link}>
                      Se connecter
                    </Link>
                  </div>
                )}
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
};

export default VerifyAccount;