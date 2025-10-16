// Données des posts pour la ville de Sherbrooke
export const sherbrookePosts = [
    // Post très récent pour tester le tri par récence
    {
        id: "post-sherbrooke-recent",
        municipality: "Sherbrooke",
        author: {
            id: "user-recent-poster",
            name: "Emma Leduc",
            avatar: null,
            initials: "EL"
        },
        content: "Bonjour tout le monde ! 👋 Qui a vu le magnifique arc-en-ciel ce matin au-dessus du mont Bellevue ? J'espère que quelqu'un a pris une photo ! 🌈 #Sherbrooke #ArcEnCiel #MontBellevue",
        attachments: [],
        timestamp: new Date(Date.now() - 30 * 60 * 1000), // Il y a 30 minutes
        createdAt: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
        section: "Accueil",
        featured: false,
        reactions: {
            like: 5,
            love: 2,
            haha: 0,
            wow: 3,
            sad: 0,
            angry: 0
        },
        userReaction: null,
        comments: [],
        commentsCount: 0
    },

    {
        id: "post-sherbrooke-1",
        municipality: "Sherbrooke",
        author: {
            id: "user-marie-bernard",
            name: "Marie Bernard",
            avatar: null,
            initials: "MB"
        },
        content: "Magnifique coucher de soleil sur le lac des Nations ce soir ! 🌅 Rien de mieux qu'une promenade au centre-ville après une journée de travail. Sherbrooke nous offre vraiment de beaux paysages urbains. #LacDesNations #Sherbrooke #CoucherDeSoleil",
        attachments: [
            {
                id: "att-1",
                type: "image",
                url: "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=800&h=600&fit=crop",
                alt: "Coucher de soleil sur le lac"
            }
        ],
        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // Il y a 2 heures
        createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        section: "Photographie",
        featured: true, // Post à la une
        reactions: {
            like: 24,
            love: 8,
            haha: 0,
            wow: 12,
            sad: 0,
            angry: 0
        },
        userReaction: "love",
        comments: [
            {
                id: "comment-1",
                author: {
                    id: "user-jean-tremblay",
                    name: "Jean Tremblay",
                    avatar: null,
                    initials: "JT"
                },
                content: "Superbe photo ! J'adore me promener là-bas aussi, surtout en fin de journée.",
                timestamp: new Date(Date.now() - 1.5 * 60 * 60 * 1000),
                reactions: { like: 3 }
            },
            {
                id: "comment-2",
                author: {
                    id: "user-sophie-gagnon",
                    name: "Sophie Gagnon",
                    avatar: null,
                    initials: "SG"
                },
                content: "Les couleurs sont magnifiques ! 😍 Tu étais du côté du parc Jacques-Cartier ?",
                timestamp: new Date(Date.now() - 1 * 60 * 60 * 1000),
                reactions: { like: 2, love: 1 }
            }
        ],
        commentsCount: 2
    },

    {
        id: "post-sherbrooke-2",
        municipality: "Sherbrooke",
        author: {
            id: "user-ville-sherbrooke",
            name: "Ville de Sherbrooke",
            avatar: null,
            initials: "VS"
        },
        content: "📢 ANNONCE IMPORTANTE\n\nLe Festival des traditions du monde de Sherbrooke revient du 15 au 17 octobre ! 🎉\n\nAu programme :\n🎵 Spectacles multiculturels\n🍽️ Délices du monde entier  \n🎨 Ateliers créatifs pour toute la famille\n🏛️ Visites du patrimoine sherbrookois\n\nRendez-vous au parc Jacques-Cartier ! Entrée gratuite.\n\n#FestivalTraditions #Sherbrooke #Culture #Gratuit",
        attachments: [
            {
                id: "att-2",
                type: "image",
                url: "https://images.unsplash.com/photo-1533174072545-7a4b6ad7a6c3?w=800&h=600&fit=crop",
                alt: "Festival multiculturel"
            },
            {
                id: "att-3",
                type: "image",
                url: "https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=400&h=300&fit=crop",
                alt: "Parc Jacques-Cartier"
            }
        ],
        timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000), // Il y a 6 heures
        createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000).toISOString(),
        section: "Événements",
        featured: true, // Post à la une - annonce importante
        reactions: {
            like: 89,
            love: 34,
            haha: 2,
            wow: 15,
            sad: 0,
            angry: 1
        },
        userReaction: null,
        comments: [
            {
                id: "comment-3",
                author: {
                    id: "user-pierre-lavoie",
                    name: "Pierre Lavoie",
                    avatar: null,
                    initials: "PL"
                },
                content: "Excellent ! Mes enfants ont adoré l'année dernière. Merci à la ville pour ces beaux événements gratuits 👏",
                timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000),
                reactions: { like: 12, love: 3 }
            },
            {
                id: "comment-4",
                author: {
                    id: "user-isabelle-cote",
                    name: "Isabelle Côté",
                    avatar: null,
                    initials: "IC"
                },
                content: "Y aura-t-il des food trucks cette année ? J'ai hâte de goûter aux spécialités internationales ! 🌮🍜",
                timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
                reactions: { like: 8, haha: 2 }
            },
            {
                id: "comment-5",
                author: {
                    id: "user-ville-sherbrooke",
                    name: "Ville de Sherbrooke",
                    avatar: null,
                    initials: "VS"
                },
                content: "Oui Isabelle ! Plus de 15 food trucks seront présents avec des cuisines du monde entier 🍕🥟🌯",
                timestamp: new Date(Date.now() - 2.5 * 60 * 60 * 1000),
                reactions: { like: 15, love: 5 }
            }
        ],
        commentsCount: 3
    },

    {
        id: "post-sherbrooke-3",
        municipality: "Sherbrooke",
        author: {
            id: "user-alex-dubois",
            name: "Alexandre Dubois",
            avatar: null,
            initials: "AD"
        },
        content: "Quelqu'un sait-il pourquoi la rue King Ouest est fermée près du Carrefour de l'Estrie ? 🚧 J'ai dû faire un détour de 20 minutes ce matin... Y a-t-il des travaux prévus longtemps ?",
        attachments: [],
        timestamp: new Date(Date.now() - 4 * 60 * 60 * 1000), // Il y a 4 heures
        createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000).toISOString(),
        section: "Transport",
        featured: false, // Post normal
        reactions: {
            like: 15,
            love: 0,
            haha: 3,
            wow: 2,
            sad: 8,
            angry: 12
        },
        userReaction: "sad",
        comments: [
            {
                id: "comment-6",
                author: {
                    id: "user-martin-roy",
                    name: "Martin Roy",
                    avatar: null,
                    initials: "MR"
                },
                content: "Réfection complète de la chaussée jusqu'à la fin octobre selon le site de la ville. Patience ! 😅",
                timestamp: new Date(Date.now() - 3.5 * 60 * 60 * 1000),
                reactions: { like: 8, sad: 2 }
            },
            {
                id: "comment-7",
                author: {
                    id: "user-julie-langlois",
                    name: "Julie Langlois",
                    avatar: null,
                    initials: "JL"
                },
                content: "Pareil pour moi ! J'évite complètement le secteur maintenant. Heureusement que la rue Portland est encore ouverte.",
                timestamp: new Date(Date.now() - 3 * 60 * 60 * 1000),
                reactions: { like: 6, angry: 1 }
            }
        ],
        commentsCount: 2
    },

    {
        id: "post-sherbrooke-4",
        municipality: "Sherbrooke",
        author: {
            id: "user-cafe-local",
            name: "Café du Coin",
            avatar: null,
            initials: "CC"
        },
        content: "☕ NOUVEAU chez nous !\n\nNous avons le plaisir de vous présenter notre nouveau mélange automne : « Érable & Vanille » 🍁\n\nTorréfié localement avec des grains biologiques équitables. Le goût parfait pour accompagner ces belles journées fraîches de septembre !\n\nVenez le découvrir dès maintenant au 245 rue Wellington Nord. Première tasse offerte aux 20 premiers clients ! 🎁\n\n#CaféLocal #Sherbrooke #TorréfactionArtisanale #Automne",
        attachments: [
            {
                id: "att-4",
                type: "image",
                url: "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=600&h=400&fit=crop",
                alt: "Tasse de café avec grains"
            },
            {
                id: "att-5",
                type: "image",
                url: "https://images.unsplash.com/photo-1506619216599-9d16d0903dfd?w=400&h=300&fit=crop",
                alt: "Intérieur chaleureux du café"
            },
            {
                id: "att-6",
                type: "image",
                url: "https://images.unsplash.com/photo-1442550528053-c431ecb55509?w=400&h=300&fit=crop",
                alt: "Grains de café torréfiés"
            }
        ],
        timestamp: new Date(Date.now() - 8 * 60 * 60 * 1000), // Il y a 8 heures
        createdAt: new Date(Date.now() - 8 * 60 * 60 * 1000).toISOString(),
        section: "Commerces",
        featured: false, // Post normal
        reactions: {
            like: 67,
            love: 23,
            haha: 1,
            wow: 5,
            sad: 0,
            angry: 0
        },
        userReaction: "like",
        comments: [
            {
                id: "comment-8",
                author: {
                    id: "user-caroline-martin",
                    name: "Caroline Martin",
                    avatar: null,
                    initials: "CM"
                },
                content: "Miam ! J'adore vos mélanges saisonniers. Je passe demain matin avant le travail ☕😊",
                timestamp: new Date(Date.now() - 6 * 60 * 60 * 1000),
                reactions: { like: 5, love: 2 }
            },
            {
                id: "comment-9",
                author: {
                    id: "user-robert-gagne",
                    name: "Robert Gagné",
                    avatar: null,
                    initials: "RG"
                },
                content: "Excellente initiative ! C'est important de soutenir les commerces locaux. Votre café est vraiment délicieux 👍",
                timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
                reactions: { like: 8, love: 1 }
            },
            {
                id: "comment-10",
                author: {
                    id: "user-cafe-local",
                    name: "Café du Coin",
                    avatar: null,
                    initials: "CC"
                },
                content: "Merci Caroline et Robert ! Nous sommes ravis de faire partie de la communauté sherbrookoise ❤️",
                timestamp: new Date(Date.now() - 4.5 * 60 * 60 * 1000),
                reactions: { like: 12, love: 4 }
            }
        ],
        commentsCount: 3
    }
];

