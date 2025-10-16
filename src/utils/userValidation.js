/**
 * Validation utilities for user creation and management.
 */

/**
 * Validate email format
 * @param {string} email - Email to validate
 * @returns {boolean} True if valid email format
 */
export function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * Validate phone number format (basic validation)
 * @param {string} phone - Phone number to validate
 * @returns {boolean} True if valid phone format
 */
export function isValidPhone(phone) {
    // Allow digits, spaces, dashes, plus, parentheses
    const phoneRegex = /^[\d\s\-\+\(\)]+$/;
    return phoneRegex.test(phone) && phone.replace(/\D/g, '').length >= 10;
}

/**
 * Validate username format
 * @param {string} username - Username to validate
 * @returns {object} Object with isValid boolean and error message
 */
export function validateUsername(username) {
    if (!username) {
        return { isValid: false, error: 'Nom d\'utilisateur requis' };
    }
    
    if (username.length < 3) {
        return { isValid: false, error: 'Le nom d\'utilisateur doit contenir au moins 3 caractères' };
    }
    
    if (username.length > 30) {
        return { isValid: false, error: 'Le nom d\'utilisateur ne peut pas dépasser 30 caractères' };
    }
    
    // Allow letters, numbers, underscore, dash
    const usernameRegex = /^[a-zA-Z0-9_-]+$/;
    if (!usernameRegex.test(username)) {
        return { isValid: false, error: 'Le nom d\'utilisateur ne peut contenir que des lettres, chiffres, tirets et underscores' };
    }
    
    return { isValid: true, error: null };
}

/**
 * Validate required text field
 * @param {string} value - Value to validate
 * @param {string} fieldName - Name of the field for error message
 * @param {number} minLength - Minimum length (default: 1)
 * @param {number} maxLength - Maximum length (default: 100)
 * @returns {object} Object with isValid boolean and error message
 */
export function validateRequiredText(value, fieldName, minLength = 1, maxLength = 100) {
    if (!value || !value.trim()) {
        return { isValid: false, error: `${fieldName} requis` };
    }
    
    if (value.trim().length < minLength) {
        return { isValid: false, error: `${fieldName} doit contenir au moins ${minLength} caractère${minLength > 1 ? 's' : ''}` };
    }
    
    if (value.trim().length > maxLength) {
        return { isValid: false, error: `${fieldName} ne peut pas dépasser ${maxLength} caractères` };
    }
    
    return { isValid: true, error: null };
}

/**
 * Validate date of birth
 * @param {string|Date} dateOfBirth - Date of birth to validate
 * @returns {object} Object with isValid boolean and error message
 */
export function validateDateOfBirth(dateOfBirth) {
    if (!dateOfBirth) {
        return { isValid: false, error: 'Date de naissance requise' };
    }
    
    const date = typeof dateOfBirth === 'string' ? new Date(dateOfBirth) : dateOfBirth;
    
    if (isNaN(date.getTime())) {
        return { isValid: false, error: 'Date de naissance invalide' };
    }
    
    const today = new Date();
    const age = today.getFullYear() - date.getFullYear();
    const monthDiff = today.getMonth() - date.getMonth();
    
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < date.getDate())) {
        age--;
    }
    
    if (age < 16) {
        return { isValid: false, error: 'L\'utilisateur doit avoir au moins 16 ans' };
    }
    
    if (age > 120) {
        return { isValid: false, error: 'Date de naissance non valide' };
    }
    
    return { isValid: true, error: null };
}

/**
 * Validate complete user form data
 * @param {object} formData - Complete form data object
 * @returns {object} Object with isValid boolean and errors object
 */
export function validateUserForm(formData) {
    const errors = {};
    let isValid = true;
    
    // Username validation
    const usernameValidation = validateUsername(formData.username);
    if (!usernameValidation.isValid) {
        errors.username = usernameValidation.error;
        isValid = false;
    }
    
    // Email validation
    if (!formData.email) {
        errors.email = 'Email requis';
        isValid = false;
    } else if (!isValidEmail(formData.email)) {
        errors.email = 'Format d\'email invalide';
        isValid = false;
    }
    
    // Password validation
    if (!formData.password) {
        errors.password = 'Mot de passe requis';
        isValid = false;
    } else if (formData.password.length < 8) {
        errors.password = 'Le mot de passe doit contenir au moins 8 caractères';
        isValid = false;
    }
    
    // First name validation
    const firstNameValidation = validateRequiredText(formData.first_name, 'Prénom', 1, 50);
    if (!firstNameValidation.isValid) {
        errors.first_name = firstNameValidation.error;
        isValid = false;
    }
    
    // Last name validation
    const lastNameValidation = validateRequiredText(formData.last_name, 'Nom', 1, 50);
    if (!lastNameValidation.isValid) {
        errors.last_name = lastNameValidation.error;
        isValid = false;
    }
    
    // Phone validation
    if (!formData.phone_number) {
        errors.phone_number = 'Numéro de téléphone requis';
        isValid = false;
    } else if (!isValidPhone(formData.phone_number)) {
        errors.phone_number = 'Format de téléphone invalide';
        isValid = false;
    }
    
    // Date of birth validation
    const dobValidation = validateDateOfBirth(formData.date_of_birth);
    if (!dobValidation.isValid) {
        errors.date_of_birth = dobValidation.error;
        isValid = false;
    }
    
    // Role validation
    if (!formData.role || !['admin', 'moderator'].includes(formData.role)) {
        errors.role = 'Rôle invalide';
        isValid = false;
    }
    
    return { isValid, errors };
}

/**
 * Check if a username is available (mock function - would call API in real implementation)
 * @param {string} username - Username to check
 * @returns {Promise<boolean>} True if username is available
 */
export async function checkUsernameAvailability(username) {
    // In a real implementation, this would make an API call
    // For now, return true after a short delay to simulate API call
    return new Promise((resolve) => {
        setTimeout(() => {
            // Mock some taken usernames
            const takenUsernames = ['admin', 'administrator', 'moderator', 'root', 'test'];
            resolve(!takenUsernames.includes(username.toLowerCase()));
        }, 500);
    });
}

/**
 * Check if an email is available (mock function - would call API in real implementation)
 * @param {string} email - Email to check
 * @returns {Promise<boolean>} True if email is available
 */
export async function checkEmailAvailability(email) {
    // In a real implementation, this would make an API call
    return new Promise((resolve) => {
        setTimeout(() => {
            // Mock some taken emails
            const takenEmails = ['admin@example.com', 'test@example.com'];
            resolve(!takenEmails.includes(email.toLowerCase()));
        }, 500);
    });
}

/**
 * Format phone number for display
 * @param {string} phone - Phone number to format
 * @returns {string} Formatted phone number
 */
export function formatPhoneNumber(phone) {
    // Remove all non-digit characters
    const cleaned = phone.replace(/\D/g, '');
    
    // Format based on length
    if (cleaned.length === 10) {
        // Format as (XXX) XXX-XXXX
        return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
        // Format as +1 (XXX) XXX-XXXX
        return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
    }
    
    // Return as-is if we can't format it
    return phone;
}

/**
 * Generate a unique employee ID
 * @param {string} role - User role (admin or moderator)
 * @returns {string} Generated employee ID
 */
export function generateEmployeeId(role) {
    const prefix = role === 'admin' ? 'ADM' : 'MOD';
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.floor(Math.random() * 100).toString().padStart(2, '0');
    
    return `${prefix}-${timestamp}-${random}`;
}