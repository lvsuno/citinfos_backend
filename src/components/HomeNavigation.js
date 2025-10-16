import React from 'react';
import { 
    Star as StarIcon, 
    Schedule as RecentIcon,
    TrendingUp as TrendingIcon 
} from '@mui/icons-material';
import styles from './HomeNavigation.module.css';

const HomeNavigation = ({ activeSort = 'recent', onSortChange }) => {
    const navigationOptions = [
        {
            key: 'featured',
            label: 'À la une',
            icon: StarIcon,
            description: 'Publications mises en avant'
        },
        {
            key: 'recent',
            label: 'Les plus récents',
            icon: RecentIcon,
            description: 'Publications les plus récentes'
        }
    ];

    const handleSortChange = (sortKey) => {
        if (onSortChange && sortKey !== activeSort) {
            onSortChange(sortKey);
        }
    };

    return (
        <div className={styles.homeNavigation}>
            <div className={styles.navigationHeader}>
                <TrendingIcon className={styles.headerIcon} />
                <h3 className={styles.headerTitle}>Explorer le contenu</h3>
            </div>
            
            <div className={styles.navigationButtons}>
                {navigationOptions.map((option) => {
                    const IconComponent = option.icon;
                    const isActive = activeSort === option.key;
                    
                    return (
                        <button
                            key={option.key}
                            className={`${styles.navButton} ${isActive ? styles.active : ''}`}
                            onClick={() => handleSortChange(option.key)}
                            title={option.description}
                            aria-pressed={isActive}
                        >
                            <IconComponent className={styles.navIcon} />
                            <span className={styles.navLabel}>{option.label}</span>
                            {isActive && <div className={styles.activeIndicator} />}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default HomeNavigation;