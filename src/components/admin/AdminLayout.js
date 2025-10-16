import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box } from '@mui/material';
import AdminSidebar from './AdminSidebar';
import { useAuth } from '../../contexts/AuthContext';

const AdminLayout = ({ children, activeSection = 'overview' }) => {
    const { user } = useAuth();
    const navigate = useNavigate();

    const handleSectionChange = (sectionId) => {
        console.log('🔄 Admin section change:', sectionId);
        
        // Navigation spécifique pour les différentes sections
        switch (sectionId) {
            case 'overview':
                navigate('/admin/dashboard');
                break;
            case 'users':
                navigate('/admin/users');
                break;
            case 'create-user':
                navigate('/admin/create-user');
                break;
            case 'municipalities':
                navigate('/admin/municipalities');
                break;
            case 'support':
                navigate('/admin/support');
                break;
            case 'profile':
                navigate('/admin/profile');
                break;
            case 'analytics':
                // À implémenter plus tard
                console.log('Analytics section - à implémenter');
                break;
            case 'content':
                // À implémenter plus tard
                console.log('Content moderation section - à implémenter');
                break;
            case 'security':
                // À implémenter plus tard
                console.log('Security section - à implémenter');
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
            <AdminSidebar 
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

export default AdminLayout;