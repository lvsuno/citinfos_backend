// Données de démonstration pour les notifications

export const demoNotifications = [
    {
        id: 1,
        type: 'like',
        user: {
            id: 'marie-claire',
            name: 'Marie-Claire Dubois',
            avatar: '/avatars/marie-claire.jpg'
        },
        target: 'Magnifique coucher de soleil sur le Mont-Orford aujourd\'hui. La nature nous offre des spectacles extraordinaires...',
        createdAt: new Date(Date.now() - 5 * 60 * 1000), // 5 minutes ago
        isRead: false
    },
    {
        id: 2,
        type: 'comment',
        user: {
            id: 'jean-marc',
            name: 'Jean-Marc Tremblay',
            avatar: '/avatars/jean-marc.jpg'
        },
        target: 'Événement culturel au centre-ville ce weekend',
        content: 'Excellente initiative ! J\'y serai avec plaisir. Merci pour l\'organisation.',
        createdAt: new Date(Date.now() - 15 * 60 * 1000), // 15 minutes ago
        isRead: false
    },
    {
        id: 3,
        type: 'message',
        user: {
            id: 'sophie-martin',
            name: 'Sophie Martin',
            avatar: '/avatars/sophie.jpg'
        },
        content: 'Bonjour ! J\'ai vu votre publication sur le covoiturage. Êtes-vous toujours disponible pour demain ?',
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
        isRead: false
    },
    {
        id: 4,
        type: 'like',
        user: {
            id: 'pierre-luc',
            name: 'Pierre-Luc Gagnon',
            avatar: '/avatars/pierre-luc.jpg'
        },
        target: 'Recommandation de restaurant : La Belle Époque sur la rue Wellington',
        createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000), // 4 hours ago
        isRead: true
    },
    {
        id: 5,
        type: 'follow',
        user: {
            id: 'amelie-roy',
            name: 'Amélie Roy',
            avatar: '/avatars/amelie.jpg'
        },
        createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000), // 6 hours ago
        isRead: true
    },
    {
        id: 6,
        type: 'event',
        content: 'Nouvel événement à Sherbrooke : Festival de musique d\'été - 15-17 juillet',
        createdAt: new Date(Date.now() - 12 * 60 * 60 * 1000), // 12 hours ago
        isRead: true
    },
    {
        id: 7,
        type: 'comment',
        user: {
            id: 'francois-leblanc',
            name: 'François Leblanc',
            avatar: '/avatars/francois.jpg'
        },
        target: 'Problème de stationnement au centre-ville',
        content: 'Je confirme, c\'est un vrai casse-tête. La ville devrait revoir sa politique de stationnement.',
        createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
        isRead: true
    },
    {
        id: 8,
        type: 'like',
        user: {
            id: 'isabelle-cote',
            name: 'Isabelle Côté',
            avatar: '/avatars/isabelle.jpg'
        },
        target: 'Photos du marché public de ce matin. Beaux légumes frais de la région !',
        createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000), // 2 days ago
        isRead: true
    },
    {
        id: 9,
        type: 'message',
        user: {
            id: 'martin-bouchard',
            name: 'Martin Bouchard',
            avatar: '/avatars/martin.jpg'
        },
        content: 'Merci pour les informations sur les pistes cyclables. C\'est exactement ce que je cherchais !',
        createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
        isRead: true
    },
    {
        id: 10,
        type: 'event',
        content: 'Rappel : Collecte de déchets spéciaux demain dans votre secteur',
        createdAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000), // 4 days ago
        isRead: true
    }
];

// Fonction utilitaire pour ajouter une nouvelle notification
export const addNotification = (notification) => {
    return {
        id: Date.now(),
        createdAt: new Date(),
        isRead: false,
        ...notification
    };
};

// Fonction utilitaire pour marquer une notification comme lue
export const markNotificationAsRead = (notifications, notificationId) => {
    return notifications.map(notification =>
        notification.id === notificationId
            ? { ...notification, isRead: true }
            : notification
    );
};

// Fonction utilitaire pour marquer toutes les notifications comme lues
export const markAllNotificationsAsRead = (notifications) => {
    return notifications.map(notification => ({
        ...notification,
        isRead: true
    }));
};

// Types de notifications supportés
export const NOTIFICATION_TYPES = {
    LIKE: 'like',
    COMMENT: 'comment',
    MESSAGE: 'message',
    FOLLOW: 'follow',
    EVENT: 'event'
};