// Mock data for development - simulates backend responses
// This allows frontend development without a running backend

export const MOCK_USERS = {
  1: {
    id: 1,
    userName: 'john_doe',
    email: 'user1@example.com',
    firstName: 'John',
    lastName: 'Doe',
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
  2: {
    id: 2,
    userName: 'jane_smith',
    email: 'jane@example.com',
    firstName: 'Jane',
    lastName: 'Smith',
    created_at: '2024-01-16T10:00:00Z',
    updated_at: '2024-01-16T10:00:00Z',
  },
  3: {
    id: 3,
    userName: 'mike_wilson',
    email: 'mike@example.com',
    firstName: 'Mike',
    lastName: 'Wilson',
    created_at: '2024-01-17T10:00:00Z',
    updated_at: '2024-01-17T10:00:00Z',
  },
};

export const MOCK_COMPETITIONS = [
  {
    id: 1,
    external_id: 39,
    name: 'Premier League',
    country: 'England',
    logo: 'https://media.api-sports.io/football/leagues/39.png',
    season: 2024,
  },
  {
    id: 2,
    external_id: 140,
    name: 'La Liga',
    country: 'Spain',
    logo: 'https://media.api-sports.io/football/leagues/140.png',
    season: 2024,
  },
];

export const MOCK_TEAMS = [
  { id: 1, name: 'Arsenal', short_name: 'ARS', logo: 'https://media.api-sports.io/football/teams/42.png', competition_id: 1 },
  { id: 2, name: 'Aston Villa', short_name: 'AVL', logo: 'https://media.api-sports.io/football/teams/66.png', competition_id: 1 },
  { id: 3, name: 'Bournemouth', short_name: 'BOU', logo: 'https://media.api-sports.io/football/teams/35.png', competition_id: 1 },
  { id: 4, name: 'Brentford', short_name: 'BRE', logo: 'https://media.api-sports.io/football/teams/55.png', competition_id: 1 },
  { id: 5, name: 'Brighton', short_name: 'BHA', logo: 'https://media.api-sports.io/football/teams/51.png', competition_id: 1 },
  { id: 6, name: 'Chelsea', short_name: 'CHE', logo: 'https://media.api-sports.io/football/teams/49.png', competition_id: 1 },
  { id: 7, name: 'Crystal Palace', short_name: 'CRY', logo: 'https://media.api-sports.io/football/teams/52.png', competition_id: 1 },
  { id: 8, name: 'Everton', short_name: 'EVE', logo: 'https://media.api-sports.io/football/teams/45.png', competition_id: 1 },
  { id: 9, name: 'Fulham', short_name: 'FUL', logo: 'https://media.api-sports.io/football/teams/36.png', competition_id: 1 },
  { id: 10, name: 'Ipswich Town', short_name: 'IPS', logo: 'https://media.api-sports.io/football/teams/57.png', competition_id: 1 },
  { id: 11, name: 'Leicester City', short_name: 'LEI', logo: 'https://media.api-sports.io/football/teams/46.png', competition_id: 1 },
  { id: 12, name: 'Liverpool', short_name: 'LIV', logo: 'https://media.api-sports.io/football/teams/40.png', competition_id: 1 },
  { id: 13, name: 'Manchester City', short_name: 'MCI', logo: 'https://media.api-sports.io/football/teams/50.png', competition_id: 1 },
  { id: 14, name: 'Manchester United', short_name: 'MUN', logo: 'https://media.api-sports.io/football/teams/33.png', competition_id: 1 },
  { id: 15, name: 'Newcastle United', short_name: 'NEW', logo: 'https://media.api-sports.io/football/teams/34.png', competition_id: 1 },
  { id: 16, name: 'Nottingham Forest', short_name: 'NFO', logo: 'https://media.api-sports.io/football/teams/65.png', competition_id: 1 },
  { id: 17, name: 'Southampton', short_name: 'SOU', logo: 'https://media.api-sports.io/football/teams/41.png', competition_id: 1 },
  { id: 18, name: 'Tottenham', short_name: 'TOT', logo: 'https://media.api-sports.io/football/teams/47.png', competition_id: 1 },
  { id: 19, name: 'West Ham', short_name: 'WHU', logo: 'https://media.api-sports.io/football/teams/48.png', competition_id: 1 },
  { id: 20, name: 'Wolves', short_name: 'WOL', logo: 'https://media.api-sports.io/football/teams/39.png', competition_id: 1 },
];

export const MOCK_FIXTURES = [
  { id: 1, home_team_id: 1, away_team_id: 6, competition_id: 1, gameweek: 18, kickoff_time: '2024-12-26T15:00:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 2, home_team_id: 12, away_team_id: 11, competition_id: 1, gameweek: 18, kickoff_time: '2024-12-26T15:00:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 3, home_team_id: 13, away_team_id: 8, competition_id: 1, gameweek: 18, kickoff_time: '2024-12-26T15:00:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 4, home_team_id: 15, away_team_id: 2, competition_id: 1, gameweek: 18, kickoff_time: '2024-12-26T17:30:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 5, home_team_id: 18, away_team_id: 16, competition_id: 1, gameweek: 18, kickoff_time: '2024-12-26T20:00:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 6, home_team_id: 14, away_team_id: 15, competition_id: 1, gameweek: 19, kickoff_time: '2024-12-30T20:00:00Z', home_score: null, away_score: null, status: 'NS' },
  { id: 7, home_team_id: 6, away_team_id: 9, competition_id: 1, gameweek: 19, kickoff_time: '2024-12-30T15:00:00Z', home_score: null, away_score: null, status: 'NS' },
  // Past fixtures with results
  { id: 100, home_team_id: 12, away_team_id: 14, competition_id: 1, gameweek: 17, kickoff_time: '2024-12-22T16:30:00Z', home_score: 2, away_score: 2, status: 'FT' },
  { id: 101, home_team_id: 1, away_team_id: 7, competition_id: 1, gameweek: 17, kickoff_time: '2024-12-21T15:00:00Z', home_score: 5, away_score: 1, status: 'FT' },
  { id: 102, home_team_id: 13, away_team_id: 2, competition_id: 1, gameweek: 17, kickoff_time: '2024-12-21T17:30:00Z', home_score: 2, away_score: 1, status: 'FT' },
];

export const MOCK_POOLS = [
  {
    id: 1,
    name: 'Premier League Survivors 2024',
    description: 'Weekly survivor challenge for the 2024/25 season',
    competition_id: 1,
    start_gameweek: 1,
    max_picks_per_team: 2,
    total_lives: 3,
    session_code: 'PLS24X',
    creator_id: 2,
  },
  {
    id: 2,
    name: 'Office Pool Champions',
    description: 'Company survivor pool',
    competition_id: 1,
    start_gameweek: 10,
    max_picks_per_team: 1,
    total_lives: 2,
    session_code: 'OFC2K4',
    creator_id: 1,
  },
  {
    id: 3,
    name: 'Friends League',
    description: 'Casual survivor pool with friends',
    competition_id: 1,
    start_gameweek: 15,
    max_picks_per_team: 2,
    total_lives: 3,
    session_code: 'FRD123',
    creator_id: 3,
  },
];

export const MOCK_POOL_USER_STATS = [
  { id: 1, pool_id: 1, user_id: 1, lives_remaining: 3, picks_made: 17, correct_picks: 12, rank: 1, eliminated_gameweek: null, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-12-20T10:00:00Z' },
  { id: 2, pool_id: 1, user_id: 2, lives_remaining: 2, picks_made: 17, correct_picks: 10, rank: 2, eliminated_gameweek: null, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-12-20T10:00:00Z' },
  { id: 3, pool_id: 1, user_id: 3, lives_remaining: 0, picks_made: 15, correct_picks: 8, rank: 5, eliminated_gameweek: 15, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-12-15T10:00:00Z' },
  { id: 4, pool_id: 2, user_id: 1, lives_remaining: 2, picks_made: 8, correct_picks: 6, rank: 2, eliminated_gameweek: null, created_at: '2024-10-01T10:00:00Z', updated_at: '2024-12-20T10:00:00Z' },
  { id: 5, pool_id: 1, user_id: 4, lives_remaining: 2, picks_made: 17, correct_picks: 9, rank: 3, eliminated_gameweek: null, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-12-20T10:00:00Z' },
  { id: 6, pool_id: 1, user_id: 5, lives_remaining: 1, picks_made: 17, correct_picks: 7, rank: 4, eliminated_gameweek: null, created_at: '2024-08-01T10:00:00Z', updated_at: '2024-12-20T10:00:00Z' },
];

export const MOCK_PICKS = [
  { id: 1, pool_id: 1, user_id: 1, team_id: 12, fixture_id: 100, competition_id: 1, result: 'DRAW', points: 0, created_at: '2024-12-20T10:00:00Z' },
  { id: 2, pool_id: 1, user_id: 1, team_id: 1, fixture_id: 101, competition_id: 1, result: 'WIN', points: 1, created_at: '2024-12-19T10:00:00Z' },
  { id: 3, pool_id: 1, user_id: 2, team_id: 13, fixture_id: 102, competition_id: 1, result: 'WIN', points: 1, created_at: '2024-12-19T10:00:00Z' },
];

export const MOCK_LEADERBOARD = [
  { user_id: 1, username: 'john_doe', lives_remaining: 3, correct_picks: 12, points: 36, eliminated_gameweek: null, is_eliminated: false, rank: 1 },
  { user_id: 2, username: 'jane_smith', lives_remaining: 2, correct_picks: 10, points: 30, eliminated_gameweek: null, is_eliminated: false, rank: 2 },
  { user_id: 4, username: 'sarah_jones', lives_remaining: 2, correct_picks: 9, points: 27, eliminated_gameweek: null, is_eliminated: false, rank: 3 },
  { user_id: 5, username: 'tom_brown', lives_remaining: 1, correct_picks: 7, points: 21, eliminated_gameweek: null, is_eliminated: false, rank: 4 },
  { user_id: 3, username: 'mike_wilson', lives_remaining: 0, correct_picks: 8, points: 24, eliminated_gameweek: 15, is_eliminated: true, rank: 5 },
];

// Helper to get team by ID
export const getTeamById = (teamId) => MOCK_TEAMS.find(t => t.id === teamId);

// Helper to get fixture with team names
export const getFixtureWithTeams = (fixture) => {
  const homeTeam = getTeamById(fixture.home_team_id);
  const awayTeam = getTeamById(fixture.away_team_id);
  return {
    ...fixture,
    homeTeam,
    awayTeam,
    displayName: `${homeTeam?.short_name || 'TBD'} vs ${awayTeam?.short_name || 'TBD'}`,
  };
};

// Get fixtures for a specific gameweek
export const getFixturesByGameweek = (gameweek) => {
  return MOCK_FIXTURES
    .filter(f => f.gameweek === gameweek)
    .map(getFixtureWithTeams);
};

// Get user's pick history with team/fixture details
export const getUserPickHistory = (userId, poolId) => {
  return MOCK_PICKS
    .filter(p => p.user_id === userId && p.pool_id === poolId)
    .map(pick => {
      const fixture = MOCK_FIXTURES.find(f => f.id === pick.fixture_id);
      const team = getTeamById(pick.team_id);
      return {
        ...pick,
        team,
        fixture: fixture ? getFixtureWithTeams(fixture) : null,
      };
    });
};

// Get teams user has already picked in a pool
export const getUserPickedTeamIds = (userId, poolId) => {
  return MOCK_PICKS
    .filter(p => p.user_id === userId && p.pool_id === poolId)
    .map(p => p.team_id);
};

// Count how many times user picked a specific team
export const getTeamPickCount = (userId, poolId, teamId) => {
  return MOCK_PICKS.filter(
    p => p.user_id === userId && p.pool_id === poolId && p.team_id === teamId
  ).length;
};
