import React, { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { useAuth } from '../contexts/AuthContext';
import {
    Person as PersonIcon,
    Email as EmailIcon,
    LocationOn as LocationIcon,
    Save as SaveIcon,
    PhotoCamera as PhotoIcon,
    Visibility as VisibilityIcon,
    VisibilityOff as VisibilityOffIcon,
    Lock as LockIcon
} from '@mui/icons-material';
import styles from './UserSettingsPage.module.css';

const UserSettingsPage = () => {
    const { user, updateUser, refreshUserData } = useAuth();
    const [isEditing, setIsEditing] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        firstName: user?.firstName || '',
        lastName: user?.lastName || '',
        email: user?.email || '',
        avatar: user?.avatar || '',
        city: user?.location?.city || '',
        region: user?.location?.region || '',
        province: user?.location?.province || '',
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
    });

    // Debug temporaire
    console.log('UserSettingsPage - user:', user);
    console.log('UserSettingsPage - formData.avatar:', formData.avatar);

    // Mettre à jour formData quand user change
    useEffect(() => {
        if (user) {
            setFormData({
                firstName: user.firstName || '',
                lastName: user.lastName || '',
                email: user.email || '',
                avatar: user.avatar || '',
                city: user.location?.city || '',
                region: user.location?.region || '',
                province: user.location?.province || '',
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            });
        }
    }, [user]);

    const [errors, setErrors] = useState({});
    const [isLoading, setIsLoading] = useState(false);
    const [successMessage, setSuccessMessage] = useState('');

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
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
            newErrors.lastName = 'Le nom de famille est requis';
        }

        if (!formData.email.trim()) {
            newErrors.email = 'L\'email est requis';
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = 'Format d\'email invalide';
        }

        if (formData.newPassword && formData.newPassword.length < 6) {
            newErrors.newPassword = 'Le mot de passe doit contenir au moins 6 caractères';
        }

        if (formData.newPassword && formData.newPassword !== formData.confirmPassword) {
            newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
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
        setSuccessMessage('');

        try {
            // Simuler une mise à jour (remplacer par vraie logique API)
            await new Promise(resolve => setTimeout(resolve, 1000));

            const updatedUserData = {
                ...user,
                firstName: formData.firstName,
                lastName: formData.lastName,
                email: formData.email,
                avatar: formData.avatar,
                location: {
                    city: formData.city,
                    region: formData.region,
                    province: formData.province
                }
            };

            if (updateUser) {
                updateUser(updatedUserData);
            }

            setSuccessMessage('Profil mis à jour avec succès !');
            setIsEditing(false);

            // Clear password fields
            setFormData(prev => ({
                ...prev,
                currentPassword: '',
                newPassword: '',
                confirmPassword: ''
            }));

        } catch (error) {
            console.error('Erreur lors de la mise à jour:', error);
            setErrors({ general: 'Une erreur est survenue lors de la mise à jour' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleCancel = () => {
        setFormData({
            firstName: user?.firstName || '',
            lastName: user?.lastName || '',
            email: user?.email || '',
            avatar: user?.avatar || '',
            city: user?.location?.city || '',
            region: user?.location?.region || '',
            province: user?.location?.province || '',
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
        });
        setErrors({});
        setIsEditing(false);
        setSuccessMessage('');
    };

    if (!user) {
        return (
            <Layout>
                <div className={styles.authRequired}>
                    <h2>Paramètres du compte</h2>
                    <p>Connectez-vous pour accéder aux paramètres de votre compte</p>
                    <button onClick={() => window.location.href = '/login'} className={styles.loginButton}>
                        Se connecter
                    </button>
                </div>
            </Layout>
        );
    }

    return (
        <Layout
            title="Paramètres du compte"
            subtitle="Gérez vos informations personnelles et vos préférences"
        >
            <div className={styles.settingsContainer}>
                {/* Message de succès */}
                {successMessage && (
                    <div className={styles.successMessage}>
                        {successMessage}
                    </div>
                )}

                {/* Erreur générale */}
                {errors.general && (
                    <div className={styles.errorMessage}>
                        {errors.general}
                    </div>
                )}

                {/* Section Profil */}
                <div className={styles.section}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>
                            <PersonIcon className={styles.sectionIcon} />
                            Informations personnelles
                        </h2>
                        {!isEditing && (
                            <button
                                className={styles.editButton}
                                onClick={() => setIsEditing(true)}
                            >
                                Modifier
                            </button>
                        )}
                    </div>

                    <form onSubmit={handleSubmit} className={styles.form}>
                        {/* Photo de profil */}
                        <div className={styles.avatarSection}>
                            <div className={styles.avatarContainer}>
                                {formData.avatar ? (
                                    <img
                                        src={formData.avatar}
                                        alt="Avatar"
                                        className={styles.avatar}
                                        onError={(e) => {
                                            console.log('Erreur chargement avatar dans profil:', formData.avatar);
                                            e.target.style.display = 'none';
                                            // Afficher le placeholder quand l'image échoue
                                            const placeholder = e.target.parentElement.querySelector('.avatar-placeholder');
                                            if (placeholder) {
                                                placeholder.style.display = 'flex';
                                            }
                                        }}
                                    />
                                ) : null}
                                <div
                                    className={`${styles.avatarPlaceholder} avatar-placeholder`}
                                    style={{ display: formData.avatar ? 'none' : 'flex' }}
                                >
                                    <PersonIcon className={styles.avatarIcon} />
                                </div>
                                <button
                                    type="button"
                                    className={styles.avatarChangeButton}
                                    disabled={!isEditing}
                                >
                                    <PhotoIcon />
                                </button>
                            </div>
                            {isEditing && (
                                <input
                                    type="url"
                                    name="avatar"
                                    placeholder="URL de la photo de profil"
                                    value={formData.avatar}
                                    onChange={handleInputChange}
                                    className={styles.input}
                                />
                            )}
                        </div>

                        {/* Informations de base */}
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Prénom</label>
                                <input
                                    type="text"
                                    name="firstName"
                                    value={formData.firstName}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className={`${styles.input} ${errors.firstName ? styles.inputError : ''}`}
                                />
                                {errors.firstName && (
                                    <span className={styles.errorText}>{errors.firstName}</span>
                                )}
                            </div>

                            <div className={styles.formGroup}>
                                <label className={styles.label}>Nom de famille</label>
                                <input
                                    type="text"
                                    name="lastName"
                                    value={formData.lastName}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className={`${styles.input} ${errors.lastName ? styles.inputError : ''}`}
                                />
                                {errors.lastName && (
                                    <span className={styles.errorText}>{errors.lastName}</span>
                                )}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>
                                <EmailIcon className={styles.inputIcon} />
                                Adresse email
                            </label>
                            <input
                                type="email"
                                name="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                className={`${styles.input} ${errors.email ? styles.inputError : ''}`}
                            />
                            {errors.email && (
                                <span className={styles.errorText}>{errors.email}</span>
                            )}
                        </div>

                        {/* Localisation */}
                        <div className={styles.formRow}>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>
                                    <LocationIcon className={styles.inputIcon} />
                                    Ville
                                </label>
                                <input
                                    type="text"
                                    name="city"
                                    value={formData.city}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className={styles.input}
                                />
                            </div>

                            <div className={styles.formGroup}>
                                <label className={styles.label}>Région</label>
                                <input
                                    type="text"
                                    name="region"
                                    value={formData.region}
                                    onChange={handleInputChange}
                                    disabled={!isEditing}
                                    className={styles.input}
                                />
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label className={styles.label}>Province</label>
                            <input
                                type="text"
                                name="province"
                                value={formData.province}
                                onChange={handleInputChange}
                                disabled={!isEditing}
                                className={styles.input}
                            />
                        </div>

                        {/* Section mot de passe - seulement en mode édition */}
                        {isEditing && (
                            <div className={styles.passwordSection}>
                                <h3 className={styles.subsectionTitle}>
                                    <LockIcon className={styles.sectionIcon} />
                                    Changer le mot de passe
                                </h3>

                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Mot de passe actuel</label>
                                    <div className={styles.passwordInputContainer}>
                                        <input
                                            type={showPassword ? "text" : "password"}
                                            name="currentPassword"
                                            value={formData.currentPassword}
                                            onChange={handleInputChange}
                                            className={styles.input}
                                            placeholder="Laissez vide pour ne pas changer"
                                        />
                                        <button
                                            type="button"
                                            className={styles.passwordToggle}
                                            onClick={() => setShowPassword(!showPassword)}
                                        >
                                            {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                                        </button>
                                    </div>
                                </div>

                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Nouveau mot de passe</label>
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        name="newPassword"
                                        value={formData.newPassword}
                                        onChange={handleInputChange}
                                        className={`${styles.input} ${errors.newPassword ? styles.inputError : ''}`}
                                    />
                                    {errors.newPassword && (
                                        <span className={styles.errorText}>{errors.newPassword}</span>
                                    )}
                                </div>

                                <div className={styles.formGroup}>
                                    <label className={styles.label}>Confirmer le nouveau mot de passe</label>
                                    <input
                                        type={showPassword ? "text" : "password"}
                                        name="confirmPassword"
                                        value={formData.confirmPassword}
                                        onChange={handleInputChange}
                                        className={`${styles.input} ${errors.confirmPassword ? styles.inputError : ''}`}
                                    />
                                    {errors.confirmPassword && (
                                        <span className={styles.errorText}>{errors.confirmPassword}</span>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Boutons d'action */}
                        {isEditing && (
                            <div className={styles.formActions}>
                                <button
                                    type="button"
                                    onClick={handleCancel}
                                    className={styles.cancelButton}
                                    disabled={isLoading}
                                >
                                    Annuler
                                </button>
                                <button
                                    type="submit"
                                    className={styles.saveButton}
                                    disabled={isLoading}
                                >
                                    <SaveIcon className={styles.buttonIcon} />
                                    {isLoading ? 'Enregistrement...' : 'Enregistrer'}
                                </button>
                            </div>
                        )}
                    </form>
                </div>

                {/* Informations du compte */}
                <div className={styles.section}>
                    <h2 className={styles.sectionTitle}>Informations du compte</h2>
                    <div className={styles.accountInfo}>
                        <div className={styles.infoItem}>
                            <span className={styles.infoLabel}>Rôle :</span>
                            <span className={`${styles.roleBadge} ${styles[user?.role]}`}>
                                {user?.roleDisplay}
                            </span>
                        </div>
                        <div className={styles.infoItem}>
                            <span className={styles.infoLabel}>Membre depuis :</span>
                            <span className={styles.infoValue}>
                                {user?.joinedDate ? new Date(user.joinedDate).toLocaleDateString('fr-FR') : 'Non défini'}
                            </span>
                        </div>
                        <div className={styles.infoItem}>
                            <span className={styles.infoLabel}>ID utilisateur :</span>
                            <span className={styles.infoValue}>#{user?.id}</span>
                        </div>
                    </div>
                    <div style={{ marginTop: '20px' }}>
                        <button
                            onClick={refreshUserData}
                            className={styles.saveButton}
                            style={{ fontSize: '14px', padding: '8px 16px' }}
                        >
                            Rafraîchir les données
                        </button>
                    </div>
                </div>
            </div>
        </Layout>
    );
};

export default UserSettingsPage;