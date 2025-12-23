import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl, StyleSheet } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';

export default function MyPoolsScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [user, setUser] = useState(null);
  const [pools, setPools] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const [userData, userPools] = await Promise.all([
        apiService.getUser(userId),
        apiService.getUserPoolsWithDetails(userId), // Use helper that fetches pool details
      ]);
      setUser(userData);
      setPools(userPools);
    } catch (error) {
      console.error('Error loading pools:', error);
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

  const getDeadlineInfo = (pool) => {
    // Mock deadline - in real app, get from fixtures
    const now = new Date();
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 2); // 2 days from now
    deadline.setHours(15, 0, 0, 0); // 3 PM kickoff
    
    const diff = deadline - now;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
      return { text: `${days}d ${hours % 24}h left`, urgent: days < 1 };
    } else if (hours > 0) {
      return { text: `${hours}h left`, urgent: hours < 6 };
    } else {
      return { text: 'Deadline passed', urgent: true };
    }
  };

  const getPickStatus = (pool) => {
    // TODO: In real app, check if user has made pick for current gameweek
    // For now, return pending to show the UI
    return 'pending';
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.accent} />
        <Text style={styles.loadingText}>Loading your pools...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>Welcome back,</Text>
          <Text style={styles.username}>{user?.username || 'Player'}</Text>
        </View>
        <View style={styles.headerRight}>
          <View style={styles.avatarContainer}>
            <Text style={styles.avatarText}>
              {(user?.username || 'U')[0].toUpperCase()}
            </Text>
          </View>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        contentContainerStyle={styles.contentContainer}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={colors.accent}
            colors={[colors.accent]}
          />
        }
      >
        {/* Quick Stats */}
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{pools.length}</Text>
            <Text style={styles.statLabel}>Active Pools</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              {pools.filter(p => getPickStatus(p) === 'pending').length}
            </Text>
            <Text style={styles.statLabel}>Picks Needed</Text>
          </View>
        </View>

        {/* Section Title */}
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>My Pools</Text>
          <Text style={styles.sectionSubtitle}>Tap a pool to manage picks</Text>
        </View>

        {/* Pools List */}
        {pools.length === 0 ? (
          <View style={styles.emptyState}>
            <View style={styles.emptyIcon}>
              <Ionicons name="people-outline" size={48} color={colors.textMuted} />
            </View>
            <Text style={styles.emptyTitle}>No Pools Yet</Text>
            <Text style={styles.emptyText}>
              Join a pool with a session code or create your own to get started!
            </Text>
            <TouchableOpacity 
              style={styles.primaryButton}
              onPress={() => navigation.navigate('JoinCreate')}
            >
              <Text style={styles.primaryButtonText}>Join or Create Pool</Text>
            </TouchableOpacity>
          </View>
        ) : (
          pools.map((pool) => {
            const deadline = getDeadlineInfo(pool);
            const pickStatus = getPickStatus(pool);
            const livesLeft = pool.user_stats?.lives_left || pool.total_lives || 3;
            
            return (
              <TouchableOpacity
                key={pool.pool_id || pool.id}
                style={styles.poolCard}
                onPress={() => navigation.navigate('PoolDetail', { 
                  poolId: pool.pool_id || pool.id, 
                  userId,
                  poolName: pool.name 
                })}
                activeOpacity={0.7}
              >
                {/* Pool Header */}
                <View style={styles.poolHeader}>
                  <View style={styles.poolTitleRow}>
                    <Text style={styles.poolName}>{pool.name}</Text>
                    {pickStatus === 'pending' && (
                      <View style={[styles.statusBadge, styles.statusPending]}>
                        <Ionicons name="alert-circle" size={12} color={colors.warning} />
                        <Text style={[styles.statusText, { color: colors.warning }]}>
                          Pick Needed
                        </Text>
                      </View>
                    )}
                    {pickStatus === 'picked' && (
                      <View style={[styles.statusBadge, styles.statusPicked]}>
                        <Ionicons name="checkmark-circle" size={12} color={colors.success} />
                        <Text style={[styles.statusText, { color: colors.success }]}>
                          Picked
                        </Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.poolDescription}>{pool.description}</Text>
                </View>

                {/* Pool Stats */}
                <View style={styles.poolStatsRow}>
                  <View style={styles.poolStat}>
                    <View style={styles.livesContainer}>
                      {[...Array(livesLeft)].map((_, i) => (
                        <Ionicons key={i} name="heart" size={16} color={colors.heart} />
                      ))}
                      {[...Array(Math.max(0, (pool.total_lives || 3) - livesLeft))].map((_, i) => (
                        <Ionicons key={`e-${i}`} name="heart-outline" size={16} color={colors.heartEmpty} />
                      ))}
                    </View>
                    <Text style={styles.poolStatLabel}>{livesLeft} Lives</Text>
                  </View>
                  
                  <View style={styles.poolStatDivider} />
                  
                  <View style={styles.poolStat}>
                    <Text style={styles.poolStatValue}>#{pool.user_stats?.rank || '-'}</Text>
                    <Text style={styles.poolStatLabel}>Rank</Text>
                  </View>
                  
                  <View style={styles.poolStatDivider} />
                  
                  <View style={styles.poolStat}>
                    <Text style={[
                      styles.poolStatValue, 
                      deadline.urgent && { color: colors.warning }
                    ]}>
                      {deadline.text}
                    </Text>
                    <Text style={styles.poolStatLabel}>Deadline</Text>
                  </View>
                </View>

                {/* Arrow indicator */}
                <View style={styles.poolArrow}>
                  <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                </View>
              </TouchableOpacity>
            );
          })
        )}

        {/* Bottom spacing */}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}

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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    backgroundColor: colors.background,
  },
  greeting: {
    fontSize: 14,
    color: colors.textMuted,
    marginBottom: 4,
  },
  username: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.textPrimary,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  avatarContainer: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textOnAccent,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 24,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  statValue: {
    fontSize: 32,
    fontWeight: '800',
    color: colors.accent,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  sectionHeader: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
  },
  poolCard: {
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: colors.border,
    position: 'relative',
  },
  poolHeader: {
    marginBottom: 16,
  },
  poolTitleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  poolName: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.textPrimary,
    flex: 1,
  },
  poolDescription: {
    fontSize: 13,
    color: colors.textMuted,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  statusPending: {
    backgroundColor: colors.warning + '20',
  },
  statusPicked: {
    backgroundColor: colors.success + '20',
  },
  statusText: {
    fontSize: 11,
    fontWeight: '600',
  },
  poolStatsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.inputBackground,
    borderRadius: 12,
    padding: 12,
  },
  poolStat: {
    flex: 1,
    alignItems: 'center',
  },
  poolStatDivider: {
    width: 1,
    height: 30,
    backgroundColor: colors.border,
  },
  livesContainer: {
    flexDirection: 'row',
    gap: 2,
    marginBottom: 4,
  },
  poolStatValue: {
    fontSize: 16,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 2,
  },
  poolStatLabel: {
    fontSize: 11,
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
  poolArrow: {
    position: 'absolute',
    right: 16,
    top: '50%',
    marginTop: -10,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyIcon: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: colors.border,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 24,
    paddingHorizontal: 20,
  },
  primaryButton: {
    backgroundColor: colors.accent,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
  },
  primaryButtonText: {
    color: colors.textOnAccent,
    fontSize: 15,
    fontWeight: '700',
  },
});
