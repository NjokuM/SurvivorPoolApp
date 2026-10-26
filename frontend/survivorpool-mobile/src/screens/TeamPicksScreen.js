import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl, Image } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
// Reuses PoolDetailScreen's styles (header / standings rows / result chips) -
// this screen is the drill-down from that screen's Teams tab.
import { createStyles } from './styles/PoolDetailScreen.styles';
import { formatGoalDifference } from '../utils/format';

export default function TeamPicksScreen({ route, navigation }) {
  const { poolId, userId, teamId, teamName, teamLogo } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [picks, setPicks] = useState([]);
  const [expandedUserIds, setExpandedUserIds] = useState(new Set());

  const toggleExpanded = (id) => {
    setExpandedUserIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const loadData = useCallback(async () => {
    try {
      const data = await apiService.getTeamPicks(poolId, teamId);
      setPicks(data.picks || []);
      setError(null);
    } catch (err) {
      console.error('Error loading team picks:', err);
      setError(err.message || 'Failed to load picks');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [poolId, teamId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  const scored = picks.filter(p => p.result);
  const totalPoints = scored.reduce((sum, p) => sum + p.points, 0);
  const goalDifference = scored.reduce((sum, p) => sum + ((p.team_goals ?? 0) - (p.opponent_goals ?? 0)), 0);
  const count = (result) => scored.filter(p => p.result === result).length;

  // One entry per player who picked this team, most points first. Picks
  // arrive newest-first from the API, so each player's list stays that way.
  const players = Object.values(
    picks.reduce((acc, pick) => {
      const entry = acc[pick.user_id] || (acc[pick.user_id] = {
        userId: pick.user_id,
        username: pick.username,
        picks: [],
        points: 0,
      });
      entry.picks.push(pick);
      if (pick.result) entry.points += pick.points;
      return acc;
    }, {})
  ).sort((a, b) =>
    b.points - a.points ||
    b.picks.length - a.picks.length ||
    a.username.localeCompare(b.username)
  );

  const renderScore = (pick) => {
    const venue = pick.is_home ? 'H' : 'A';
    const opponent = pick.opponent_name || 'Unknown';
    if (pick.team_goals === null || pick.team_goals === undefined) {
      return `vs ${opponent} (${venue})`;
    }
    return `${pick.team_goals}–${pick.opponent_goals} vs ${opponent} (${venue})`;
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={[styles.headerCenter, styles.teamRowInfo]}>
          {teamLogo ? (
            <Image source={{ uri: teamLogo }} style={styles.teamRowLogo} resizeMode="contain" />
          ) : null}
          <Text style={[styles.headerTitle, { flexShrink: 1 }]} numberOfLines={1}>{teamName}</Text>
        </View>
      </View>

      {loading ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.accent} />
        </View>
      ) : (
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
          {/* Summary */}
          <View style={styles.teamSummaryRow}>
            <View style={{ alignItems: 'center' }}>
              <Text style={styles.statsValue}>{totalPoints}</Text>
              <Text style={styles.statsLabel}>Points</Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <Text style={styles.statsValue}>{picks.length}</Text>
              <Text style={styles.statsLabel}>Picks</Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <Text style={styles.statsValue}>{count('WIN')}-{count('DRAW')}-{count('LOSS')}</Text>
              <Text style={styles.statsLabel}>W-D-L</Text>
            </View>
            <View style={{ alignItems: 'center' }}>
              <Text style={styles.statsValue}>{formatGoalDifference(goalDifference)}</Text>
              <Text style={styles.statsLabel}>GD</Text>
            </View>
          </View>

          {error && <Text style={styles.historySubtitle}>{error}</Text>}
          {!error && picks.length === 0 && (
            <Text style={styles.historySubtitle}>Nobody in this pool has picked {teamName} yet</Text>
          )}

          {players.map((player) => {
            const isCurrentUser = player.userId === userId;
            const isExpanded = expandedUserIds.has(player.userId);
            const pickCount = player.picks.length;
            return (
              <View key={player.userId}>
                <TouchableOpacity
                  style={[styles.teamPickRow, isCurrentUser && styles.standingsRowHighlight]}
                  onPress={() => toggleExpanded(player.userId)}
                  activeOpacity={0.7}
                >
                  <View style={styles.historyAvatar}>
                    <Text style={styles.historyAvatarText}>{player.username[0].toUpperCase()}</Text>
                  </View>
                  <View style={styles.teamPickInfo}>
                    <Text style={[styles.standingsName, isCurrentUser && styles.standingsNameHighlight]} numberOfLines={1}>
                      {player.username} {isCurrentUser && '(You)'}
                    </Text>
                    <Text style={styles.teamPickMatch}>
                      {pickCount} {pickCount === 1 ? 'pick' : 'picks'}
                    </Text>
                  </View>
                  <Text style={styles.teamPickPoints}>{player.points} pts</Text>
                  <Ionicons
                    name={isExpanded ? 'chevron-up' : 'chevron-down'}
                    size={18}
                    color={colors.textMuted}
                    style={{ marginLeft: 8 }}
                  />
                </TouchableOpacity>

                {isExpanded && player.picks.map((pick) => (
                  <View key={pick.pick_id} style={[styles.teamPickRow, styles.teamPickSubRow]}>
                    <View style={styles.historyWeekBadge}>
                      <Text style={styles.historyWeekBadgeText}>GW{pick.gameweek}</Text>
                    </View>
                    <Text style={[styles.teamPickMatch, styles.teamPickInfo, { marginTop: 0 }]} numberOfLines={1}>
                      {renderScore(pick)}
                    </Text>
                    <View style={[
                      styles.historyResult,
                      pick.result === 'WIN' && styles.historyResultWin,
                      pick.result === 'DRAW' && styles.historyResultDraw,
                      pick.result === 'LOSS' && styles.historyResultLoss,
                    ]}>
                      <Text style={styles.historyResultText}>
                        {pick.result === 'WIN' ? '✓' : pick.result === 'DRAW' ? 'D' : pick.result === 'LOSS' ? '✗' : '-'}
                      </Text>
                    </View>
                    <Text style={styles.teamPickPoints}>
                      {pick.result ? `+${pick.points}` : '–'}
                    </Text>
                  </View>
                ))}
              </View>
            );
          })}
        </ScrollView>
      )}
    </View>
  );
}
