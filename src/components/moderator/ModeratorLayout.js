import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box } from '@mui/material';
import ModeratorSidebar from './ModeratorSidebar';
import { useAuth } from '../../contexts/AuthContext';

const ModeratorLayout = ({ children, activeSection = 'overview' }) => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const handleSectionChange = (sectionId) => {
        console.log('🔄 Moderator section change:', sectionId);
        
        // Navigation spécifique pour les différentes sections
        switch (sectionId) {
            case 'overview':
                navigate('/moderator/dashboard');
                break;
            case 'moderation-feed':
                navigate('/moderator/feed');
                break;
            case 'reported-content':
                navigate('/moderator/reported');
                break;
            case 'pending-review':
                navigate('/moderator/pending');
                break;
            case 'profile':
                navigate('/moderator/profile');
                break;
            case 'reports':
                // À implémenter plus tard
                console.log('Reports section - à implémenter');
                break;
            case 'analytics':
                // À implémenter plus tard
                console.log('Analytics section - à implémenter');
                break;
            case 'settings':
                // À implémenter plus tard
                console.log('Settings section - à implémenter');
                break;
            default:
                console.log('Unknown section:', sectionId);
        }
    };

    return (
        <Box display="flex" minHeight="100vh">
            <ModeratorSidebar 
                activeSection={activeSection}
                onSectionChange={handleSectionChange}
                user={user}
            />
            <Box component="main" sx={{ flexGrow: 1 }}>
                {children}
            </Box>
        </Box>
    );
};

export default ModeratorLayout;