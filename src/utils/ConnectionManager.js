// Utilitaire pour gérer les tentatives de reconnexion API
export class ConnectionManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.retryAttempts = 0;
        this.maxRetries = 3;
        this.retryDelay = 1000; // 1 seconde

        // Écouter les changements de statut réseau
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
    }

    handleOnline() {
        this.isOnline = true;
        this.retryAttempts = 0;
        console.log('Connexion rétablie');
    }

    handleOffline() {
        this.isOnline = false;
        console.log('Connexion perdue');
    }

    async executeWithRetry(apiCall, showNotification = null) {
        if (!this.isOnline) {
            throw new Error('Aucune connexion internet');
        }

        let lastError;

        for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
            try {
                this.retryAttempts = attempt;
                const result = await apiCall();
                this.retryAttempts = 0; // Réinitialiser après succès
                return result;
            } catch (error) {
                lastError = error;

                if (attempt < this.maxRetries) {
                    if (showNotification) {
                        showNotification(
                            `Tentative ${attempt + 1}/${this.maxRetries + 1} échouée. Nouvelle tentative...`,
                            'warning'
                        );
                    }

                    // Délai progressif (backoff exponentiel)
                    const delay = this.retryDelay * Math.pow(2, attempt);
                    await new Promise(resolve => setTimeout(resolve, delay));
                } else {
                    if (showNotification) {
                        showNotification(
                            'Toutes les tentatives ont échoué. Veuillez vérifier votre connexion.',
                            'error'
                        );
                    }
                }
            }
        }

        throw lastError;
    }

    getConnectionStatus() {
        return {
            isOnline: this.isOnline,
            retryAttempts: this.retryAttempts,
            maxRetries: this.maxRetries
        };
    }

    // Cleanup pour supprimer les event listeners
    destroy() {
        window.removeEventListener('online', this.handleOnline.bind(this));
        window.removeEventListener('offline', this.handleOffline.bind(this));
    }
}

export default ConnectionManager;