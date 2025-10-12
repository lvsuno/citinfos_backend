/**
 * Device Fingerprint Service
 *
 * Manages server-generated device fingerprints for anonymous user tracking.
 *
 * Flow:
 * 1. Server generates fingerprint on first request
 * 2. Server sends fingerprint in X-Device-Fingerprint response header
 * 3. Client caches fingerprint in localStorage
 * 4. Client sends cached fingerprint in subsequent requests
 *
 * Performance:
 * - First request: Server generates (10-20ms, one-time)
 * - Subsequent requests: Client sends cached (0.1ms)
 * - Server uses cached fingerprint (0.1ms)
 */

class FingerprintService {
    constructor() {
        this.storageKey = 'device_fingerprint';
        this.sessionKey = 'session_id';
        this.fingerprint = null;
    }

    /**
     * Get cached device fingerprint (received from server)
     *
     * Priority:
     * 1. Memory cache
     * 2. localStorage (server-provided fingerprint)
     *
     * @returns {string|null} Cached fingerprint or null
     */
    getFingerprint() {
        // Tier 1: Memory cache
        if (this.fingerprint) {
            return this.fingerprint;
        }

        // Tier 2: localStorage (server-provided)
        const stored = localStorage.getItem(this.storageKey);
        if (stored) {
            this.fingerprint = stored;
            return stored;
        }

        // No fingerprint yet - will be set by server response
        return null;
    }

    /**
     * Save fingerprint to localStorage and memory cache
     * (Called when receiving fingerprint from server)
     *
     * @param {string} fingerprint - Server-generated fingerprint
     */
    saveFingerprint(fingerprint) {
        this.fingerprint = fingerprint;
        try {
            localStorage.setItem(this.storageKey, fingerprint);
        } catch (e) {
            // localStorage may be disabled
            console.warn('Cannot save fingerprint to localStorage:', e);
        }
    }

    /**
     * Extract fingerprint from server response header
     * Called automatically by axios response interceptor
     *
     * @param {Object} response - Axios response object
     */
    extractFromResponse(response) {
        try {
            const fingerprint = response.headers['x-device-fingerprint'];
            if (fingerprint) {
                this.saveFingerprint(fingerprint);
            }
        } catch (e) {
            // Ignore errors
        }
    }

    /**
     * Get session ID (for session tracking)
     *
     * @returns {string|null} Session ID
     */
    getSessionId() {
        try {
            return localStorage.getItem(this.sessionKey);
        } catch (e) {
            return null;
        }
    }

    /**
     * Save session ID (for session tracking)
     *
     * @param {string} sessionId - Session ID to save
     */
    saveSessionId(sessionId) {
        try {
            localStorage.setItem(this.sessionKey, sessionId);
        } catch (e) {
            console.warn('Cannot save session ID to localStorage:', e);
        }
    }

    /**
     * Clear fingerprint and session (for testing/logout)
     */
    clear() {
        this.fingerprint = null;
        try {
            localStorage.removeItem(this.storageKey);
            localStorage.removeItem(this.sessionKey);
        } catch (e) {
            // Ignore
        }
    }
}

// Export singleton instance
export default new FingerprintService();
