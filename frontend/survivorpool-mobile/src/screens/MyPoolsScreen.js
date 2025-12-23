import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/MyPoolsScreen.styles';
import { EmptyState } from '../components/EmptyState';

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
          <EmptyState
            type="noPools"
            actionLabel="Join or Create Pool"
            onAction={() => navigation.navigate('JoinCreate')}
          />
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
