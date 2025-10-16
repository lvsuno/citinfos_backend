/**
 * Utility functions for password generation and validation.
 */

/**
 * Generate a random password with specified criteria.
 * @param {number} length - Password length (default: 12)
 * @param {boolean} includeUppercase - Include uppercase letters (default: true)
 * @param {boolean} includeLowercase - Include lowercase letters (default: true)
 * @param {boolean} includeNumbers - Include numbers (default: true)
 * @param {boolean} includeSymbols - Include symbols (default: false)
 * @returns {string} Generated password
 */
export function generatePassword(
    length = 12,
    includeUppercase = true,
    includeLowercase = true,
    includeNumbers = true,
    includeSymbols = false
) {
    let charset = '';
    
    if (includeUppercase) charset += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    if (includeLowercase) charset += 'abcdefghijklmnopqrstuvwxyz';
    if (includeNumbers) charset += '0123456789';
    if (includeSymbols) charset += '!@#$%^&*()_+-=[]{}|;:,.<>?';
    
    if (charset === '') {
        throw new Error('At least one character set must be included');
    }
    
    let password = '';
    for (let i = 0; i < length; i++) {
        password += charset.charAt(Math.floor(Math.random() * charset.length));
    }
    
    return password;
}

/**
 * Check password strength and return score with feedback.
 * @param {string} password - Password to check
 * @returns {object} Object with score (0-100) and feedback array
 */
export function checkPasswordStrength(password) {
    let score = 0;
    const feedback = [];
    
    if (!password) {
        return { score: 0, feedback: ['Mot de passe requis'] };
    }
    
    // Length check
    if (password.length >= 8) {
        score += 25;
    } else {
        feedback.push('Le mot de passe doit contenir au moins 8 caractères');
    }
    
    // Uppercase check
    if (/[A-Z]/.test(password)) {
        score += 25;
    } else {
        feedback.push('Ajouter au moins une lettre majuscule');
    }
    
    // Lowercase check
    if (/[a-z]/.test(password)) {
        score += 25;
    } else {
        feedback.push('Ajouter au moins une lettre minuscule');
    }
    
    // Number check
    if (/\d/.test(password)) {
        score += 25;
    } else {
        feedback.push('Ajouter au moins un chiffre');
    }
    
    // Symbol check (bonus)
    if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
        score += 10;
    }
    
    // Length bonus
    if (password.length >= 12) {
        score += 10;
    }
    
    return {
        score: Math.min(score, 100),
        feedback
    };
}

/**
 * Get password strength level based on score.
 * @param {number} score - Password strength score (0-100)
 * @returns {object} Object with level, color, and label
 */
export function getPasswordStrengthLevel(score) {
    if (score < 25) {
        return { level: 'weak', color: '#ef4444', label: 'Faible' };
    } else if (score < 50) {
        return { level: 'fair', color: '#f59e0b', label: 'Moyen' };
    } else if (score < 75) {
        return { level: 'good', color: '#3b82f6', label: 'Bon' };
    } else {
        return { level: 'strong', color: '#10b981', label: 'Fort' };
    }
}

/**
 * Validate password meets minimum requirements.
 * @param {string} password - Password to validate
 * @returns {object} Object with isValid boolean and errors array
 */
export function validatePassword(password) {
    const errors = [];
    
    if (!password) {
        return { isValid: false, errors: ['Mot de passe requis'] };
    }
    
    if (password.length < 8) {
        errors.push('Le mot de passe doit contenir au moins 8 caractères');
    }
    
    if (!/[A-Z]/.test(password)) {
        errors.push('Le mot de passe doit contenir au moins une lettre majuscule');
    }
    
    if (!/[a-z]/.test(password)) {
        errors.push('Le mot de passe doit contenir au moins une lettre minuscule');
    }
    
    if (!/\d/.test(password)) {
        errors.push('Le mot de passe doit contenir au moins un chiffre');
    }
    
    return {
        isValid: errors.length === 0,
        errors
    };
}

/**
 * Generate multiple password suggestions.
 * @param {number} count - Number of passwords to generate (default: 3)
 * @param {number} length - Password length (default: 12)
 * @returns {array} Array of generated passwords
 */
export function generatePasswordSuggestions(count = 3, length = 12) {
    const passwords = [];
    
    for (let i = 0; i < count; i++) {
        passwords.push(generatePassword(length, true, true, true, i === 0));
    }
    
    return passwords;
}

/**
 * Check if password contains common patterns.
 * @param {string} password - Password to check
 * @returns {array} Array of detected patterns
 */
export function checkCommonPatterns(password) {
    const patterns = [];
    
    // Sequential characters
    if (/123|abc|qwe/i.test(password)) {
        patterns.push('Contient des caractères séquentiels');
    }
    
    // Repeated characters
    if (/(.)\1{2,}/.test(password)) {
        patterns.push('Contient des caractères répétés');
    }
    
    // Common words
    const commonWords = ['password', 'admin', 'user', 'login', '123456'];
    for (const word of commonWords) {
        if (password.toLowerCase().includes(word)) {
            patterns.push(`Contient le mot commun "${word}"`);
            break;
        }
    }
    
    return patterns;
}