// Fonction pour filtrer les posts par municipalité
export const getPostsByMunicipality = (municipalityName) => {
    return sherbrookePosts.filter(post =>
        post.municipality.toLowerCase() === municipalityName.toLowerCase()
    );
};

// Fonction pour filtrer les posts par municipalité et section
export const getPostsByMunicipalityAndSection = (municipalityName, section) => {
    return sherbrookePosts.filter(post =>
        post.municipality.toLowerCase() === municipalityName.toLowerCase() &&
        post.section.toLowerCase() === section.toLowerCase()
    );
};

// Fonction utilitaire pour formater le temps
export const formatTimeAgo = (timestamp) => {
    const now = new Date();
    const diffInMs = now - timestamp;
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

    if (diffInMinutes < 1) return "À l'instant";
    if (diffInMinutes < 60) return `${diffInMinutes} min`;
    if (diffInHours < 24) return `${diffInHours}h`;
    if (diffInDays === 1) return "Hier";
    if (diffInDays < 7) return `${diffInDays} jours`;

    return timestamp.toLocaleDateString('fr-CA', {
        day: 'numeric',
        month: 'short'
    });
};

// Fonction pour obtenir le total des réactions
export const getTotalReactions = (reactions) => {
    return Object.values(reactions).reduce((total, count) => total + count, 0);
};

// Fonction pour obtenir les icônes de réactions les plus populaires
export const getTopReactionIcons = (reactions, limit = 3) => {
    const reactionEmojis = {
        like: '👍',
        love: '❤️',
        haha: '😂',
        wow: '😮',
        sad: '😢',
        angry: '😠'
    };

    return Object.entries(reactions)
        .filter(([type, count]) => count > 0)
        .sort(([, a], [, b]) => b - a)
        .slice(0, limit)
        .map(([type]) => reactionEmojis[type]);
};