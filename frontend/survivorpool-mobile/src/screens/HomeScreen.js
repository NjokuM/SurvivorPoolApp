import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, Image, StatusBar, RefreshControl, StyleSheet } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';

export default function HomeScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors, isDark, toggleTheme } = useTheme();
  const styles = createStyles(colors);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('picks');
  
  // Data state
  const [user, setUser] = useState(null);
  const [currentPool, setCurrentPool] = useState(null);
  const [userPools, setUserPools] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [teams, setTeams] = useState([]);
  const [fixtures, setFixtures] = useState([]);
  const [userPicks, setUserPicks] = useState([]);
  const [currentGameweek, setCurrentGameweek] = useState(18);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [selectedFixture, setSelectedFixture] = useState(null);

  const loadData = useCallback(async () => {
    try {
      // Get user pools first
      const pools = await apiService.getUserPools(userId);
      setUserPools(pools);
      
      if (pools.length > 0) {
        const poolId = pools[0].pool_id;
        const data = await apiService.getHomeScreenData(userId, poolId);
        setUser(data.user);
        setCurrentPool(data.pool);
        setLeaderboard(data.leaderboard);
        setTeams(data.teams);
        setFixtures(data.fixtures);
        setUserPicks(data.userPicks);
        setCurrentGameweek(data.currentGameweek);
      } else {
        // User has no pools, just load user data
        const userData = await apiService.getUser(userId);
        setUser(userData);
      }
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  const handleLogout = () => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  const handleMakePick = async () => {
    if (!selectedTeam || !selectedFixture) {
      alert('Please select a team and fixture');
      return;
    }

    try {
      await apiService.createPick({
        pool_id: currentPool.id,
        user_id: userId,
        team_id: selectedTeam,
        fixture_id: selectedFixture,
      });
      alert('Pick submitted successfully!');
      setSelectedTeam(null);
      setSelectedFixture(null);
      loadData();
    } catch (error) {
      alert(error.message || 'Failed to submit pick');
    }
  };

  const handleJoinPool = async (poolId) => {
    try {
      await apiService.joinPool(poolId, userId);
      alert('Successfully joined pool!');
      loadData();
    } catch (error) {
      alert(error.message || 'Failed to join pool');
    }
  };

  // Loading state
  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.accent} />
        <Text style={styles.loadingText}>Loading your data...</Text>
      </View>
    );
  }

  const tabs = [
    { id: 'picks', label: 'Make Pick', icon: 'football' },
    { id: 'standings', label: 'Standings', icon: 'trophy' },
    { id: 'history', label: 'History', icon: 'time' },
    { id: 'pools', label: 'Pools', icon: 'people' },
  ];

  const livesLeft = user?.livesLeft || currentPool?.total_lives || 3;

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.surface} />
      
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.headerTitle}>Survivor Pool</Text>
            <Text style={styles.headerSubtitle}>
              {currentPool ? currentPool.name : 'Join a pool to start'}
            </Text>
          </View>
          <View style={styles.headerActions}>
            <TouchableOpacity style={styles.headerButton} onPress={() => {}}>
              <Ionicons name="notifications-outline" size={22} color={colors.textPrimary} />
            </TouchableOpacity>
            <TouchableOpacity style={styles.headerButton} onPress={handleLogout}>
              <Ionicons name="log-out-outline" size={22} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>

        {/* Stats Row */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{currentGameweek}</Text>
            <Text style={styles.statLabel}>Gameweek</Text>
          </View>
          <View style={[styles.statCard, styles.statCardHighlight]}>
            <Text style={[styles.statValue, styles.statValueAccent]}>{livesLeft}</Text>
            <Text style={styles.statLabel}>Lives Left</Text>
            <View style={styles.livesRow}>
              {[...Array(livesLeft)].map((_, i) => (
                <Ionicons key={i} name="heart" size={14} color={colors.heart} />
              ))}
              {[...Array(Math.max(0, (currentPool?.total_lives || 3) - livesLeft))].map((_, i) => (
                <Ionicons key={`empty-${i}`} name="heart-outline" size={14} color={colors.heartEmpty} />
              ))}
            </View>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{userPicks.length}</Text>
            <Text style={styles.statLabel}>Picks Made</Text>
          </View>
        </View>
      </View>

      {/* Content */}
      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.accent}
            colors={[colors.accent]}
          />
        }
      >
        {/* Tab Bar */}
        <View style={styles.tabBar}>
          {tabs.map((tab) => (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tabButton, activeTab === tab.id && styles.tabButtonActive]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Text style={[styles.tabText, activeTab === tab.id && styles.tabTextActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Make Pick Tab */}
        {activeTab === 'picks' && currentPool && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Select Your Team</Text>
              <View style={styles.badge}>
                <Text style={styles.badgeText}>GW {currentGameweek}</Text>
              </View>
            </View>

            {/* Teams Grid */}
            <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginBottom: 24 }}>
              {teams.slice(0, 10).map((team) => {
                const isSelected = selectedTeam === team.id;
                const isUsedMax = team.usedCount >= (currentPool?.max_picks_per_team || 2);
                
                return (
                  <TouchableOpacity
                    key={team.id}
                    style={[
                      styles.card,
                      { width: '47%', padding: 12, marginBottom: 0 },
                      isSelected && { borderColor: colors.accent, borderWidth: 2 },
                      isUsedMax && { opacity: 0.5 },
                    ]}
                    onPress={() => !isUsedMax && setSelectedTeam(team.id)}
                    disabled={isUsedMax}
                  >
                    <Image
                      source={{ uri: team.logo }}
                      style={styles.teamLogo}
                      resizeMode="contain"
                    />
                    <Text style={styles.teamName} numberOfLines={1}>{team.name}</Text>
                    <Text style={[styles.cardSubtitle, { fontSize: 11, marginTop: 4 }]}>
                      {team.nextMatch}
                    </Text>
                    {team.usedCount > 0 && (
                      <View style={[styles.badge, { marginTop: 8, alignSelf: 'center' }]}>
                        <Text style={[styles.badgeText, { fontSize: 10 }]}>
                          Used {team.usedCount}x
                        </Text>
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>

            {/* Confirm Button */}
            {selectedTeam && (
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleMakePick}
              >
                <Text style={styles.primaryButtonText}>Confirm Pick</Text>
              </TouchableOpacity>
            )}
          </>
        )}

        {/* No Pool State */}
        {activeTab === 'picks' && !currentPool && (
          <View style={styles.emptyState}>
            <View style={styles.emptyIcon}>
              <Ionicons name="football-outline" size={40} color="rgba(255,255,255,0.3)" />
            </View>
            <Text style={styles.emptyTitle}>No Active Pool</Text>
            <Text style={styles.emptyText}>Join a pool to start making picks</Text>
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={() => setActiveTab('pools')}
            >
              <Text style={styles.primaryButtonText}>Browse Pools</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Standings Tab */}
        {activeTab === 'standings' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Leaderboard</Text>
            </View>

            <View style={styles.card}>
              {leaderboard.map((entry, index) => {
                const isCurrentUser = entry.user_id === userId;
                return (
                  <View
                    key={entry.user_id}
                    style={[
                      styles.leaderboardItem,
                      isCurrentUser && styles.currentUserRow,
                      index === leaderboard.length - 1 && { borderBottomWidth: 0 },
                    ]}
                  >
                    <View style={[
                      styles.leaderboardRank,
                      index < 3 && styles.leaderboardRankTop,
                    ]}>
                      <Text style={styles.leaderboardRankText}>{entry.rank}</Text>
                    </View>
                    <View style={styles.leaderboardInfo}>
                      <Text style={styles.leaderboardName}>
                        {entry.username} {isCurrentUser && '(You)'}
                      </Text>
                      <Text style={styles.leaderboardPoints}>
                        {entry.total_points} points
                      </Text>
                    </View>
                    <View style={styles.leaderboardLives}>
                      <Ionicons name="heart" size={16} color="#e90052" />
                      <Text style={styles.leaderboardLivesText}>{entry.lives_left}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          </>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Your Pick History</Text>
            </View>

            {userPicks.length === 0 ? (
              <View style={styles.emptyState}>
                <View style={styles.emptyIcon}>
                  <Ionicons name="time-outline" size={40} color="rgba(255,255,255,0.3)" />
                </View>
                <Text style={styles.emptyTitle}>No Picks Yet</Text>
                <Text style={styles.emptyText}>Your pick history will appear here</Text>
              </View>
            ) : (
              userPicks.map((pick) => (
                <View key={pick.id} style={styles.card}>
                  <View style={styles.cardHeader}>
                    <View>
                      <Text style={styles.cardTitle}>{pick.team?.name || 'Team'}</Text>
                      <Text style={styles.cardSubtitle}>
                        {pick.fixture?.displayName || 'Fixture'}
                      </Text>
                    </View>
                    <View style={[
                      styles.badge,
                      pick.result === 'WIN' && { backgroundColor: 'rgba(16, 185, 129, 0.15)' },
                      pick.result === 'LOSS' && { backgroundColor: 'rgba(239, 68, 68, 0.15)' },
                    ]}>
                      <Text style={[
                        styles.badgeText,
                        pick.result === 'WIN' && { color: '#10b981' },
                        pick.result === 'LOSS' && { color: '#ef4444' },
                      ]}>
                        {pick.result || 'Pending'}
                      </Text>
                    </View>
                  </View>
                </View>
              ))
            )}
          </>
        )}

        {/* Pools Tab */}
        {activeTab === 'pools' && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Your Pools</Text>
            </View>

            {userPools.length === 0 ? (
              <View style={styles.emptyState}>
                <View style={styles.emptyIcon}>
                  <Ionicons name="people-outline" size={40} color="rgba(255,255,255,0.3)" />
                </View>
                <Text style={styles.emptyTitle}>No Pools Joined</Text>
                <Text style={styles.emptyText}>Join a pool to compete with others</Text>
              </View>
            ) : (
              userPools.map((poolStat) => (
                <TouchableOpacity
                  key={poolStat.id}
                  style={[
                    styles.poolCard,
                    currentPool?.id === poolStat.pool_id && styles.poolCardActive,
                  ]}
                  onPress={() => {
                    // Switch to this pool
                    apiService.getHomeScreenData(userId, poolStat.pool_id).then((data) => {
                      setCurrentPool(data.pool);
                      setLeaderboard(data.leaderboard);
                      setTeams(data.teams);
                      setFixtures(data.fixtures);
                      setUserPicks(data.userPicks);
                      setActiveTab('picks');
                    });
                  }}
                >
                  <Text style={styles.poolName}>{poolStat.pool?.name}</Text>
                  <View style={styles.poolInfo}>
                    <Ionicons name="calendar-outline" size={14} color="rgba(255,255,255,0.5)" />
                    <Text style={styles.poolInfoText}>Gameweek {currentGameweek}</Text>
                  </View>
                  <View style={styles.poolStats}>
                    <View style={styles.poolStat}>
                      <Ionicons name="heart" size={14} color="#e90052" />
                      <Text style={styles.poolStatText}>{poolStat.lives_left} lives</Text>
                    </View>
                  </View>
                </TouchableOpacity>
              ))
            )}

            <View style={styles.divider} />

            {/* Available Pools */}
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Join a Pool</Text>
            </View>

            <AvailablePoolsList userId={userId} onJoin={handleJoinPool} />
          </>
        )}

        {/* Bottom spacing */}
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// Available Pools Component
function AvailablePoolsList({ userId, onJoin }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);
  const [pools, setPools] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiService.getAllPools().then((data) => {
      setPools(data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return <ActivityIndicator color={colors.accent} />;
  }

  return (
    <>
      {pools.map((pool) => (
        <View key={pool.id} style={styles.poolCard}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
            <View style={{ flex: 1 }}>
              <Text style={styles.poolName}>{pool.name}</Text>
              <Text style={[styles.poolInfoText, { marginTop: 4 }]}>{pool.description}</Text>
            </View>
            <TouchableOpacity
              style={styles.primaryButton}
              onPress={() => onJoin(pool.id)}
            >
              <Text style={styles.primaryButtonText}>Join</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.poolStats}>
            <View style={styles.poolStat}>
              <Ionicons name="heart" size={14} color={colors.heart} />
              <Text style={styles.poolStatText}>{pool.total_lives} lives</Text>
            </View>
            <View style={styles.poolStat}>
              <Ionicons name="repeat" size={14} color={colors.textMuted} />
              <Text style={styles.poolStatText}>Max {pool.max_picks_per_team}x per team</Text>
            </View>
          </View>
        </View>
      ))}
    </>
  );
}

// Dynamic styles based on theme
const createStyles = (colors) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.background,
  },
  loadingText: {
    color: colors.textMuted,
    marginTop: 16,
    fontSize: 16,
  },
  header: {
    backgroundColor: colors.surface,
    paddingTop: 50,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 8,
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.textPrimary,
    letterSpacing: 0.5,
  },
  headerSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
    marginTop: 2,
  },
  headerActions: {
    flexDirection: 'row',
    gap: 12,
  },
  headerButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: colors.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 12,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.inputBackground,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  statCardHighlight: {
    backgroundColor: colors.accent + '15',
    borderColor: colors.accent + '40',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  statValueAccent: {
    color: colors.accent,
  },
  statLabel: {
    fontSize: 11,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  livesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    marginTop: 8,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 4,
    marginBottom: 20,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tabButtonActive: {
    backgroundColor: colors.accent,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
  },
  tabTextActive: {
    color: colors.textOnAccent,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    backgroundColor: colors.accent + '20',
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.accent,
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  cardSubtitle: {
    fontSize: 13,
    color: colors.textMuted,
  },
  poolCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  poolCardActive: {
    borderColor: colors.accent,
    borderWidth: 2,
  },
  poolName: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  poolInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 6,
  },
  poolInfoText: {
    fontSize: 13,
    color: colors.textMuted,
  },
  poolStats: {
    flexDirection: 'row',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: colors.border,
    gap: 16,
  },
  poolStat: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  poolStatText: {
    fontSize: 13,
    color: colors.textSecondary,
    fontWeight: '500',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.inputBackground,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 20,
  },
  primaryButton: {
    backgroundColor: colors.accent,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  primaryButtonText: {
    color: colors.textOnAccent,
    fontSize: 15,
    fontWeight: '700',
  },
  divider: {
    height: 1,
    backgroundColor: colors.border,
    marginVertical: 24,
  },
  teamLogo: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.inputBackground,
    marginBottom: 8,
  },
  teamName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    textAlign: 'center',
  },
  leaderboardItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  leaderboardRank: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.inputBackground,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  leaderboardRankTop: {
    backgroundColor: colors.accent + '30',
  },
  leaderboardRankText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.textPrimary,
  },
  leaderboardInfo: {
    flex: 1,
  },
  leaderboardName: {
    fontSize: 15,
    fontWeight: '600',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  leaderboardPoints: {
    fontSize: 12,
    color: colors.textMuted,
  },
  leaderboardLives: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  leaderboardLivesText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.heart,
  },
  currentUserRow: {
    backgroundColor: colors.accent + '15',
    borderRadius: 8,
    marginHorizontal: -8,
    paddingHorizontal: 8,
  },
});