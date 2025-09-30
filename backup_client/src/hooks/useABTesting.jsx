import { useState, useEffect, createContext, useContext } from 'react';
import PropTypes from 'prop-types';

// Mock A/B Testing Client
const abTestingClient = {
  async getSimilarUsers(userId) {
    return {
      experiment_group: Math.random() > 0.5 ? 'control' : 'test',
      experiment_id: 'active-experiment',
      user_id: userId
    };
  },

  async getExperimentVariant(experimentId) {
    return {
      variant: Math.random() > 0.5 ? 'A' : 'B',
      experiment_id: experimentId
    };
  }
};

// Create A/B Testing Context
const ABTestingContext = createContext(null);

export const ABTestingProvider = ({ children }) => {
  const [currentExperiment, setCurrentExperiment] = useState(null);
  const [userGroup, setUserGroup] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const getSimilarUsers = async (userId) => {
    setIsLoading(true);
    try {
      const result = await abTestingClient.getSimilarUsers(userId);
      setCurrentExperiment('active-experiment');
      setUserGroup(result.experiment_group || null);
      return result;
    } catch (error) {
      console.error('Error getting similar users:', error);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  const getExperimentVariant = async (experimentId) => {
    try {
      const result = await abTestingClient.getExperimentVariant(experimentId);
      return result.variant;
    } catch (error) {
      console.error('Error getting experiment variant:', error);
      return 'A'; // Default variant
    }
  };

  const isInExperiment = currentExperiment !== null && userGroup !== null;

  const value = {
    currentExperiment,
    userGroup,
    isLoading,
    isInExperiment,
    getSimilarUsers,
    getExperimentVariant,
  };

  return (
    <ABTestingContext.Provider value={value}>
      {children}
    </ABTestingContext.Provider>
  );
};

ABTestingProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Hook to use A/B Testing context
export const useABTesting = () => {
  const context = useContext(ABTestingContext);

  if (!context) {
    throw new Error('useABTesting must be used within an ABTestingProvider');
  }

  return context;
};

export default useABTesting;
