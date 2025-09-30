// Utilisateurs statiques pour test des rôles
export const STATIC_USERS = [
    {
        id: 1,
        email: 'admin@communaute.local',
        password: 'admin123',
        firstName: 'Elvis',
        lastName: 'Togban',
        role: 'administrator',
        roleDisplay: 'Administrateur',
        avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face&auto=format',
        location: {
            city: 'Sherbrooke',
            region: 'Estrie',
            province: 'Québec'
        },
        joinedDate: '2024-01-15',
        permissions: [
            'manage_users',
            'manage_communities',
            'manage_events',
            'manage_content',
            'view_analytics',
            'system_settings',
            'moderate_content',
            'ban_users'
        ],
        stats: {
            communitiesManaged: 12,
            usersManaged: 2847,
            eventsCreated: 45
        }
    },
    {
        id: 2,
        email: 'moderateur@communaute.local',
        password: 'modo123',
        firstName: 'Djemel',
        lastName: 'Ziou',
        role: 'moderator',
        roleDisplay: 'Modérateur',
        avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face&auto=format',
        location: {
            city: 'Sherbrooke',
            region: 'Estrie',
            province: 'Québec'
        },
        joinedDate: '2024-03-20',
        permissions: [
            'moderate_content',
            'manage_events',
            'warn_users',
            'delete_posts',
            'manage_reports',
            'view_user_details'
        ],
        stats: {
            communitiesModerated: 5,
            postsModerated: 156,
            eventsManaged: 23,
            reportsHandled: 89
        }
    },
    {
        id: 3,
        email: 'utilisateur@communaute.local',
        password: 'user123',
        firstName: 'Islam',
        lastName: 'Benamirouche',
        role: 'user',
        roleDisplay: 'Utilisateur',
        avatar: '/assets/islam.jpg',
        location: {
            city: 'Sherbrooke',
            region: 'Estrie',
            province: 'Québec'
        },
        joinedDate: '2024-06-10',
        permissions: [
            'create_posts',
            'comment_posts',
            'join_communities',
            'attend_events',
            'report_content'
        ],
        stats: {
            communitiesJoined: 8,
            postsCreated: 34,
            eventsAttended: 12,
            connectionsAcceptMade: 67
        }
    }
];

// Fonction pour authentifier un utilisateur
export const authenticateUser = (email, password) => {
    const user = STATIC_USERS.find(
        u => u.email.toLowerCase() === email.toLowerCase() && u.password === password
    );

    if (user) {
        // Ne pas retourner le mot de passe dans la réponse
        const { password: _, ...userWithoutPassword } = user;
        return userWithoutPassword;
    }

    return null;
};

// Fonction pour obtenir un utilisateur par ID
export const getUserById = (id) => {
    const user = STATIC_USERS.find(u => u.id === id);
    if (user) {
        const { password: _, ...userWithoutPassword } = user;
        return userWithoutPassword;
    }
    return null;
};

// Fonction pour vérifier les permissions
export const hasPermission = (user, permission) => {
    return user && user.permissions && user.permissions.includes(permission);
};

// Constantes pour les rôles
export const USER_ROLES = {
    ADMINISTRATOR: 'administrator',
    MODERATOR: 'moderator',
    USER: 'user'
};

// Fonction pour obtenir la couleur du rôle - avec la nouvelle palette
export const getRoleColor = (role) => {
    switch (role) {
        case USER_ROLES.ADMINISTRATOR:
            return '#84CC16'; // Lime Green pour l'admin - couleur d'accent
        case USER_ROLES.MODERATOR:
            return '#06B6D4'; // Cyan pour le modérateur - couleur secondaire
        case USER_ROLES.USER:
            return '#1E293B'; // Deep Navy pour l'utilisateur - couleur primaire
        default:
            return '#1E293B'; // Deep Navy par défaut
    }
};

// Fonction pour obtenir la couleur de fond du rôle
export const getRoleBackgroundColor = (role) => {
    switch (role) {
        case USER_ROLES.ADMINISTRATOR:
            return '#F7FEE7'; // Fond lime très clair
        case USER_ROLES.MODERATOR:
            return '#ECFEFF'; // Fond cyan très clair
        case USER_ROLES.USER:
            return '#F1F5F9'; // Light Gray
        default:
            return '#F1F5F9'; // Light Gray par défaut
    }
};

// Messages d'information pour les utilisateurs de test
export const TEST_USERS_INFO = {
    instructions: `
Utilisateurs de test disponibles :

🔴 ADMINISTRATEUR
Email: admin@communaute.local
Mot de passe: admin123
Permissions: Accès complet au système

🟠 MODÉRATEUR
Email: moderateur@communaute.local
Mot de passe: modo123
Permissions: Modération et gestion d'événements

🔵 UTILISATEUR
Email: utilisateur@communaute.local
Mot de passe: user123
Permissions: Utilisation standard de la plateforme
  `,

    getWelcomeMessage: (user) => {
        switch (user.role) {
            case USER_ROLES.ADMINISTRATOR:
                return `Bienvenue ${user.firstName} ! En tant qu'administrateur, vous avez accès à toutes les fonctionnalités de gestion de la plateforme.`;
            case USER_ROLES.MODERATOR:
                return `Bienvenue ${user.firstName} ! En tant que modérateur, vous pouvez gérer le contenu et les événements de votre région.`;
            case USER_ROLES.USER:
                return `Bienvenue ${user.firstName} ! Découvrez votre communauté locale et participez aux discussions.`;
            default:
                return `Bienvenue sur la plateforme communautaire !`;
        }
    }
};