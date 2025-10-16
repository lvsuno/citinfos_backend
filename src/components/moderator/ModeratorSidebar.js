import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Box,
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
    Divider,
    Avatar,
    Chip
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    Gavel as ModerationIcon,
    Assignment as AssignmentIcon,
    BarChart as AnalyticsIcon,
    Settings as SettingsIcon,
    Security as SecurityIcon,
    Flag as FlagIcon,
    Person as PersonIcon,
    ExitToApp as LogoutIcon,
    Visibility as VisibilityIcon,
    Report as ReportIcon
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import styles from './ModeratorSidebar.module.css';

const SIDEBAR_WIDTH = 280;

const ModeratorSidebar = ({ activeSection, onSectionChange, user }) => {
    const { logout } = useAuth();
    const navigate = useNavigate();

    const menuItems = [
        {
            id: 'overview',
            label: 'Vue d\'ensemble',
            icon: <DashboardIcon />,
            active: true
        },
        {
            id: 'moderation-feed',
            label: 'Fil de modération',
            icon: <ModerationIcon />,
            active: true
        },
        {
            id: 'reported-content',
            label: 'Contenu signalé',
            icon: <FlagIcon />,
            active: true
        },
        {
            id: 'pending-review',
            label: 'En attente de révision',
            icon: <VisibilityIcon />,
            active: true
        },
        {
            id: 'reports',
            label: 'Rapports',
            icon: <ReportIcon />,
            active: false,
            comingSoon: true
        },
        {
            id: 'analytics',
            label: 'Statistiques',
            icon: <AnalyticsIcon />,
            active: false,
            comingSoon: true
        },
        {
            id: 'settings',
            label: 'Paramètres',
            icon: <SettingsIcon />,
            active: false,
            comingSoon: true
        }
    ];

    const handleLogout = async () => {
        try {
            console.log('🚪 Moderator logout initiated');
            await logout();
            console.log('✅ Moderator logout completed, redirecting to login');
            navigate('/login', { replace: true });
        } catch (error) {
            console.error('❌ Erreur lors de la déconnexion modérateur:', error);
            navigate('/login', { replace: true });
        }
    };

    const handleMenuItemClick = (item) => {
        if (!item.active) return;
        
        // Navigation spécifique pour certaines sections
        if (item.id === 'moderation-feed') {
            navigate('/moderator/feed');
        } else if (item.id === 'reported-content') {
            navigate('/moderator/reported');
        } else if (item.id === 'pending-review') {
            navigate('/moderator/pending');
        } else {
            // Utiliser le callback pour les autres sections
            onSectionChange(item.id);
        }
    };

    return (
        <Drawer
            variant="permanent"
            className={styles.sidebar}
            sx={{
                width: SIDEBAR_WIDTH,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                    width: SIDEBAR_WIDTH,
                    boxSizing: 'border-box',
                    background: 'linear-gradient(180deg, #2d1b69 0%, #1e1b4b 100%)',
                    color: 'white',
                    borderRight: 'none'
                },
            }}
        >
            {/* Header avec infos modérateur */}
            <Box className={styles.sidebarHeader}>
                <Avatar
                    src={user?.profile_picture}
                    className={styles.moderatorAvatar}
                    sx={{ width: 50, height: 50 }}
                >
                    {user?.username?.charAt(0).toUpperCase()}
                </Avatar>
                <Box className={styles.moderatorInfo}>
                    <Typography variant="h6" className={styles.moderatorName}>
                        {user?.username}
                    </Typography>
                    <Chip
                        label="Modérateur"
                        size="small"
                        className={styles.moderatorChip}
                        sx={{
                            background: 'linear-gradient(45deg, #7c3aed, #6366f1)',
                            color: 'white',
                            fontWeight: 600,
                            fontSize: '0.75rem'
                        }}
                    />
                </Box>
            </Box>

            <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.2)' }} />

            {/* Menu de navigation */}
            <List className={styles.menuList}>
                {menuItems.map((item) => (
                    <ListItem key={item.id} disablePadding>
                        <ListItemButton
                            selected={activeSection === item.id}
                            onClick={() => handleMenuItemClick(item)}
                            disabled={!item.active}
                            className={`${styles.menuItem} ${activeSection === item.id ? styles.active : ''
                                } ${!item.active ? styles.disabled : ''}`}
                            sx={{
                                '&.Mui-selected': {
                                    background: 'linear-gradient(45deg, #7c3aed, #6366f1)',
                                    '&:hover': {
                                        background: 'linear-gradient(45deg, #6366f1, #4f46e5)',
                                    }
                                },
                                '&:hover': {
                                    background: 'rgba(255, 255, 255, 0.1)',
                                },
                                '&.Mui-disabled': {
                                    opacity: 0.5,
                                    color: 'rgba(255, 255, 255, 0.5)'
                                }
                            }}
                        >
                            <ListItemIcon
                                sx={{
                                    color: activeSection === item.id ? 'white' : 'rgba(255, 255, 255, 0.8)',
                                    minWidth: 40
                                }}
                            >
                                {item.icon}
                            </ListItemIcon>
                            <ListItemText
                                primary={item.label}
                                primaryTypographyProps={{
                                    fontSize: '0.875rem',
                                    fontWeight: activeSection === item.id ? 600 : 400
                                }}
                            />
                            {item.comingSoon && (
                                <Chip
                                    label="Bientôt"
                                    size="small"
                                    sx={{
                                        height: 20,
                                        fontSize: '0.6rem',
                                        background: 'rgba(255, 255, 255, 0.2)',
                                        color: 'white'
                                    }}
                                />
                            )}
                        </ListItemButton>
                    </ListItem>
                ))}
            </List>

            {/* Bouton profil */}
            <Box sx={{ px: 1, pb: 1 }}>
                <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.2)', mb: 1 }} />
                <ListItem disablePadding>
                    <ListItemButton
                        onClick={() => navigate('/moderator/profile')}
                        className={styles.profileButton}
                        sx={{
                            borderRadius: 2,
                            '&:hover': {
                                background: 'rgba(34, 197, 94, 0.2)',
                            }
                        }}
                    >
                        <ListItemIcon sx={{ color: '#22c55e', minWidth: 40 }}>
                            <PersonIcon />
                        </ListItemIcon>
                        <ListItemText
                            primary="Mon Profil"
                            primaryTypographyProps={{
                                fontSize: '0.875rem',
                                color: '#22c55e',
                                fontWeight: 500
                            }}
                        />
                    </ListItemButton>
                </ListItem>
            </Box>

            {/* Bouton de déconnexion */}
            <Box className={styles.sidebarFooter}>
                <Divider sx={{ borderColor: 'rgba(255, 255, 255, 0.2)', mb: 1 }} />
                <ListItem disablePadding>
                    <ListItemButton
                        onClick={handleLogout}
                        className={styles.logoutButton}
                        sx={{
                            '&:hover': {
                                background: 'rgba(239, 68, 68, 0.2)',
                            }
                        }}
                    >
                        <ListItemIcon sx={{ color: '#ef4444', minWidth: 40 }}>
                            <LogoutIcon />
                        </ListItemIcon>
                        <ListItemText
                            primary="Déconnexion"
                            primaryTypographyProps={{
                                fontSize: '0.875rem',
                                color: '#ef4444'
                            }}
                        />
                    </ListItemButton>
                </ListItem>
            </Box>
        </Drawer>
    );
};

export default ModeratorSidebar;