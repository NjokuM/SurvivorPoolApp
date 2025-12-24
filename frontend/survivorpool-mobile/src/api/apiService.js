// API Service Layer - Handles all backend communication
// Supports both real API calls and mock data for development

import API from './api';
import {
  MOCK_USERS,
  MOCK_POOLS,
  MOCK_POOL_USER_STATS,
  MOCK_TEAMS,
  MOCK_FIXTURES,
  MOCK_PICKS,
  MOCK_LEADERBOARD,
  MOCK_COMPETITIONS,
  getFixturesByGameweek,
  getUserPickHistory,
  getTeamPickCount,
  getTeamById,
} from './mockData';

// Toggle this to switch between mock and real API
const USE_MOCK_DATA = false;

// Simulate network delay for realistic UX testing
const mockDelay = (ms = 500) => new Promise(resolve => setTimeout(resolve, ms));

// Helper to extract error message from axios error response
// Backend returns errors as { detail: "error message" }
const getErrorMessage = (error) => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  return error.message || 'An unexpected error occurred';
};

// ==================== AUTH ====================

export const login = async (email, password) => {
  if (USE_MOCK_DATA) {
    await mockDelay(800);
    const user = Object.values(MOCK_USERS).find(u => u.email === email);
    if (user && password === 'password123') {
      return { success: true, message: 'Logged in successfully', user: { id: user.id, email: user.email } };
    }
    return { success: false, message: 'Invalid credentials' };
  }

  const formData = new FormData();
  formData.append('email', email);
  formData.append('password', password);
  const res = await API.post('/login', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const signup = async (userData) => {
  if (USE_MOCK_DATA) {
    await mockDelay(800);
    // Simulate successful signup
    const newId = Object.keys(MOCK_USERS).length + 1;
    return { message: 'User created successfully', user_id: newId };
  }

  const formData = new FormData();
  formData.append('userName', userData.userName);
  formData.append('email', userData.email);
  formData.append('password', userData.password);
  formData.append('firstName', userData.firstName);
  formData.append('lastName', userData.lastName);
  const res = await API.post('/signup', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
};

export const logout = async () => {
  if (USE_MOCK_DATA) {
    await mockDelay(300);
    return { message: 'Logged out' };
  }
  const res = await API.post('/logout');
  return res.data;
};

// ==================== USERS ====================

export const getUser = async (userId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    const user = MOCK_USERS[userId];
    if (!user) throw new Error('User not found');
    return user;
  }
  const res = await API.get(`/users/${userId}`);
  return res.data;
};

// ==================== POOLS ====================

export const getAllPools = async () => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    return MOCK_POOLS;
  }
  const res = await API.get('/pools');
  return res.data;
};

export const getPoolById = async (poolId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    const pool = MOCK_POOLS.find(p => p.id === poolId);
    if (!pool) throw new Error('Pool not found');
    const usersStats = MOCK_POOL_USER_STATS.filter(s => s.pool_id === poolId);
    return { ...pool, users_stats: usersStats };
  }
  const res = await API.get(`/pools/${poolId}`);
  return res.data;
};

export const getUserPools = async (userId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    // Mock returns same shape as backend: PoolUserStatsResponse[]
    const userStats = MOCK_POOL_USER_STATS.filter(s => s.user_id === userId);
    return userStats.map(stat => ({
      id: stat.id,
      pool_id: stat.pool_id,
      user_id: stat.user_id,
      lives_left: stat.lives_remaining, // Backend uses lives_left
      eliminated_gameweek: stat.eliminated_gameweek,
      created_at: stat.created_at,
      updated_at: stat.updated_at,
    }));
  }
  // Backend returns: List[PoolUserStatsResponse] with { id, pool_id, user_id, lives_left, eliminated_gameweek, created_at, updated_at }
  const res = await API.get(`/users/${userId}/pools`);
  return res.data;
};

