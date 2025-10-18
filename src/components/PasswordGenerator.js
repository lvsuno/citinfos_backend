import React, { useState } from 'react';
import { createPortal } from 'react-dom';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CloseIcon from '@mui/icons-material/Close';
import apiService from '../services/apiService';
import styles from './PasswordGenerator.module.css';

const PasswordGenerator = ({ onPasswordSelect }) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showGenerator, setShowGenerator] = useState(false);
  const [copied, setCopied] = useState(null);

  const generatePasswords = async () => {
    setLoading(true);
    try {
      const response = await apiService.get('/auth/generate-passwords/?count=3');

      if (response.data && response.data.suggestions) {
        setSuggestions(response.data.suggestions);
      }
    } catch (error) {      // Generate fallback passwords client-side if backend fails
      const fallbackPasswords = generateFallbackPasswords(3);
      setSuggestions(fallbackPasswords);
    } finally {
      setLoading(false);
    }
  };

  const generateFallbackPasswords = (count) => {
    const passwords = [];
    const chars = {
      lowercase: 'abcdefghijklmnopqrstuvwxyz',
      uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
      numbers: '0123456789',
      symbols: '!@#$%^&*()_+-=[]{}|;:,.<>?'
    };

    for (let i = 0; i < count; i++) {
      let password = '';
      const length = 12 + Math.floor(Math.random() * 4); // 12-15 chars

      // Ensure at least one from each category
      password += chars.lowercase[Math.floor(Math.random() * chars.lowercase.length)];
      password += chars.uppercase[Math.floor(Math.random() * chars.uppercase.length)];
      password += chars.numbers[Math.floor(Math.random() * chars.numbers.length)];
      password += chars.symbols[Math.floor(Math.random() * chars.symbols.length)];

      // Fill the rest randomly
      const allChars = Object.values(chars).join('');
      for (let j = 4; j < length; j++) {
        password += allChars[Math.floor(Math.random() * allChars.length)];
      }

      // Shuffle the password
      password = password.split('').sort(() => 0.5 - Math.random()).join('');
      passwords.push(password);
    }

    return passwords;
  };

  const copyToClipboard = async (password, index) => {
    try {
      await navigator.clipboard.writeText(password);
      setCopied(index);
      setTimeout(() => setCopied(null), 2000);
    } catch (error) {    }
  };

  const selectPassword = (password) => {
    onPasswordSelect(password);
    setShowGenerator(false);
  };

  const handleToggleGenerator = () => {
    const willShow = !showGenerator;

    if (willShow) {
      // Force close municipality selector and any other dropdowns
      const dropdowns = document.querySelectorAll('[aria-expanded="true"], .EnhancedMunicipalitySelector_dropdownMenu__show');
      dropdowns.forEach(dropdown => {
        // Try clicking the dropdown itself or its parent button
        dropdown.click();
      });

      // Also try to find and click any municipal selector buttons
      const municipalityButtons = document.querySelectorAll('[aria-haspopup="listbox"]');
      municipalityButtons.forEach(button => {
        if (button.getAttribute('aria-expanded') === 'true') {
          button.click();
        }
      });

      // Generate passwords if needed
      if (suggestions.length === 0) {
        generatePasswords();
      }
    }

    setShowGenerator(willShow);
  };

  return (
    <div className={styles.passwordGenerator}>
      <button
        type="button"
        onClick={handleToggleGenerator}
        className={styles.triggerButton}
        title="Générer un mot de passe fort"
      >
        <AutoAwesomeIcon className={styles.triggerIcon} />
      </button>

      {showGenerator && createPortal(
        <>
          {/* Backdrop */}
          <div
            className={styles.backdrop}
            onClick={() => setShowGenerator(false)}
          />

          {/* Modal */}
          <div className={styles.modal}>
            <div className={styles.modalHeader}>
              <h3 className={styles.modalTitle}>Suggestions de mots de passe</h3>
              <div className={styles.modalActions}>
                <button
                  type="button"
                  onClick={generatePasswords}
                  disabled={loading}
                  className={styles.refreshButton}
                  title="Générer de nouveaux mots de passe"
                >
                  <RefreshIcon className={`${styles.refreshIcon} ${loading ? styles.spinning : ''}`} />
                </button>
                <button
                  type="button"
                  onClick={() => setShowGenerator(false)}
                  className={styles.closeButton}
                  title="Fermer"
                >
                  <CloseIcon className={styles.closeIcon} />
                </button>
              </div>
            </div>

            <div className={styles.modalContent}>
              {loading ? (
                <div className={styles.loadingState}>
                  <div className={styles.loadingSpinner} />
                  <p className={styles.loadingText}>Génération de mots de passe...</p>
                </div>
              ) : suggestions.length > 0 ? (
                <div className={styles.passwordList}>
                  {suggestions.map((password, index) => (
                    <div key={index} className={styles.passwordItem}>
                      <code className={styles.passwordText}>{password}</code>
                      <div className={styles.passwordActions}>
                        <button
                          type="button"
                          onClick={() => copyToClipboard(password, index)}
                          className={styles.copyButton}
                          title="Copier dans le presse-papiers"
                        >
                          <ContentCopyIcon className={styles.copyIcon} />
                          {copied === index && <span className={styles.copiedIndicator}>Copié!</span>}
                        </button>
                        <button
                          type="button"
                          onClick={() => selectPassword(password)}
                          className={styles.useButton}
                        >
                          Utiliser
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={styles.emptyState}>
                  <p className={styles.emptyText}>
                    Cliquez sur actualiser pour générer des mots de passe forts
                  </p>
                </div>
              )}
            </div>

            <div className={styles.modalFooter}>
              <p className={styles.requirements}>
                <strong>Exigences:</strong> 8+ caractères, majuscules, minuscules, chiffres et caractères spéciaux (!@#$%^&*)
              </p>
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
};

export default PasswordGenerator;