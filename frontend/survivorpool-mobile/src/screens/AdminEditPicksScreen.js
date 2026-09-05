import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, Image } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
// Reuses PoolDetailScreen's styles (team grid / gameweek selector) rather
// than duplicating them - this screen is visually the same "pick a team
// for a gameweek" interaction, just acting on someone else's picks with
// admin authorization instead of the caller's own.
import { createStyles } from './styles/PoolDetailScreen.styles';

export default function AdminEditPicksScreen({ route, navigation }) {
  const { poolId, targetUserId, targetUsername } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [pool, setPool] = useState(null);
  const [teams, setTeams] = useState([]);
  const [fixtures, setFixtures] = useState([]);
  const [targetPicks, setTargetPicks] = useState([]);
  const [gameweek, setGameweek] = useState(null);
  const [selectedTeam, setSelectedTeam] = useState(null);

  const loadData = useCallback(async () => {
    try {
      // getHomeScreenData is written generically around "userId" - passing
      // the target member's id (not the admin's own) gives back exactly
      // their picks/stats for this pool, which is all we need here.
      const data = await apiService.getHomeScreenData(targetUserId, poolId);
      setPool(data.pool);
      setTeams(data.teams);
      setFixtures(data.fixtures);
      setTargetPicks(data.userPicks);

      setGameweek((current) => {
        if (current) return current;
        const pickedGws = new Set(data.userPicks.map((p) => p.gameweek));
        const allGws = [...new Set(data.fixtures.map((f) => f.gameweek))].sort((a, b) => a - b);
        const firstMissing = allGws.find((gw) => !pickedGws.has(gw));
        return firstMissing ?? data.currentGameweek ?? allGws[0] ?? 1;
      });
    } catch (error) {
      console.error('Error loading admin pick editor data:', error);
      Toast.show({ type: 'error', text1: 'Failed to load', text2: error.message });
    } finally {
      setLoading(false);
    }
  }, [targetUserId, poolId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const gameweekNumbers = [...new Set(fixtures.map((f) => f.gameweek))].sort((a, b) => a - b);
  const minGw = gameweekNumbers[0] || 1;
  const maxGw = gameweekNumbers[gameweekNumbers.length - 1] || 1;
  const existingPickForGw = targetPicks.find((p) => p.gameweek === gameweek);

  const handleSubmit = async () => {
    if (!selectedTeam || !gameweek) return;
    const fixture = fixtures.find(
      (f) => f.gameweek === gameweek && (f.home_team_id === selectedTeam || f.away_team_id === selectedTeam)
    );
    if (!fixture) return;

    setSubmitting(true);
    try {
      const result = await apiService.adminSetUserPicks(poolId, targetUserId, [
        { fixture_id: fixture.id, team_id: selectedTeam },
      ]);
      const livesNote = pool?.has_lives ? `, ${result.lives_left} lives left` : '';
      Toast.show({
        type: 'success',
        text1: 'Pick updated',
        text2: `${targetUsername}'s stats recomputed - ${result.total_points} pts${livesNote}`,
      });
      setSelectedTeam(null);
      await loadData();
    } catch (error) {
      Toast.show({ type: 'error', text1: 'Failed to update pick', text2: error.message });
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.accent} />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />

      <View style={{ flexDirection: 'row', alignItems: 'center', paddingHorizontal: 16, paddingTop: 56, paddingBottom: 12 }}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={{ marginRight: 12 }}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <View>
          <Text style={{ fontSize: 18, fontWeight: '700', color: colors.textPrimary }}>
            Edit {targetUsername}'s Picks
          </Text>
          <Text style={{ fontSize: 13, color: colors.textMuted }}>{pool?.name}</Text>
        </View>
      </View>

      <ScrollView>
        <View style={styles.pickHeader}>
          <Text style={styles.pickTitle}>Set a pick for {targetUsername}</Text>
          <Text style={styles.pickSubtitle}>
            Admin override - deadlines and the per-team limit don't apply here. All of{' '}
            {targetUsername}'s stats are fully recomputed after saving, not just this gameweek.
          </Text>
        </View>

        <View style={styles.weekSelectorContainer}>
          <View style={styles.weekSelector}>
            <TouchableOpacity
              style={styles.weekButton}
              onPress={() => setGameweek(Math.max(minGw, gameweek - 1))}
              disabled={gameweek <= minGw}
            >
              <Ionicons name="chevron-back" size={20} color={gameweek <= minGw ? colors.textMuted : colors.textPrimary} />
            </TouchableOpacity>
            <View style={{ alignItems: 'center' }}>
              <Text style={styles.weekText}>Gameweek {gameweek}</Text>
              {existingPickForGw && (
                <Text style={{ color: colors.info, fontSize: 11 }}>Currently picked</Text>
              )}
            </View>
            <TouchableOpacity
              style={styles.weekButton}
              onPress={() => setGameweek(Math.min(maxGw, gameweek + 1))}
              disabled={gameweek >= maxGw}
            >
              <Ionicons name="chevron-forward" size={20} color={gameweek >= maxGw ? colors.textMuted : colors.textPrimary} />
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.teamsGrid}>
          {teams.map((team) => {
            const fixture = fixtures.find(
              (f) => f.gameweek === gameweek && (f.home_team_id === team.id || f.away_team_id === team.id)
            );
            if (!fixture) return null;

            const isSelected = selectedTeam === team.id;
            const isCurrentPick = existingPickForGw?.team_id === team.id;
            const opponentId = fixture.home_team_id === team.id ? fixture.away_team_id : fixture.home_team_id;
            const opponent = teams.find((t) => t.id === opponentId);

            return (
              <TouchableOpacity
                key={team.id}
                style={[styles.teamCard, isSelected && styles.teamCardSelected, isCurrentPick && styles.teamCardUserPick]}
                onPress={() => setSelectedTeam(isSelected ? null : team.id)}
                activeOpacity={0.7}
              >
                {isCurrentPick && (
                  <View style={styles.userPickBadge}>
                    <Text style={styles.userPickBadgeText}>CURRENT</Text>
                  </View>
                )}
                <Image source={{ uri: team.logo }} style={styles.teamLogo} resizeMode="contain" />
                <Text style={styles.teamName} numberOfLines={1}>{team.name}</Text>
                <Text style={styles.teamFixture} numberOfLines={1}>
                  vs {opponent?.short_name || opponent?.name || 'TBD'}
                </Text>
                {isSelected && (
                  <View style={styles.selectedIndicator}>
                    <Ionicons name="checkmark-circle" size={16} color={colors.accent} />
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </View>

        {selectedTeam && (
          <View style={styles.confirmContainer}>
            <TouchableOpacity style={styles.confirmButton} onPress={handleSubmit} disabled={submitting}>
              <Text style={styles.confirmButtonText}>
                {submitting ? 'Saving...' : `Save Pick: ${teams.find((t) => t.id === selectedTeam)?.name}`}
              </Text>
            </TouchableOpacity>
          </View>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}