// Helper: Get user pools with full pool details (makes additional calls)
export const getUserPoolsWithDetails = async (userId) => {
  const userPoolStats = await getUserPools(userId);
  
  // Fetch full pool details for each pool the user is in
  const poolsWithDetails = await Promise.all(
    userPoolStats.map(async (stats) => {
      try {
        // First get pool to know competition_id
        const pool = await getPoolById(stats.pool_id);
        
        // Then fetch remaining data in parallel
        const [leaderboard, poolPicks, poolFixtures] = await Promise.all([
          getPoolLeaderboard(stats.pool_id),
          getPoolPicks(stats.pool_id),
          pool?.competition_id ? getFixtures({ league: pool.competition_id }) : Promise.resolve([]),
        ]);
        
        // Calculate current gameweek from fixtures
        const now = new Date();
        const upcomingFixtures = poolFixtures
          .filter(f => new Date(f.kickoff_time) > now)
          .sort((a, b) => new Date(a.kickoff_time) - new Date(b.kickoff_time));
        const currentGameweek = upcomingFixtures[0]?.gameweek || 1;
        
        // Find earliest kickoff for deadline
        const currentGwFixtures = poolFixtures.filter(f => f.gameweek === currentGameweek);
        const earliestKickoff = currentGwFixtures
          .map(f => new Date(f.kickoff_time))
          .sort((a, b) => a - b)[0] || null;
        
        // Calculate user rank from leaderboard
        const userRank = leaderboard.findIndex(e => e.user_id === userId) + 1 || null;
        
        // Check if user has pick for current gameweek
        const userCurrentPick = poolPicks.find(p => {
          const fixture = poolFixtures.find(f => f.id === p.fixture_id);
          return p.user_id === userId && fixture?.gameweek === currentGameweek;
        });
        
        return {
          ...pool,
          user_stats: {
            lives_left: stats.lives_left,
            eliminated_gameweek: stats.eliminated_gameweek,
            rank: userRank,
          },
          currentGameweek,
          earliestKickoff,
          hasCurrentPick: !!userCurrentPick,
        };
      } catch (error) {
        console.error(`Failed to fetch pool ${stats.pool_id}:`, error);
        return null;
      }
    })
  );
  
  return poolsWithDetails.filter(Boolean);
};

export const joinPool = async (poolId, userId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(600);
    const pool = MOCK_POOLS.find(p => p.id === poolId);
    if (!pool) throw new Error('Pool not found');
    return {
      id: MOCK_POOL_USER_STATS.length + 1,
      pool_id: poolId,
      user_id: userId,
      lives_left: pool.total_lives,
      eliminated_gameweek: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  const res = await API.post(`/pools/${poolId}/join`, { user_id: userId });
  return res.data;
};

// Join pool by session code
export const joinPoolByCode = async (sessionCode, userId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(600);
    const pool = MOCK_POOLS.find(p => p.session_code === sessionCode);
    if (!pool) throw new Error('Invalid session code');
    return {
      id: MOCK_POOL_USER_STATS.length + 1,
      pool_id: pool.id,
      user_id: userId,
      lives_left: pool.total_lives,
      eliminated_gameweek: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
  }
  try {
    const res = await API.post('/pools/join_by_code', { user_id: userId, session_code: sessionCode });
    return res.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const createPool = async (poolData) => {
  if (USE_MOCK_DATA) {
    await mockDelay(600);
    const newPool = {
      id: MOCK_POOLS.length + 1,
      ...poolData,
    };
    return newPool;
  }
  // Backend PoolCreate schema expects: { name, description?, competition_id, start_gameweek?, max_picks_per_team?, total_lives?, created_by }
  // Rename creator_id to created_by for backend, remove session_code (backend generates it)
  const { session_code, creator_id, ...rest } = poolData;
  const backendPoolData = {
    ...rest,
    created_by: creator_id, // Backend expects created_by, not creator_id
  };
  try {
    const res = await API.post('/pools/create', backendPoolData);
    return res.data; // Backend returns pool with session_code
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const getPoolLeaderboard = async (poolId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    // Return mock data in backend's shape: LeaderboardEntry
    return MOCK_LEADERBOARD.map(entry => ({
      user_id: entry.user_id,
      username: entry.username,
      lives_left: entry.lives_remaining, // Backend uses lives_left
      total_points: entry.points,        // Backend uses total_points
      eliminated_gameweek: entry.eliminated_gameweek,
      is_eliminated: entry.is_eliminated,
      rank: entry.rank,
    }));
  }
  // Backend returns: List[LeaderboardEntry] with { user_id, username, lives_left, total_points, eliminated_gameweek, is_eliminated, rank }
  const res = await API.get(`/pools/${poolId}/leaderboard`);
  return res.data;
};

// ==================== COMPETITIONS ====================

export const getCompetitions = async () => {
  if (USE_MOCK_DATA) {
    await mockDelay(300);
    return MOCK_COMPETITIONS;
  }
  const res = await API.get('/competitions/leagues');
  return res.data;
};

// ==================== TEAMS ====================

export const getTeams = async (competitionId = null) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    if (competitionId) {
      return MOCK_TEAMS.filter(t => t.competition_id === competitionId);
    }
    return MOCK_TEAMS;
  }
  const params = competitionId ? { league: competitionId } : {};
  const res = await API.get('/competitions/teams', { params });
  return res.data;
};

// ==================== FIXTURES ====================

export const getFixtures = async (filters = {}) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    let fixtures = [...MOCK_FIXTURES];
    if (filters.gameweek) {
      fixtures = getFixturesByGameweek(filters.gameweek);
    }
    if (filters.league) {
      fixtures = fixtures.filter(f => f.competition_id === filters.league);
    }
    return fixtures;
  }
  const res = await API.get('/competitions/fixtures', { params: filters });
  return res.data;
};

