import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const DebugUserInfo = () => {
    const { user } = useAuth();

    if (!user) return <div>Aucun utilisateur connecté</div>;

    return (
        <div style={{
            position: 'fixed',
            top: '70px',
            right: '10px',
            background: 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '10px',
            fontSize: '12px',
            borderRadius: '5px',
            zIndex: 9999,
            maxWidth: '300px'
        }}>
            <h4>Debug User Info:</h4>
            <p><strong>ID:</strong> {user.id}</p>
            <p><strong>Nom:</strong> {user.firstName} {user.lastName}</p>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Avatar:</strong> {user.avatar || 'AUCUN'}</p>
            {user.avatar && (
                <div>
                    <p><strong>Test avatar:</strong></p>
                    <img
                        src={user.avatar}
                        alt="Test"
                        style={{ width: '50px', height: '50px', objectFit: 'cover' }}
                        onError={() => console.log('ERREUR: Image avatar ne peut pas se charger')}
                        onLoad={() => console.log('SUCCESS: Avatar chargé avec succès')}
                    />
                </div>
            )}
        </div>
    );
};

export default DebugUserInfo;