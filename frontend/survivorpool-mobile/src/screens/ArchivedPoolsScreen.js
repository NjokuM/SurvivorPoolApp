import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
// Reuses MyPoolsScreen's pool-card styles for a consistent look, rather
// than duplicating the card/stats layout.
import { createStyles } from './styles/MyPoolsScreen.styles';
import { EmptyState } from '../components/EmptyState';

export default function ArchivedPoolsScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const [loading, setLoading] = useState(true);
  const [pools, setPools] = useState([]);

  const loadData = useCallback(async () => {
    try {
      const userPools = await apiService.getUserPoolsWithDetails(userId);
      setPools(userPools.filter(pool => pool.is_active === false));
    } catch (error) {
      console.error('Error loading archived pools:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.accent} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />

      <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20 }}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginRight: 12 }}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.username}>Archived Pools</Text>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {pools.length === 0 ? (
          <EmptyState
            icon="archive-outline"
            title="No Archived Pools"
            subtitle="Pools move here once their season ends, or once a survivor pool has a winner."
          />
        ) : (
          pools.map((pool) => {
            const livesLeft = pool.user_stats?.lives_left ?? 0;
            // Rank (from the backend leaderboard: lives_left desc, then
            // total_points as tiebreak) is the actual determinant of who
            // won - surviving isn't enough on its own once more than one
            // player is still alive when the season ends.
            const rank = pool.user_stats?.rank;
            const resultLabel = rank === 1 ? 'Winner' : livesLeft > 0 ? 'Runner-up' : 'Eliminated';

            return (
              <TouchableOpacity
                key={pool.pool_id || pool.id}
                style={styles.poolCard}
                onPress={() => navigation.navigate('PoolDetail', {
                  poolId: pool.pool_id || pool.id,
                  userId,
                  poolName: pool.name,
                })}
                activeOpacity={0.7}
              >
                <View style={styles.poolHeader}>
                  <View style={styles.poolTitleRow}>
                    <Text style={styles.poolName}>{pool.name}</Text>
                    <View style={[styles.statusBadge, { backgroundColor: colors.textMuted + '20' }]}>
                      <Ionicons name="archive" size={12} color={colors.textMuted} />
                      <Text style={[styles.statusText, { color: colors.textMuted }]}>Ended</Text>
                    </View>
                  </View>
                  <Text style={styles.poolDescription}>{pool.description}</Text>
                </View>

                <View style={styles.poolStatsRow}>
                  <View style={styles.poolStat}>
                    {pool.has_lives === false ? (
                      <>
                        <Text style={styles.poolStatValue}>{pool.user_stats?.total_points ?? 0}</Text>
                        <Text style={styles.poolStatLabel}>Points</Text>
                      </>
                    ) : (
                      <>
                        <Text style={styles.poolStatValue}>{resultLabel}</Text>
                        <Text style={styles.poolStatLabel}>Result</Text>
                      </>
                    )}
                  </View>

                  <View style={styles.poolStatDivider} />

                  <View style={styles.poolStat}>
                    <Text style={styles.poolStatValue}>#{pool.user_stats?.rank || '-'}</Text>
                    <Text style={styles.poolStatLabel}>Final Rank</Text>
                  </View>
                </View>

                <View style={styles.poolArrow}>
                  <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                </View>
              </TouchableOpacity>
            );
          })
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}