export const getFixtureById = async (fixtureId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(300);
    const fixture = MOCK_FIXTURES.find(f => f.id === fixtureId);
    if (!fixture) throw new Error('Fixture not found');
    return fixture;
  }
  const res = await API.get(`/competitions/fixtures/${fixtureId}`);
  return res.data;
};

// ==================== PICKS ====================

export const createPick = async (pickData) => {
  if (USE_MOCK_DATA) {
    await mockDelay(600);
    // Validate pick
    const pool = MOCK_POOLS.find(p => p.id === pickData.pool_id);
    if (!pool) throw new Error('Pool not found');

    const teamPickCount = getTeamPickCount(pickData.user_id, pickData.pool_id, pickData.team_id);
    if (teamPickCount >= pool.max_picks_per_team) {
      throw new Error(`You've already picked this team the maximum of ${pool.max_picks_per_team} times`);
    }

    const newPick = {
      id: MOCK_PICKS.length + 1,
      ...pickData,
      competition_id: pool.competition_id,
      result: null,
      points: null,
      created_at: new Date().toISOString(),
    };
    return newPick;
  }
  try {
    const res = await API.post('/picks/', pickData);
    return res.data;
  } catch (error) {
    throw new Error(getErrorMessage(error));
  }
};

export const getUserPicks = async (userId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    return MOCK_PICKS.filter(p => p.user_id === userId).map(pick => ({
      ...pick,
      team: getTeamById(pick.team_id),
    }));
  }
  const res = await API.get(`/picks/user/${userId}`);
  return res.data;
};

export const getPoolPicks = async (poolId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(400);
    return MOCK_PICKS.filter(p => p.pool_id === poolId);
  }
  const res = await API.get(`/picks/pool/${poolId}`);
  return res.data;
};

export const updatePick = async (pickId, updateData) => {
  if (USE_MOCK_DATA) {
    await mockDelay(500);
    const pick = MOCK_PICKS.find(p => p.id === pickId);
    if (!pick) throw new Error('Pick not found');
    return { ...pick, ...updateData };
  }
  const res = await API.put(`/picks/${pickId}`, updateData);
  return res.data;
};

// ==================== HELPER FUNCTIONS ====================

