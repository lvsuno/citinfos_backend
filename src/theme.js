import { createTheme } from '@mui/material/styles';

// Nouvelle palette de couleurs moderne : Deep Navy, Cyan, Lime Green, Neutral
const theme = createTheme({
    typography: {
        fontFamily: [
            'Poppins',
            'SF Pro Display',
            '-apple-system',
            'BlinkMacSystemFont',
            'Segoe UI Variable',
            'Segoe UI',
            'Roboto',
            'Oxygen',
            'Ubuntu',
            'Cantarell',
            'sans-serif'
        ].join(','),
        h1: {
            fontWeight: 700,
        },
        h2: {
            fontWeight: 700,
        },
        h3: {
            fontWeight: 600,
        },
        h4: {
            fontWeight: 600,
        },
        h5: {
            fontWeight: 600,
        },
        h6: {
            fontWeight: 600,
        },
    },
    palette: {
        // Primary: Deep Navy - couleur principale élégante et professionnelle
        primary: {
            main: '#1E293B', // Deep Navy
            light: '#334155', // Navy plus clair
            dark: '#0F172A', // Charcoal (très sombre)
            contrastText: '#ffffff',
        },

        // Secondary: Cyan - couleur secondaire moderne et énergique
        secondary: {
            main: '#06B6D4', // Cyan
            light: '#22D3EE', // Cyan clair
            dark: '#0891B2', // Cyan foncé
            contrastText: '#ffffff',
        },

        // Accent: Lime Green - couleur d'accent vive et moderne
        accent: {
            main: '#84CC16', // Lime Green
            light: '#A3E635', // Lime plus clair
            dark: '#65A30D', // Lime plus foncé
            contrastText: '#ffffff',
        },

        // Backgrounds avec les couleurs neutres
        background: {
            default: '#F1F5F9', // Light Gray - arrière-plan principal
            paper: '#ffffff', // Blanc pur pour les cartes
            subtle: '#F8FAFC', // Gris très clair pour les zones subtiles
        },

        // Textes avec Deep Navy et Charcoal
        text: {
            primary: '#0F172A', // Charcoal pour le texte principal
            secondary: '#1E293B', // Deep Navy pour le texte secondaire
            disabled: '#94A3B8', // Gris pour le texte désactivé
        },

        // États avec la nouvelle palette
        success: {
            main: '#84CC16', // Lime Green pour le succès
            light: '#A3E635',
            dark: '#65A30D',
        },
        warning: {
            main: '#F59E0B', // Orange pour les avertissements
            light: '#FBBF24',
            dark: '#D97706',
        },
        error: {
            main: '#EF4444', // Rouge pour les erreurs
            light: '#F87171',
            dark: '#DC2626',
        },
        info: {
            main: '#06B6D4', // Cyan pour les informations
            light: '#22D3EE',
            dark: '#0891B2',
        },

        // Nuances de gris neutres
        grey: {
            50: '#F8FAFC',
            100: '#F1F5F9', // Light Gray principal
            200: '#E2E8F0',
            300: '#CBD5E1',
            400: '#94A3B8',
            500: '#64748B',
            600: '#475569',
            700: '#334155',
            800: '#1E293B', // Deep Navy
            900: '#0F172A', // Charcoal
        },
    },

    components: {
        // Boutons avec style moderne
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    padding: '10px 24px',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                    textTransform: 'none',
                    boxShadow: 'none',
                    transition: 'all 0.2s ease-in-out',
                    '&:hover': {
                        boxShadow: '0 4px 12px rgba(37, 99, 235, 0.15)',
                        transform: 'translateY(-1px)',
                    },
                },
                containedPrimary: {
                    background: 'linear-gradient(135deg, #2563eb 0%, #3b82f6 100%)',
                    color: '#ffffff',
                    '&:hover': {
                        background: 'linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%)',
                        boxShadow: '0 8px 25px rgba(37, 99, 235, 0.25)',
                    },
                },
                outlinedPrimary: {
                    borderColor: '#e2e8f0',
                    color: '#2563eb',
                    backgroundColor: '#ffffff',
                    '&:hover': {
                        borderColor: '#2563eb',
                        backgroundColor: '#f8fafc',
                        boxShadow: '0 4px 12px rgba(37, 99, 235, 0.1)',
                    },
                },
            },
        },

        // AppBar avec style épuré
        MuiAppBar: {
            styleOverrides: {
                root: {
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    backgroundColor: '#ffffff',
                    color: '#1e293b',
                    borderBottom: '1px solid #e2e8f0',
                },
            },
        },

        // Cartes avec design moderne
        MuiCard: {
            styleOverrides: {
                root: {
                    borderRadius: 12,
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                    border: '1px solid #e2e8f0',
                    backgroundColor: '#ffffff',
                    transition: 'all 0.3s ease-in-out',
                    '&:hover': {
                        boxShadow: '0 8px 25px rgba(0,0,0,0.1)',
                        transform: 'translateY(-2px)',
                        borderColor: '#cbd5e1',
                    },
                },
            },
        },

        // Inputs avec style cohérent
        MuiTextField: {
            styleOverrides: {
                root: {
                    '& .MuiOutlinedInput-root': {
                        borderRadius: 8,
                        backgroundColor: '#ffffff',
                        '& fieldset': {
                            borderColor: '#e2e8f0',
                        },
                        '&:hover fieldset': {
                            borderColor: '#cbd5e1',
                        },
                        '&.Mui-focused fieldset': {
                            borderColor: '#2563eb',
                            borderWidth: 2,
                        },
                    },
                },
            },
        },

        // Chips avec design moderne
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: 8,
                    fontWeight: 500,
                    fontSize: '0.8rem',
                },
                filled: {
                    backgroundColor: '#f1f5f9',
                    color: '#475569',
                },
                outlined: {
                    borderColor: '#e2e8f0',
                    color: '#64748b',
                },
            },
        },

        // Container avec padding cohérent
        MuiContainer: {
            styleOverrides: {
                root: {
                    paddingLeft: '24px',
                    paddingRight: '24px',
                },
            },
        },

        // Paper avec style moderne
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundColor: '#ffffff',
                    borderRadius: 12,
                    border: '1px solid #e2e8f0',
                },
                elevation1: {
                    boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                },
                elevation2: {
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
                },
                elevation8: {
                    boxShadow: '0 25px 50px rgba(0,0,0,0.15)',
                },
            },
        },
    },

    spacing: 8,

    breakpoints: {
        values: {
            xs: 0,
            sm: 600,
            md: 960,
            lg: 1280,
            xl: 1920,
        },
    },

    // Définition des nuances personnalisées
    shape: {
        borderRadius: 8,
    },
});

// Palette personnalisée pour les rôles - nuances harmonieuses de bleu et gris
theme.palette.roles = {
    administrator: {
        main: '#1e40af', // Bleu foncé pour l'admin
        light: '#3b82f6',
        bg: '#eff6ff',
    },
    moderator: {
        main: '#64748b', // Gris bleuté pour le modérateur
        light: '#94a3b8',
        bg: '#f8fafc',
    },
    user: {
        main: '#3b82f6', // Bleu standard pour l'utilisateur
        light: '#60a5fa',
        bg: '#f0f9ff',
    },
};

export default theme;