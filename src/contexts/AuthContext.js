import React, { createContext, useContext, useState, useEffect } from 'react';
import { authenticateUser, getUserById, hasPermission } from '../data/users';
import { getUserRedirectUrl } from '../data/municipalitiesUtils';

const AuthContext = createContext();

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Vérifier si un utilisateur est déjà connecté (localStorage)
        const savedUser = localStorage.getItem('currentUser');
        if (savedUser) {
            try {
                const parsedUser = JSON.parse(savedUser);
                console.log('Utilisateur chargé depuis localStorage:', parsedUser);

                // Vérifier si l'utilisateur a un avatar, sinon le récupérer depuis STATIC_USERS
                if (!parsedUser.avatar && parsedUser.id) {
                    const fullUser = getUserById(parsedUser.id);
                    if (fullUser && fullUser.avatar) {
                        const updatedUser = { ...parsedUser, avatar: fullUser.avatar };
                        setUser(updatedUser);
                        localStorage.setItem('currentUser', JSON.stringify(updatedUser));
                        console.log('Avatar mis à jour:', updatedUser.avatar);
                    } else {
                        setUser(parsedUser);
                    }
                } else {
                    setUser(parsedUser);
                }
            } catch (error) {
                console.error('Erreur lors du chargement de l\'utilisateur sauvegardé:', error);
                localStorage.removeItem('currentUser');
            }
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        try {
            const authenticatedUser = authenticateUser(email, password);
            if (authenticatedUser) {
                // S'assurer que toutes les données utilisateur sont incluses, y compris l'avatar
                const fullUser = getUserById(authenticatedUser.id);
                const userWithAllData = { ...authenticatedUser, ...fullUser };

                console.log('Login - données utilisateur complètes:', userWithAllData);
                console.log('Login - avatar:', userWithAllData.avatar);

                setUser(userWithAllData);
                localStorage.setItem('currentUser', JSON.stringify(userWithAllData));
                return { success: true, user: userWithAllData };
            } else {
                return { success: false, error: 'Email ou mot de passe incorrect' };
            }
        } catch (error) {
            console.error('Erreur login:', error);
            return { success: false, error: 'Erreur lors de la connexion' };
        }
    };

    const signUp = async (userData) => {
        try {
            // Simulation d'une inscription (à remplacer par votre logique réelle)
            const newUser = {
                id: Date.now(),
                email: userData.email,
                firstName: userData.firstName,
                lastName: userData.lastName,
                municipality: userData.municipality,
                role: 'citizen',
                isVerified: false
            };

            setUser(newUser);
            localStorage.setItem('currentUser', JSON.stringify(newUser));
            return { success: true, user: newUser };
        } catch (error) {
            throw new Error('Erreur lors de l\'inscription');
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem('currentUser');
    };

    const updateUser = (updatedUserData) => {
        setUser(updatedUserData);
        localStorage.setItem('currentUser', JSON.stringify(updatedUserData));
    };

    const refreshUserData = () => {
        if (user?.id) {
            const freshData = getUserById(user.id);
            if (freshData) {
                console.log('Rafraîchissement des données utilisateur:', freshData);
                setUser(freshData);
                localStorage.setItem('currentUser', JSON.stringify(freshData));
            }
        }
    };

    const checkPermission = (permission) => {
        return hasPermission(user, permission);
    };

    const isRole = (role) => {
        return user && user.role === role;
    };

    const getHomeUrl = () => {
        return getUserRedirectUrl(user);
    };

    const value = {
        user,
        login,
        signUp,
        logout,
        updateUser,
        refreshUserData,
        loading,
        isAuthenticated: !!user,
        checkPermission,
        isRole,
        getHomeUrl
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};