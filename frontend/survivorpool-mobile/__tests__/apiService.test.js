// Mock the API module before importing apiService
jest.mock('../src/api/api', () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
  },
}));

import API from '../src/api/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  login,
  signup,
  logout,
  getUser,
  getAllPools,
  getPoolById,
  getUserPools,
  joinPool,
  joinPoolByCode,
  createPool,
  leavePool,
  deletePool,
  getPoolLeaderboard,
  getCompetitions,
  getTeams,
  getFixtures,
  getFixtureById,
  createPick,
  getUserPicks,
  getPoolPicks,
  updatePick,
} from '../src/api/apiService';

beforeEach(() => {
  jest.clearAllMocks();
  AsyncStorage.clear();
});

// ==================== AUTH ====================
describe('Auth API', () => {
  describe('login', () => {
    it('sends form data and stores tokens on success', async () => {
      API.post.mockResolvedValueOnce({
        data: {
          success: true,
          access_token: 'at_123',
          refresh_token: 'rt_456',
          user: { id: 1, email: 'test@test.com' },
        },
      });

      const result = await login('test@test.com', 'password');

      expect(API.post).toHaveBeenCalledWith('/login', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      expect(result.success).toBe(true);
      expect(result.access_token).toBe('at_123');
      // Tokens should be stored
      expect(AsyncStorage.multiSet).toHaveBeenCalled();
    });

    it('does not store tokens on failed login', async () => {
      API.post.mockResolvedValueOnce({
        data: { success: false, message: 'Invalid credentials' },
      });

      const result = await login('bad@test.com', 'wrong');

      expect(result.success).toBe(false);
      expect(AsyncStorage.multiSet).not.toHaveBeenCalled();
    });

    it('propagates network errors', async () => {
      API.post.mockRejectedValueOnce(new Error('Network Error'));
      await expect(login('test@test.com', 'pass')).rejects.toThrow('Network Error');
    });
  });

  describe('signup', () => {
    it('sends user data as form data', async () => {
      API.post.mockResolvedValueOnce({
        data: { message: 'User created', user_id: 5 },
      });

      const result = await signup({
        userName: 'testuser',
        email: 'test@test.com',
        password: 'pass123',
        firstName: 'Test',
        lastName: 'User',
      });

      expect(API.post).toHaveBeenCalledWith('/signup', expect.any(FormData), {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      expect(result.user_id).toBe(5);
    });
  });

  describe('logout', () => {
    it('calls /logout and clears auth', async () => {
      API.post.mockResolvedValueOnce({ data: { message: 'Logged out' } });

      await logout();

      expect(API.post).toHaveBeenCalledWith('/logout');
      expect(AsyncStorage.multiRemove).toHaveBeenCalled();
    });

    it('clears auth even if /logout request fails', async () => {
      API.post.mockRejectedValueOnce(new Error('Server error'));

      // Error propagates (no catch, only finally), but clearAuth still runs
      await expect(logout()).rejects.toThrow('Server error');
      expect(AsyncStorage.multiRemove).toHaveBeenCalled();
    });
  });
});

// ==================== USERS ====================
describe('Users API', () => {
  it('getUser fetches user by ID', async () => {
    API.get.mockResolvedValueOnce({ data: { id: 1, email: 'test@test.com' } });

    const user = await getUser(1);

    expect(API.get).toHaveBeenCalledWith('/users/1');
    expect(user.id).toBe(1);
  });
});

// ==================== POOLS ====================
describe('Pools API', () => {
  it('getAllPools fetches all pools', async () => {
    API.get.mockResolvedValueOnce({ data: [{ id: 1, name: 'Pool A' }] });

    const pools = await getAllPools();

    expect(API.get).toHaveBeenCalledWith('/pools');
    expect(pools).toHaveLength(1);
  });

  it('getPoolById fetches a specific pool', async () => {
    API.get.mockResolvedValueOnce({
      data: { id: 1, name: 'Pool A', users_stats: [] },
    });

    const pool = await getPoolById(1);

    expect(API.get).toHaveBeenCalledWith('/pools/1');
    expect(pool.name).toBe('Pool A');
  });

  it('getUserPools fetches pools for a user', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ pool_id: 1, user_id: 5, lives_left: 3 }],
    });

    const pools = await getUserPools(5);

    expect(API.get).toHaveBeenCalledWith('/users/5/pools');
    expect(pools[0].lives_left).toBe(3);
  });

  it('joinPool sends POST with user_id', async () => {
    API.post.mockResolvedValueOnce({
      data: { pool_id: 1, user_id: 5, lives_left: 3 },
    });

    const result = await joinPool(1, 5);

    expect(API.post).toHaveBeenCalledWith('/pools/1/join', { user_id: 5 });
    expect(result.lives_left).toBe(3);
  });

  it('joinPoolByCode sends session code', async () => {
    API.post.mockResolvedValueOnce({
      data: { pool_id: 1, user_id: 5 },
    });

    const result = await joinPoolByCode('ABC123', 5);

    expect(API.post).toHaveBeenCalledWith('/pools/join_by_code', {
      user_id: 5,
      session_code: 'ABC123',
    });
  });

  it('joinPoolByCode throws readable error on failure', async () => {
    API.post.mockRejectedValueOnce({
      response: { data: { detail: 'Invalid session code' } },
    });

    await expect(joinPoolByCode('BAD', 5)).rejects.toThrow('Invalid session code');
  });

  it('createPool maps creator_id to created_by', async () => {
    API.post.mockResolvedValueOnce({
      data: { id: 1, name: 'New Pool', session_code: 'XYZ' },
    });

    const result = await createPool({
      name: 'New Pool',
      competition_id: 1,
      creator_id: 5,
      total_lives: 3,
    });

    // Should send created_by, not creator_id
    expect(API.post).toHaveBeenCalledWith('/pools/create', {
      name: 'New Pool',
      competition_id: 1,
      created_by: 5,
      total_lives: 3,
    });
    expect(result.session_code).toBe('XYZ');
  });

  it('leavePool sends DELETE with user_id param', async () => {
    API.delete.mockResolvedValueOnce({ data: { message: 'Left pool' } });

    await leavePool(1, 5);

    expect(API.delete).toHaveBeenCalledWith('/pools/1/leave', { params: { user_id: 5 } });
  });

  it('deletePool sends DELETE with user_id param', async () => {
    API.delete.mockResolvedValueOnce({ data: { message: 'Deleted' } });

    await deletePool(1, 5);

    expect(API.delete).toHaveBeenCalledWith('/pools/1', { params: { user_id: 5 } });
  });

  it('getPoolLeaderboard returns leaderboard data', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ user_id: 1, lives_left: 3, total_points: 10, rank: 1 }],
    });

    const lb = await getPoolLeaderboard(1);

    expect(API.get).toHaveBeenCalledWith('/pools/1/leaderboard');
    expect(lb[0].rank).toBe(1);
  });
});

