import React, { createContext, useContext, useState, useCallback } from 'react';
import apiService from '../api/apiService';

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [currentPool, setCurrentPool] = useState(null);
  const [userPools, setUserPools] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [teams, setTeams] = useState([]);
  const [fixtures, setFixtures] = useState([]);
  const [userPicks, setUserPicks] = useState([]);
  const [currentGameweek, setCurrentGameweek] = useState(18);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const clearError = () => setError(null);

  const loadUserData = useCallback(async (userId) => {
    setLoading(true);
    setError(null);
    try {
      const userData = await apiService.getUser(userId);
      setUser(userData);
      
      const pools = await apiService.getUserPools(userId);
      setUserPools(pools);
      
      // If user has pools, load the first one by default
      if (pools.length > 0) {
        const poolId = pools[0].pool_id;
        await loadPoolData(userId, poolId);
      }
    } catch (err) {
      setError(err.message || 'Failed to load user data');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPoolData = useCallback(async (userId, poolId) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getHomeScreenData(userId, poolId);
      setUser(data.user);
      setCurrentPool(data.pool);
      setLeaderboard(data.leaderboard);
      setTeams(data.teams);
      setFixtures(data.fixtures);
      setUserPicks(data.userPicks);
      setCurrentGameweek(data.currentGameweek);
    } catch (err) {
      setError(err.message || 'Failed to load pool data');
    } finally {
      setLoading(false);
    }
  }, []);

  const makePick = useCallback(async (teamId, fixtureId) => {
    if (!user || !currentPool) return;
    
    setLoading(true);
    setError(null);
    try {
      const pick = await apiService.createPick({
        pool_id: currentPool.id,
        user_id: user.id,
        team_id: teamId,
        fixture_id: fixtureId,
      });
      
      // Refresh data after pick
      await loadPoolData(user.id, currentPool.id);
      return pick;
    } catch (err) {
      setError(err.message || 'Failed to make pick');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user, currentPool, loadPoolData]);

  const joinPool = useCallback(async (poolId) => {
    if (!user) return;
    
    setLoading(true);
    setError(null);
    try {
      await apiService.joinPool(poolId, user.id);
      await loadUserData(user.id);
    } catch (err) {
      setError(err.message || 'Failed to join pool');
      throw err;
    } finally {
      setLoading(false);
    }
  }, [user, loadUserData]);

  const value = {
    // State
    user,
    currentPool,
    userPools,
    leaderboard,
    teams,
    fixtures,
    userPicks,
    currentGameweek,
    loading,
    error,
    
    // Actions
    setUser,
    setCurrentPool,
    loadUserData,
    loadPoolData,
    makePick,
    joinPool,
    clearError,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