// Get enriched data for the pool detail screen
export const getHomeScreenData = async (userId, poolId) => {
  if (USE_MOCK_DATA) {
    await mockDelay(600);
    
    const user = MOCK_USERS[userId];
    const userPoolStats = MOCK_POOL_USER_STATS.find(
      s => s.user_id === userId && s.pool_id === poolId
    );
    const pool = MOCK_POOLS.find(p => p.id === poolId);
    // Transform leaderboard to backend shape
    const leaderboard = MOCK_LEADERBOARD.map(entry => ({
      user_id: entry.user_id,
      username: entry.username,
      lives_left: entry.lives_remaining,
      total_points: entry.points,
      eliminated_gameweek: entry.eliminated_gameweek,
      is_eliminated: entry.is_eliminated,
      rank: entry.rank,
    }));
    const currentGameweek = 18;
    const fixtures = getFixturesByGameweek(currentGameweek);
    const userPicks = getUserPickHistory(userId, poolId);
    const teams = MOCK_TEAMS.filter(t => t.competition_id === pool?.competition_id);

    // Add pick count to teams
    const teamsWithPickCount = teams.map(team => ({
      ...team,
      usedCount: getTeamPickCount(userId, poolId, team.id),
      nextMatch: fixtures.find(
        f => f.home_team_id === team.id || f.away_team_id === team.id
      )?.displayName || 'No upcoming match',
    }));

    // Return userStats in backend shape (lives_left not lives_remaining)
    return {
      user: {
        ...user,
        livesLeft: userPoolStats?.lives_remaining || pool?.total_lives || 3,
        isEliminated: userPoolStats?.lives_remaining === 0,
      },
      pool,
      userStats: userPoolStats ? {
        ...userPoolStats,
        lives_left: userPoolStats.lives_remaining, // Map to backend field name
      } : null,
      leaderboard,
      currentGameweek,
      fixtures,
      userPicks,
      teams: teamsWithPickCount,
    };
  }

  // Real API calls - fetch pool first to get competition_id
  const pool = await getPoolById(poolId);
  
  const [user, leaderboard, teamsRaw, fixturesRaw, allPoolPicks] = await Promise.all([
    getUser(userId),
    getPoolLeaderboard(poolId),
    getTeams(pool?.competition_id),
    getFixtures({ league: pool?.competition_id }),
    getPoolPicks(poolId),
  ]);

  // Find user's stats from pool data
  const userStats = pool?.users_stats?.find(s => s.user_id === userId) || null;
  
  // Get user's picks for this pool to calculate used counts
  const userPoolPicks = allPoolPicks.filter(p => p.user_id === userId);
  
  // Enrich all picks with gameweek from their fixture
  const allPicksWithGameweek = allPoolPicks.map(pick => {
    const fixture = fixturesRaw.find(f => f.id === pick.fixture_id);
    return {
      ...pick,
      gameweek: fixture?.gameweek || null,
    };
  });
  
  // Calculate current gameweek from fixtures (first fixture that hasn't started yet)
  const now = new Date();
  const upcomingFixtures = fixturesRaw
    .filter(f => new Date(f.kickoff_time) > now)
    .sort((a, b) => new Date(a.kickoff_time) - new Date(b.kickoff_time));
  const currentGameweek = upcomingFixtures[0]?.gameweek || 1;
  
  // Find earliest kickoff in current gameweek for deadline
  const currentGwFixtures = fixturesRaw.filter(f => f.gameweek === currentGameweek);
  const earliestKickoff = currentGwFixtures
    .map(f => new Date(f.kickoff_time))
    .sort((a, b) => a - b)[0] || null;
  
  // Helper to get team name by ID
  const getTeamName = (teamId) => {
    const team = teamsRaw.find(t => t.id === teamId);
    return team?.short_name || team?.name || 'TBD';
  };
  
  // Enrich teams with next match info and used count
  const teams = teamsRaw.map(team => {
    // Find fixture where this team plays (home or away)
    const nextFixture = fixturesRaw.find(
      f => f.home_team_id === team.id || f.away_team_id === team.id
    );
    
    // Calculate how many times user has picked this team
    const usedCount = userPoolPicks.filter(p => p.team_id === team.id).length;
    
    // Build display name for next match
    let nextMatch = 'No upcoming match';
    if (nextFixture) {
      const homeTeamName = getTeamName(nextFixture.home_team_id);
      const awayTeamName = getTeamName(nextFixture.away_team_id);
      nextMatch = `${homeTeamName} vs ${awayTeamName}`;
    }
    
    return {
      ...team,
      usedCount,
      nextMatch,
    };
  });

  // Check if user has made pick for current gameweek
  const userCurrentGwPick = allPicksWithGameweek.find(
    p => p.user_id === userId && p.gameweek === currentGameweek
  );

  return {
    user,
    pool,
    userStats,
    leaderboard,
    currentGameweek,
    earliestKickoff, // For deadline display
    fixtures: fixturesRaw,
    userPicks: userPoolPicks.map(p => {
      const fixture = fixturesRaw.find(f => f.id === p.fixture_id);
      return { ...p, gameweek: fixture?.gameweek || null };
    }),
    allPoolPicks: allPicksWithGameweek, // All picks for history
    hasCurrentPick: !!userCurrentGwPick, // Whether user has made pick for current GW
    teams,
  };
};

export default {
  login,
  signup,
  logout,
  getUser,
  getAllPools,
  getPoolById,
  getUserPools,
  getUserPoolsWithDetails,
  joinPool,
  joinPoolByCode,
  createPool,
  getPoolLeaderboard,
  getCompetitions,
  getTeams,
  getFixtures,
  getFixtureById,
  createPick,
  getUserPicks,
  getPoolPicks,
  updatePick,
  getHomeScreenData,
};