// ==================== COMPETITIONS ====================
describe('Competitions API', () => {
  it('getCompetitions fetches leagues', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ id: 1, name: 'Premier League' }],
    });

    const comps = await getCompetitions();

    expect(API.get).toHaveBeenCalledWith('/competitions/leagues');
    expect(comps[0].name).toBe('Premier League');
  });
});

// ==================== TEAMS ====================
describe('Teams API', () => {
  it('getTeams fetches all teams', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ id: 1, name: 'Arsenal' }],
    });

    const teams = await getTeams();

    expect(API.get).toHaveBeenCalledWith('/competitions/teams', { params: {} });
    expect(teams[0].name).toBe('Arsenal');
  });

  it('getTeams filters by competition', async () => {
    API.get.mockResolvedValueOnce({ data: [] });

    await getTeams(1);

    expect(API.get).toHaveBeenCalledWith('/competitions/teams', { params: { league: 1 } });
  });
});

// ==================== FIXTURES ====================
describe('Fixtures API', () => {
  it('getFixtures sends filters as query params', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ id: 1, gameweek: 27, status: 'NS' }],
    });

    const fixtures = await getFixtures({ league: 1, gameweek: 27 });

    expect(API.get).toHaveBeenCalledWith('/competitions/fixtures', {
      params: { league: 1, gameweek: 27 },
    });
    expect(fixtures[0].gameweek).toBe(27);
  });

  it('getFixtures works with no filters', async () => {
    API.get.mockResolvedValueOnce({ data: [] });

    await getFixtures();

    expect(API.get).toHaveBeenCalledWith('/competitions/fixtures', { params: {} });
  });

  it('getFixtures can filter by status', async () => {
    API.get.mockResolvedValueOnce({ data: [] });

    await getFixtures({ league: 1, status: 'FT' });

    expect(API.get).toHaveBeenCalledWith('/competitions/fixtures', {
      params: { league: 1, status: 'FT' },
    });
  });

  it('getFixtureById fetches single fixture', async () => {
    API.get.mockResolvedValueOnce({
      data: { id: 42, home_team_id: 1, away_team_id: 2 },
    });

    const fixture = await getFixtureById(42);

    expect(API.get).toHaveBeenCalledWith('/competitions/fixtures/42');
    expect(fixture.id).toBe(42);
  });
});

// ==================== PICKS ====================
describe('Picks API', () => {
  it('createPick sends pick data', async () => {
    API.post.mockResolvedValueOnce({
      data: { id: 1, pool_id: 1, user_id: 5, team_id: 3, fixture_id: 10 },
    });

    const pick = await createPick({
      pool_id: 1,
      user_id: 5,
      team_id: 3,
      fixture_id: 10,
    });

    expect(API.post).toHaveBeenCalledWith('/picks/', {
      pool_id: 1,
      user_id: 5,
      team_id: 3,
      fixture_id: 10,
    });
    expect(pick.team_id).toBe(3);
  });

  it('createPick throws readable error on failure', async () => {
    API.post.mockRejectedValueOnce({
      response: { data: { detail: "You've already made a pick for gameweek 27." } },
    });

    await expect(
      createPick({ pool_id: 1, user_id: 5, team_id: 3, fixture_id: 10 })
    ).rejects.toThrow("You've already made a pick for gameweek 27.");
  });

  it('getUserPicks fetches picks for a user', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ id: 1, team_id: 3, result: 'WIN' }],
    });

    const picks = await getUserPicks(5);

    expect(API.get).toHaveBeenCalledWith('/picks/user/5');
    expect(picks[0].result).toBe('WIN');
  });

  it('getPoolPicks fetches picks for a pool', async () => {
    API.get.mockResolvedValueOnce({
      data: [{ id: 1, user_id: 5, team_id: 3 }],
    });

    const picks = await getPoolPicks(1);

    expect(API.get).toHaveBeenCalledWith('/picks/pool/1');
    expect(picks).toHaveLength(1);
  });

  it('updatePick sends PUT with update data', async () => {
    API.put.mockResolvedValueOnce({
      data: { id: 1, team_id: 7 },
    });

    const updated = await updatePick(1, { team_id: 7 });

    expect(API.put).toHaveBeenCalledWith('/picks/1', { team_id: 7 });
    expect(updated.team_id).toBe(7);
  });
});
