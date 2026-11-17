import { View, Text, TouchableOpacity, ScrollView, StatusBar } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
// Reuses PoolDetailScreen's styles (header / history rows / result chips) -
// this screen is the drill-down from that screen's Standings tab.
import { createStyles } from './styles/PoolDetailScreen.styles';
import { formatGoalDifference } from '../utils/format';

// Everything is passed in from the standings row the user tapped, so this
// screen shows the same snapshot as the table it came from.
export default function PlayerPicksScreen({ route, navigation }) {
  const { username, isCurrentUser, totalPoints, goalDifference, livesLeft, gameweeks, picks } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const count = (result) => picks.filter(p => p.result === result).length;

  // "2–1 vs Chelsea (H)" once played, "vs Chelsea (H)" before kick-off
  const renderMatch = (pick) => {
    if (!pick.opponentName) return null;
    const venue = pick.isHome ? 'H' : 'A';
    const score = pick.teamGoals !== null ? `${pick.teamGoals}–${pick.opponentGoals} ` : '';
    return `${score}vs ${pick.opponentName} (${venue})`;
  };

  const renderResult = (result) => (
    <View style={[
      styles.historyResult,
      result === 'WIN' && styles.historyResultWin,
      result === 'DRAW' && styles.historyResultDraw,
      result === 'LOSS' && styles.historyResultLoss,
    ]}>
      <Text style={styles.historyResultText}>
        {result === 'WIN' ? '✓' : result === 'DRAW' ? 'D' : result === 'LOSS' ? '✗' : '-'}
      </Text>
    </View>
  );

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.surface} />

      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>
            {username}{isCurrentUser ? ' (You)' : ''}
          </Text>
        </View>
      </View>

      <ScrollView style={styles.content}>
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
            <Text style={styles.statsValue}>
              {livesLeft === null ? formatGoalDifference(goalDifference) : livesLeft}
            </Text>
            <Text style={styles.statsLabel}>{livesLeft === null ? 'GD' : 'Lives'}</Text>
          </View>
        </View>

        {gameweeks.map((gw) => {
          const weekPicks = picks.filter(p => p.gameweek === gw);
          return (
            <View key={gw} style={styles.historyWeekRow}>
              <View style={styles.historyWeekBadge}>
                <Text style={styles.historyWeekBadgeText}>GW{gw}</Text>
              </View>
              {weekPicks.length === 0 ? (
                <Text style={styles.historyNoPick}>No pick</Text>
              ) : (
                <View style={{ flex: 1, gap: 4 }}>
                  {weekPicks.map((pick) => (
                    <View key={pick.id} style={{ flexDirection: 'row', alignItems: 'center' }}>
                      <View style={{ flex: 1, marginRight: 8 }}>
                        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                          {weekPicks.length > 1 && (
                            <Ionicons name="flash" size={13} color={colors.warning} style={{ marginRight: 4 }} />
                          )}
                          <Text style={[styles.historyWeekTeam, { flex: 0, flexShrink: 1 }]} numberOfLines={1}>
                            {pick.teamName}
                          </Text>
                        </View>
                        {renderMatch(pick) && (
                          <Text style={[styles.teamPickMatch, { marginTop: 2 }]} numberOfLines={1}>
                            {renderMatch(pick)}
                          </Text>
                        )}
                      </View>
                      {renderResult(pick.result)}
                      <Text style={[styles.teamPickPoints, { marginLeft: 8, width: 40 }]}>
                        {pick.result ? `+${pick.points || 0}` : '–'}
                      </Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          );
        })}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}
