import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl, Image, Alert } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import * as Clipboard from 'expo-clipboard';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/PoolDetailScreen.styles';
import { formatGoalDifference } from '../utils/format';

export default function PoolDetailScreen({ route, navigation }) {
  const { poolId, userId, poolName } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary', 'pick', 'standings', 'teams', 'history', 'info'
  
  // Data state
  const [pool, setPool] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [teamLeaderboard, setTeamLeaderboard] = useState([]);
  const [teams, setTeams] = useState([]);
  const [fixtures, setFixtures] = useState([]);
  const [userPicks, setUserPicks] = useState([]);
  const [allPoolPicks, setAllPoolPicks] = useState([]);
  const [currentGameweek, setCurrentGameweek] = useState(1);
  const [earliestKickoff, setEarliestKickoff] = useState(null);
  const [hasCurrentPick, setHasCurrentPick] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [historyWeek, setHistoryWeek] = useState(null);
  const [historyFilter, setHistoryFilter] = useState('week'); // 'week' or 'user'
  const [selectedHistoryUser, setSelectedHistoryUser] = useState(null);
  const [pickGameweek, setPickGameweek] = useState(null); // Gameweek for making picks
  const [doubleWeeks, setDoubleWeeks] = useState({ allowance: 0, used: 0, remaining: 0, active_gameweeks: [] });
  // In a double week with both picks made, which of the two a new selection replaces
  const [editPickId, setEditPickId] = useState(null);
  const [adminDoubleWeeks, setAdminDoubleWeeks] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const [data, teamBoard] = await Promise.all([
        apiService.getHomeScreenData(userId, poolId),
        // The Teams tab is secondary - don't let it block the rest of the screen.
        apiService.getTeamLeaderboard(poolId).catch((error) => {
          console.error('Error loading team leaderboard:', error);
          return [];
        }),
      ]);
      setTeamLeaderboard(teamBoard);
      setPool(data.pool);
      setUserStats(data.userStats);
      setLeaderboard(data.leaderboard);
      setTeams(data.teams);
      setFixtures(data.fixtures);
      setUserPicks(data.userPicks);
      setAllPoolPicks(data.allPoolPicks || []);
      setCurrentGameweek(data.currentGameweek);
      setEarliestKickoff(data.earliestKickoff);
      setHasCurrentPick(data.hasCurrentPick || false);
      if (data.doubleWeeks) setDoubleWeeks(data.doubleWeeks);
      setAdminDoubleWeeks(data.pool?.double_weeks ?? 0);
      setHistoryWeek(data.currentGameweek);
      if (!pickGameweek) setPickGameweek(data.currentGameweek); // Default to current gameweek
    } catch (error) {
      console.error('Error loading pool data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [userId, poolId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, [loadData]);

  const isPoolCreator = pool?.created_by === userId;

  const handleLeavePool = () => {
    Alert.alert(
      'Leave Pool',
      'Are you sure you want to leave this pool? Your picks and stats will be deleted.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Leave',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.leavePool(poolId, userId);
              Toast.show({
                type: 'success',
                text1: 'Left Pool',
                text2: 'You have successfully left the pool',
              });
              navigation.goBack();
            } catch (error) {
              Toast.show({
                type: 'error',
                text1: 'Error',
                text2: error.message || 'Failed to leave pool',
              });
            }
          },
        },
      ]
    );
  };

  const handleDeletePool = () => {
    Alert.alert(
      'Delete Pool',
      'Are you sure you want to delete this pool? This action cannot be undone and will remove all members, picks, and stats.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await apiService.deletePool(poolId, userId);
              Toast.show({
                type: 'success',
                text1: 'Pool Deleted',
                text2: 'The pool has been permanently deleted',
              });
              navigation.goBack();
            } catch (error) {
              Toast.show({
                type: 'error',
                text1: 'Error',
                text2: error.message || 'Failed to delete pool',
              });
            }
          },
        },
      ]
    );
  };

  const handleMakePick = async () => {
    if (!selectedTeam) {
      Toast.show({
        type: 'error',
        text1: 'No Team Selected',
        text2: 'Please select a team to pick',
      });
      return;
    }

    try {
      // Find fixture for the selected team in the selected gameweek
      const fixture = fixtures.find(f => 
        (f.home_team_id === selectedTeam || f.away_team_id === selectedTeam) &&
        f.gameweek === pickGameweek
      );
      
      if (!fixture) {
        Toast.show({
          type: 'error',
          text1: 'No Fixture',
          text2: `No match found for this team in GW${pickGameweek}`,
        });
        return;
      }
      
      // Edit an existing pick, or add one (a second pick in a double week)
      const existingPick = getEditTarget(pickGameweek);
      const isSecondPick = !existingPick && weekPicksFor(pickGameweek).length > 0;

      if (existingPick) {
        // Update existing pick
        await apiService.updatePick(existingPick.id, {
          team_id: selectedTeam,
          fixture_id: fixture.id,
        });
        
        Toast.show({
          type: 'success',
          text1: 'Pick Updated!',
          text2: `Your pick for Gameweek ${pickGameweek} has been changed`,
        });
      } else {
        // Create new pick
        await apiService.createPick({
          pool_id: poolId,
          user_id: userId,
          team_id: selectedTeam,
          fixture_id: fixture.id,
        });
        
        Toast.show({
          type: 'success',
          text1: isSecondPick ? 'Second Pick Submitted!' : 'Pick Submitted!',
          text2: isSecondPick
            ? `Your double week for Gameweek ${pickGameweek} is set`
            : `Your pick for Gameweek ${pickGameweek} is locked in`,
        });
      }
      
      setSelectedTeam(null);
      loadData();
    } catch (error) {
      Toast.show({
        type: 'error',
        text1: 'Pick Failed',
        text2: error.message || 'Failed to submit pick',
      });
    }
  };

  const getUsedTeamIds = () => {
    return userPicks.map(p => p.team_id);
  };

  // ---- Double weeks (points-only pools) ----
  const isPointsPool = pool?.has_lives === false;
  const weekPicksFor = (gw) => userPicks.filter(p => p.gameweek === gw).sort((a, b) => a.id - b.id);
  const isDoubleWeekOn = (gw) => (doubleWeeks.active_gameweeks || []).includes(gw);
  const fixtureStarted = (fixtureId) => {
    const f = fixtures.find(x => x.id === fixtureId);
    return !!f && new Date(f.kickoff_time) <= new Date();
  };
  const gameweekOpen = (gw) => fixtures.some(f => f.gameweek === gw && new Date(f.kickoff_time) > new Date());

  // Which existing pick a new selection replaces, or null to add a new pick.
  const getEditTarget = (gw) => {
    const weekPicks = weekPicksFor(gw);
    const maxPicks = isDoubleWeekOn(gw) ? 2 : 1;
    if (weekPicks.length < maxPicks) return null;
    return (
      weekPicks.find(p => p.id === editPickId) ||
      [...weekPicks].reverse().find(p => !fixtureStarted(p.fixture_id)) ||
      weekPicks[weekPicks.length - 1]
    );
  };

  const teamShortName = (teamId) => {
    const team = teams.find(t => t.id === teamId);
    return team?.short_name || team?.name || 'TBD';
  };

  const handleActivateDoubleWeek = () => {
    Alert.alert(
      '⚡ Play a Double Week?',
      `Pick a second team in Gameweek ${pickGameweek}, from a different match. Both results count towards your points.\n\nYou have ${doubleWeeks.remaining} left. You can turn it off again until your second pick kicks off.`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Play Double Week',
          onPress: async () => {
            try {
              setDoubleWeeks(await apiService.activateDoubleWeek(poolId, pickGameweek));
              setEditPickId(null);
              setSelectedTeam(null);
              Toast.show({ type: 'success', text1: 'Double Week on', text2: `Pick a second team for Gameweek ${pickGameweek}` });
            } catch (error) {
              Toast.show({ type: 'error', text1: 'Could not start double week', text2: error.message });
            }
          },
        },
      ]
    );
  };

  const handleDeactivateDoubleWeek = () => {
    const hasSecondPick = weekPicksFor(pickGameweek).length > 1;
    Alert.alert(
      'Turn off Double Week?',
      hasSecondPick
        ? `Your second pick for Gameweek ${pickGameweek} will be removed and you'll get the double week back.`
        : "You'll get the double week back.",
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Turn Off',
          style: 'destructive',
          onPress: async () => {
            try {
              setDoubleWeeks(await apiService.deactivateDoubleWeek(poolId, pickGameweek));
              setEditPickId(null);
              setSelectedTeam(null);
              loadData();
            } catch (error) {
              Toast.show({ type: 'error', text1: 'Could not turn off double week', text2: error.message });
            }
          },
        },
      ]
    );
  };

  const renderHistoryPicks = (picks, teamStyle, align = 'flex-end') => {
    const realPicks = picks.filter(p => p.team_id);
    if (realPicks.length === 0) {
      return <Text style={styles.historyNoPick}>No pick</Text>;
    }
    return (
      <View style={{ flex: 1, alignItems: align, gap: 4 }}>
        {realPicks.map((pick) => (
          <View key={pick.id} style={{ flexDirection: 'row', alignItems: 'center' }}>
            {realPicks.length > 1 && <Ionicons name="flash" size={13} color={colors.warning} style={{ marginRight: 4 }} />}
            <Text style={[teamStyle, { flex: 0, flexShrink: 1, marginRight: 8 }]} numberOfLines={1}>{teams.find(t => t.id === pick.team_id)?.name || 'TBD'}</Text>
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
          </View>
        ))}
      </View>
    );
  };

  const handleSaveDoubleWeekAllowance = async () => {
    try {
      await apiService.setDoubleWeekAllowance(poolId, adminDoubleWeeks);
      Toast.show({
        type: 'success',
        text1: 'Double weeks updated',
        text2: adminDoubleWeeks > 0 ? `${adminDoubleWeeks} per player` : 'Double weeks switched off',
      });
      loadData();
    } catch (error) {
      Toast.show({ type: 'error', text1: 'Could not update double weeks', text2: error.message });
    }
  };

  const getDeadlineCountdown = () => {
    if (!earliestKickoff) {
      return 'No deadline';
    }
    
    const now = new Date();
    const deadline = new Date(earliestKickoff);
    const diff = deadline - now;
    
    if (diff <= 0) {
      return 'Games Started';
    }
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours >= 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
  };

  const livesLeft = userStats?.lives_left || pool?.total_lives || 3;
  const usedTeamIds = getUsedTeamIds();
  
  // Calculate user's rank from leaderboard
  const userRank = leaderboard.findIndex(e => e.user_id === userId) + 1 || '-';

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
        <ActivityIndicator size="large" color={colors.accent} />
        <Text style={styles.loadingText}>Loading pool...</Text>
      </View>
    );
  }

  const tabs = [
    { id: 'summary', label: 'Summary', icon: 'home' },
    { id: 'pick', label: 'Make Pick', icon: 'football' },
    { id: 'standings', label: 'Standings', icon: 'trophy' },
    { id: 'teams', label: 'Teams', icon: 'shield' },
    { id: 'history', label: 'History', icon: 'time' },
    { id: 'info', label: 'Info', icon: 'information-circle' },
  ];

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.surface} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity 
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <Text style={styles.headerTitle} numberOfLines={1}>{poolName || pool?.name}</Text>
          <Text style={styles.headerSubtitle}>Gameweek {currentGameweek}</Text>
        </View>
        <View style={styles.headerRight}>
          <View style={styles.livesIndicator}>
            {pool?.has_lives === false ? (
              <>
                <Ionicons name="trophy" size={16} color={colors.accent} />
                <Text style={styles.livesText}>{userStats?.total_points || 0}</Text>
              </>
            ) : (
              <>
                <Ionicons name="heart" size={16} color={colors.heart} />
                <Text style={styles.livesText}>{livesLeft}</Text>
              </>
            )}
          </View>
        </View>
      </View>

      {/* Tab Bar */}
      <View style={styles.tabBar}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabBarContent}>
          {tabs.map((tab) => (
            <TouchableOpacity
              key={tab.id}
              style={[styles.tabButton, activeTab === tab.id && styles.tabButtonActive]}
              onPress={() => setActiveTab(tab.id)}
            >
              <Ionicons 
                name={tab.icon} 
                size={18} 
                color={activeTab === tab.id ? colors.textOnAccent : colors.textMuted} 
              />
              <Text style={[styles.tabText, activeTab === tab.id && styles.tabTextActive]}>
                {tab.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

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
        {/* SUMMARY TAB */}
        {activeTab === 'summary' && (
          <>
            {/* Deadline Alert - only show if user hasn't made a pick */}
            {!hasCurrentPick && (() => {
              const gamesStarted = earliestKickoff && new Date(earliestKickoff) <= new Date();
              
              return gamesStarted ? (
                <View style={[styles.deadlineCard, styles.deadlineCardUrgent]}>
                  <View style={[styles.deadlineIcon, styles.deadlineIconUrgent]}>
                    <Ionicons name="warning" size={24} color={colors.error} />
                  </View>
                  <View style={styles.deadlineContent}>
                    <Text style={[styles.deadlineLabel, styles.deadlineLabelUrgent]}>Games Started</Text>
                    <Text style={[styles.deadlineTime, styles.deadlineTimeUrgent]}>
                      Some teams may be unavailable
                    </Text>
                  </View>
                  <TouchableOpacity 
                    style={[styles.deadlineButton, styles.deadlineButtonUrgent]}
                    onPress={() => setActiveTab('pick')}
                  >
                    <Text style={styles.deadlineButtonText}>Pick Now</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <View style={styles.deadlineCard}>
                  <View style={styles.deadlineIcon}>
                    <Ionicons name="alarm" size={24} color={colors.warning} />
                  </View>
                  <View style={styles.deadlineContent}>
                    <Text style={styles.deadlineLabel}>Pick Deadline</Text>
                    <Text style={styles.deadlineTime}>{getDeadlineCountdown()}</Text>
                  </View>
                  <TouchableOpacity 
                    style={styles.deadlineButton}
                    onPress={() => setActiveTab('pick')}
                  >
                    <Text style={styles.deadlineButtonText}>Make Pick</Text>
                  </TouchableOpacity>
                </View>
              );
            })()}

            {/* Stats Overview */}
            <View style={styles.statsGrid}>
              {pool?.has_lives === false ? (
                <View style={styles.statsCard}>
                  <Text style={styles.statsValue}>{userStats?.total_points || 0}</Text>
                  <Text style={styles.statsLabel}>Total Points</Text>
                </View>
              ) : (
                <View style={styles.statsCard}>
                  <View style={styles.livesDisplay}>
                    {[...Array(livesLeft)].map((_, i) => (
                      <Ionicons key={i} name="heart" size={20} color={colors.heart} />
                    ))}
                    {[...Array(Math.max(0, (pool?.total_lives || 3) - livesLeft))].map((_, i) => (
                      <Ionicons key={`e-${i}`} name="heart-outline" size={20} color={colors.heartEmpty} />
                    ))}
                  </View>
                  <Text style={styles.statsLabel}>Lives Remaining</Text>
                </View>
              )}
              <View style={styles.statsCard}>
                <Text style={styles.statsValue}>#{userRank}</Text>
                <Text style={styles.statsLabel}>Your Rank</Text>
              </View>
              <View style={styles.statsCard}>
                <Text style={styles.statsValue}>{userPicks.length}</Text>
                <Text style={styles.statsLabel}>Picks Made</Text>
              </View>
              <View style={styles.statsCard}>
                <Text style={styles.statsValue}>{leaderboard.length}</Text>
                <Text style={styles.statsLabel}>Players</Text>
              </View>
            </View>

            {/* Picks for This Week - All Pool Members */}
            <View style={styles.recentPickCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Picks This Week</Text>
                <Text style={styles.cardSubtitle}>Gameweek {currentGameweek}</Text>
              </View>
              {leaderboard.map((entry) => {
                const memberPicks = allPoolPicks.filter(p => p.user_id === entry.user_id && p.gameweek === currentGameweek && p.team_id);
                const isCurrentUser = entry.user_id === userId;
                
                return (
                  <View key={entry.user_id} style={[styles.weekPickRow, isCurrentUser && styles.weekPickRowHighlight]}>
                    <View style={styles.weekPickUser}>
                      <View style={[styles.weekPickAvatar, isCurrentUser && styles.weekPickAvatarHighlight]}>
                        <Text style={[styles.weekPickAvatarText, isCurrentUser && styles.weekPickAvatarTextHighlight]}>
                          {entry.username[0].toUpperCase()}
                        </Text>
                      </View>
                      <Text style={[styles.weekPickUsername, isCurrentUser && styles.weekPickUsernameHighlight]}>
                        {isCurrentUser ? 'You' : entry.username}
                      </Text>
                    </View>
                    {memberPicks.length > 0 ? (
                      <View style={styles.weekPickBadges}>
                        {memberPicks.length > 1 && (
                          <Ionicons name="flash" size={14} color={colors.warning} />
                        )}
                        {memberPicks.map((memberPick) => {
                          const pickResult = memberPick.result?.toUpperCase();
                          return (
                            <View key={memberPick.id} style={[
                              styles.weekPickTeamBadge,
                              pickResult === 'WIN' && styles.weekPickTeamBadgeWin,
                              pickResult === 'DRAW' && styles.weekPickTeamBadgeDraw,
                              pickResult === 'LOSS' && styles.weekPickTeamBadgeLoss,
                            ]}>
                              <Text style={[
                                styles.weekPickTeamText,
                                pickResult === 'WIN' && styles.weekPickTeamTextWin,
                                pickResult === 'DRAW' && styles.weekPickTeamTextDraw,
                                pickResult === 'LOSS' && styles.weekPickTeamTextLoss,
                              ]}>
                                {teamShortName(memberPick.team_id)}
                              </Text>
                            </View>
                          );
                        })}
                      </View>
                    ) : (
                      <Text style={styles.weekPickNoPick}>No pick</Text>
                    )}
                  </View>
                );
              })}
            </View>
          </>
        )}

        {/* MAKE PICK TAB */}
        {activeTab === 'pick' && (
          <>
            <View style={styles.pickHeader}>
              <Text style={styles.pickTitle}>Select Your Team</Text>
              <Text style={styles.pickSubtitle}>
                Choose wisely - you can only pick each team {pool?.max_picks_per_team || 2} times
              </Text>
            </View>

            {/* Gameweek Selector */}
            <View style={styles.weekSelectorContainer}>
              <View style={styles.weekSelector}>
                <TouchableOpacity 
                  style={styles.weekButton}
                  onPress={() => { setPickGameweek(Math.max(currentGameweek, pickGameweek - 1)); setEditPickId(null); }}
                  disabled={pickGameweek <= currentGameweek}
                >
                  <Ionicons name="chevron-back" size={20} color={pickGameweek <= currentGameweek ? colors.textMuted : colors.textPrimary} />
                </TouchableOpacity>
                <View style={{ alignItems: 'center' }}>
                  <Text style={styles.weekText}>Gameweek {pickGameweek}</Text>
                  {pickGameweek === currentGameweek && (
                    <Text style={{ color: colors.success, fontSize: 11 }}>Current</Text>
                  )}
                  {pickGameweek > currentGameweek && (
                    <Text style={{ color: colors.info, fontSize: 11 }}>Future</Text>
                  )}
                </View>
                <TouchableOpacity 
                  style={styles.weekButton}
                  onPress={() => { setPickGameweek(Math.min(38, pickGameweek + 1)); setEditPickId(null); }}
                >
                  <Ionicons name="chevron-forward" size={20} color={colors.textPrimary} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Double Week (points-only pools) */}
            {isPointsPool && doubleWeeks.allowance > 0 && (() => {
              const doubleOn = isDoubleWeekOn(pickGameweek);
              const weekPicks = weekPicksFor(pickGameweek);
              const open = gameweekOpen(pickGameweek);
              if (!doubleOn && !open) return null;
              const target = getEditTarget(pickGameweek);

              return (
                <View style={[styles.doubleWeekCard, doubleOn && styles.doubleWeekCardActive]}>
                  <View style={styles.doubleWeekRow}>
                    <Ionicons name="flash" size={22} color={colors.warning} />
                    <View style={{ flex: 1, marginLeft: 10 }}>
                      <Text style={styles.doubleWeekTitle}>
                        {doubleOn ? 'Double Week on' : 'Double Week'}
                      </Text>
                      <Text style={styles.doubleWeekSub}>
                        {doubleOn
                          ? (weekPicks.length < 2
                            ? 'Pick a second team from a different match'
                            : 'Both picks count this gameweek')
                          : `Pick two teams this gameweek · ${doubleWeeks.remaining} of ${doubleWeeks.allowance} left`}
                      </Text>
                    </View>
                    {doubleOn ? (
                      open && (
                        <TouchableOpacity style={styles.doubleWeekButtonOutline} onPress={handleDeactivateDoubleWeek}>
                          <Text style={styles.doubleWeekButtonOutlineText}>Turn off</Text>
                        </TouchableOpacity>
                      )
                    ) : (
                      <TouchableOpacity
                        style={[styles.doubleWeekButton, doubleWeeks.remaining <= 0 && styles.doubleWeekButtonDisabled]}
                        onPress={handleActivateDoubleWeek}
                        disabled={doubleWeeks.remaining <= 0}
                      >
                        <Text style={styles.doubleWeekButtonText}>
                          {doubleWeeks.remaining > 0 ? 'Play' : 'None left'}
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>

                  {/* With both picks made, choose which one a new selection replaces */}
                  {doubleOn && weekPicks.length === 2 && (
                    <View style={styles.doubleWeekChips}>
                      <Text style={styles.doubleWeekSub}>Change:</Text>
                      {weekPicks.map((p) => {
                        const started = fixtureStarted(p.fixture_id);
                        const active = target?.id === p.id;
                        return (
                          <TouchableOpacity
                            key={p.id}
                            style={[styles.doubleWeekChip, active && styles.doubleWeekChipActive, started && { opacity: 0.5 }]}
                            onPress={() => { setEditPickId(p.id); setSelectedTeam(null); }}
                            disabled={started}
                          >
                            <Text style={[styles.doubleWeekChipText, active && styles.doubleWeekChipTextActive]}>
                              {teamShortName(p.team_id)}{started ? ' (started)' : ''}
                            </Text>
                          </TouchableOpacity>
                        );
                      })}
                    </View>
                  )}
                </View>
              );
            })()}

            {/* Teams Grid */}
            {(() => {
              // The pick a selection would replace (null = adding a new pick).
              // Editing is locked once that pick's match has started.
              const weekPicks = weekPicksFor(pickGameweek);
              const existingPick = getEditTarget(pickGameweek);
              const currentPickStarted = existingPick ? fixtureStarted(existingPick.fixture_id) : false;
              // Adding a second pick: it must come from a different match.
              const takenFixtureIds = existingPick ? [] : weekPicks.map(p => p.fixture_id);
              
              return (
                <View style={styles.teamsGrid}>
                  {teams.map((team) => {
                    const isSelected = selectedTeam === team.id;
                    const isUsed = usedTeamIds.includes(team.id);
                    const usedCount = usedTeamIds.filter(id => id === team.id).length;
                    const isMaxed = usedCount >= (pool?.max_picks_per_team || 2);
                    
                    // Check if this is one of the user's picks for this gameweek
                    const isUserPick = weekPicks.some(p => p.team_id === team.id);
                    
                    // Find fixture for this team in the selected gameweek
                    const gameweekFixture = fixtures.find(f => 
                      (f.home_team_id === team.id || f.away_team_id === team.id) &&
                      f.gameweek === pickGameweek
                    );
                    
                    // Check if match has already started
                    const matchStarted = gameweekFixture && new Date(gameweekFixture.kickoff_time) <= new Date();
                    
                    // Build match display string for selected gameweek
                    let matchDisplay = 'No match this week';
                    if (gameweekFixture) {
                      const homeTeam = teams.find(t => t.id === gameweekFixture.home_team_id);
                      const awayTeam = teams.find(t => t.id === gameweekFixture.away_team_id);
                      const homeShort = homeTeam?.short_name || homeTeam?.name?.substring(0, 3) || 'TBD';
                      const awayShort = awayTeam?.short_name || awayTeam?.name?.substring(0, 3) || 'TBD';
                      matchDisplay = `${homeShort} vs ${awayShort}`;
                    }
                    
                    // Determine if team is disabled:
                    // - maxed out picks for this team
                    // - no fixture this week
                    // - this team's match has started
                    // - user's current pick's match has started (can't edit anymore)
                    // - this is the user's current pick (no point selecting same team)
                    // - a second double week pick in the same match as the first
                    const sameMatchAsPick = !!gameweekFixture && takenFixtureIds.includes(gameweekFixture.id);
                    const isDisabled = isMaxed || !gameweekFixture || matchStarted || (currentPickStarted && !isUserPick) || isUserPick || sameMatchAsPick;
                    
                    return (
                      <TouchableOpacity
                        key={team.id}
                        style={[
                          styles.teamCard,
                          isSelected && styles.teamCardSelected,
                          isUserPick && styles.teamCardUserPick,
                          isDisabled && !isUserPick && styles.teamCardDisabled,
                        ]}
                        onPress={() => !isDisabled && !currentPickStarted && setSelectedTeam(isSelected ? null : team.id)}
                        disabled={isDisabled || currentPickStarted}
                        activeOpacity={0.7}
                      >
                        {/* Match Started ribbon banner */}
                        {matchStarted && !isMaxed && !isUserPick && (
                          <View style={styles.matchStartedBanner} pointerEvents="none">
                            <View style={styles.matchStartedRibbon}>
                              <Text style={styles.matchStartedText}>STARTED</Text>
                            </View>
                          </View>
                        )}
                        {/* User's Pick indicator */}
                        {isUserPick && (
                          <View style={styles.userPickBadge}>
                            <Text style={styles.userPickBadgeText}>YOUR PICK</Text>
                          </View>
                        )}
                        <Image
                          source={{ uri: team.logo }}
                          style={styles.teamLogo}
                          resizeMode="contain"
                        />
                        <Text style={styles.teamName} numberOfLines={1}>{team.name}</Text>
                        <Text style={styles.teamFixture} numberOfLines={1}>{matchDisplay}</Text>
                        {usedCount > 0 && (
                          <View style={[styles.usedCountBadge, isMaxed && styles.usedCountBadgeMaxed]}>
                            <Text style={[styles.usedCountText, isMaxed && styles.usedCountTextMaxed]}>
                              {usedCount}/{pool?.max_picks_per_team || 2}
                            </Text>
                          </View>
                        )}
                        {isSelected && (
                          <View style={styles.selectedIndicator}>
                            <Ionicons name="checkmark-circle" size={16} color={colors.accent} />
                          </View>
                        )}
                      </TouchableOpacity>
                    );
                  })}
                </View>
              );
            })()}

            {/* Confirm Button */}
            {selectedTeam && (() => {
              const isEditMode = !!getEditTarget(pickGameweek);
              const isSecondPick = !isEditMode && weekPicksFor(pickGameweek).length > 0;
              const teamName = teams.find(t => t.id === selectedTeam)?.name;
              
              return (
                <View style={styles.confirmContainer}>
                  <TouchableOpacity 
                    style={[styles.confirmButton, isEditMode && styles.confirmButtonEdit]} 
                    onPress={handleMakePick}
                  >
                    <Text style={styles.confirmButtonText}>
                      {isEditMode
                        ? `Confirm Pick Edit: ${teamName}`
                        : isSecondPick
                          ? `⚡ Confirm Second Pick: ${teamName}`
                          : `Confirm Pick: ${teamName}`
                      }
                    </Text>
                  </TouchableOpacity>
                </View>
              );
            })()}
          </>
        )}

        {/* STANDINGS TAB */}
        {activeTab === 'standings' && (
          <>
            <View style={styles.standingsHeader}>
              <Text style={styles.standingsTitle}>Pool Standings</Text>
              <Text style={styles.standingsSubtitle}>{leaderboard.length} players</Text>
            </View>

            {/* Column Headers */}
            <View style={styles.standingsColumnHeader}>
              <Text style={[styles.columnHeaderText, { width: 40 }]}>Rank</Text>
              <Text style={[styles.columnHeaderText, { flex: 1 }]}>Player</Text>
              <Text style={[styles.columnHeaderText, { width: 50, textAlign: 'center' }]}>Picks</Text>
              <Text style={[styles.columnHeaderText, { width: 50, textAlign: 'center' }]}>Pts</Text>
              <Text style={[styles.columnHeaderText, { width: 40, textAlign: 'center' }]}>GD</Text>
              {pool?.has_lives !== false && (
                <Text style={[styles.columnHeaderText, { width: 60, textAlign: 'center' }]}>Lives</Text>
              )}
            </View>

            {leaderboard.map((entry, index) => {
              const isCurrentUser = entry.user_id === userId;
              const pickCount = allPoolPicks.filter(p => p.user_id === entry.user_id).length;
              return (
                <View 
                  key={entry.user_id} 
                  style={[styles.standingsRow, isCurrentUser && styles.standingsRowHighlight]}
                >
                  <View style={[
                    styles.standingsRank,
                    index === 0 && styles.standingsRankGold,
                    index === 1 && styles.standingsRankSilver,
                    index === 2 && styles.standingsRankBronze,
                  ]}>
                    <Text style={styles.standingsRankText}>{index + 1}</Text>
                  </View>
                  <View style={styles.standingsInfo}>
                    <Text style={[styles.standingsName, isCurrentUser && styles.standingsNameHighlight]}>
                      {entry.username} {isCurrentUser && '(You)'}
                    </Text>
                  </View>
                  <Text style={styles.standingsStatText}>{pickCount}</Text>
                  <Text style={[styles.standingsStatText, styles.standingsPoints]}>{entry.total_points || 0}</Text>
                  <Text style={[styles.standingsStatText, styles.standingsGd]}>{formatGoalDifference(entry.goal_difference)}</Text>
                  {pool?.has_lives !== false && (
                    <View style={styles.standingsLives}>
                      {[...Array(entry.lives_left || 0)].map((_, i) => (
                        <Ionicons key={i} name="heart" size={12} color={colors.heart} />
                      ))}
                      {[...Array(Math.max(0, (pool?.total_lives || 3) - (entry.lives_left || 0)))].map((_, i) => (
                        <Ionicons key={`e-${i}`} name="heart-outline" size={12} color={colors.heartEmpty} />
                      ))}
                    </View>
                  )}
                </View>
              );
            })}
          </>
        )}

        {/* TEAMS TAB */}
        {activeTab === 'teams' && (
          <>
            <View style={styles.standingsHeader}>
              <Text style={styles.standingsTitle}>Team Leaderboard</Text>
              <Text style={styles.standingsSubtitle}>Points earned by players picking each team</Text>
            </View>

            <View style={styles.standingsColumnHeader}>
              <Text style={[styles.columnHeaderText, { width: 44 }]}>Rank</Text>
              <Text style={[styles.columnHeaderText, { flex: 1 }]}>Team</Text>
              <Text style={[styles.columnHeaderText, { width: 44, textAlign: 'center' }]}>Picks</Text>
              <Text style={[styles.columnHeaderText, { width: 40, textAlign: 'center' }]}>GD</Text>
              <Text style={[styles.columnHeaderText, { width: 44, textAlign: 'center' }]}>Pts</Text>
              <View style={{ width: 16 }} />
            </View>

            {teamLeaderboard.length === 0 && (
              <Text style={styles.historySubtitle}>No team data yet</Text>
            )}

            {teamLeaderboard.map((team) => (
              <TouchableOpacity
                key={team.team_id}
                style={styles.standingsRow}
                onPress={() => navigation.navigate('TeamPicks', {
                  poolId,
                  userId,
                  teamId: team.team_id,
                  teamName: team.team_name,
                  teamLogo: team.logo,
                })}
              >
                <View style={[
                  styles.standingsRank,
                  team.total_points > 0 && team.rank === 1 && styles.standingsRankGold,
                  team.total_points > 0 && team.rank === 2 && styles.standingsRankSilver,
                  team.total_points > 0 && team.rank === 3 && styles.standingsRankBronze,
                ]}>
                  <Text style={styles.standingsRankText}>{team.rank}</Text>
                </View>
                <View style={[styles.standingsInfo, styles.teamRowInfo]}>
                  {team.logo ? (
                    <Image source={{ uri: team.logo }} style={styles.teamRowLogo} resizeMode="contain" />
                  ) : null}
                  <Text style={styles.standingsName} numberOfLines={1}>{team.team_name}</Text>
                </View>
                <Text style={[styles.standingsStatText, { width: 44 }]}>{team.times_picked}</Text>
                <Text style={[styles.standingsStatText, styles.standingsGd]}>{formatGoalDifference(team.goal_difference)}</Text>
                <Text style={[styles.standingsStatText, { width: 44 }]}>{team.total_points}</Text>
                <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
              </TouchableOpacity>
            ))}
          </>
        )}

        {/* HISTORY TAB */}
        {activeTab === 'history' && (
          <>
            <View style={styles.historyHeader}>
              <Text style={styles.historyTitle}>Pick History</Text>
            </View>

            {/* Filter Toggle */}
            <View style={styles.historyFilterRow}>
              <TouchableOpacity
                style={[styles.historyFilterButton, historyFilter === 'week' && styles.historyFilterButtonActive]}
                onPress={() => { setHistoryFilter('week'); setSelectedHistoryUser(null); }}
              >
                <Ionicons name="calendar" size={16} color={historyFilter === 'week' ? colors.textOnAccent : colors.textMuted} />
                <Text style={[styles.historyFilterText, historyFilter === 'week' && styles.historyFilterTextActive]}>
                  By Week
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.historyFilterButton, historyFilter === 'user' && styles.historyFilterButtonActive]}
                onPress={() => setHistoryFilter('user')}
              >
                <Ionicons name="person" size={16} color={historyFilter === 'user' ? colors.textOnAccent : colors.textMuted} />
                <Text style={[styles.historyFilterText, historyFilter === 'user' && styles.historyFilterTextActive]}>
                  By Player
                </Text>
              </TouchableOpacity>
            </View>

            {/* Week Selector (when filter is 'week') */}
            {historyFilter === 'week' && (
              <>
                <View style={styles.weekSelectorContainer}>
                  <View style={styles.weekSelector}>
                    <TouchableOpacity 
                      style={styles.weekButton}
                      onPress={() => setHistoryWeek(Math.max(1, historyWeek - 1))}
                    >
                      <Ionicons name="chevron-back" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                    <Text style={styles.weekText}>Gameweek {historyWeek}</Text>
                    <TouchableOpacity 
                      style={styles.weekButton}
                      onPress={() => setHistoryWeek(Math.min(currentGameweek, historyWeek + 1))}
                    >
                      <Ionicons name="chevron-forward" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Week's picks */}
                {leaderboard.map((entry) => {
                  const picks = allPoolPicks.filter(p => p.user_id === entry.user_id && p.gameweek === historyWeek);

                  return (
                    <View key={entry.user_id} style={styles.historyRow}>
                      <View style={styles.historyUser}>
                        <View style={styles.historyAvatar}>
                          <Text style={styles.historyAvatarText}>
                            {entry.username[0].toUpperCase()}
                          </Text>
                        </View>
                        <Text style={styles.historyUsername}>{entry.username}</Text>
                      </View>
                      {renderHistoryPicks(picks, styles.historyTeam)}
                    </View>
                  );
                })}
              </>
            )}

            {/* User Selector (when filter is 'user') */}
            {historyFilter === 'user' && !selectedHistoryUser && (
              <>
                <Text style={styles.historySubtitle}>Select a player to view their pick history</Text>
                {leaderboard.map((entry) => (
                  <TouchableOpacity
                    key={entry.user_id}
                    style={styles.historyUserSelect}
                    onPress={() => setSelectedHistoryUser(entry)}
                  >
                    <View style={styles.historyAvatar}>
                      <Text style={styles.historyAvatarText}>
                        {entry.username[0].toUpperCase()}
                      </Text>
                    </View>
                    <View style={styles.historyUserSelectInfo}>
                      <Text style={styles.historyUsername}>{entry.username}</Text>
                      <Text style={styles.historyUserSelectSub}>
                        {entry.total_points || 0} pts{pool?.has_lives !== false ? ` • ${entry.lives_left || 0} lives` : ''}
                      </Text>
                    </View>
                    <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                  </TouchableOpacity>
                ))}
              </>
            )}

            {/* User's Full History (when a user is selected) */}
            {historyFilter === 'user' && selectedHistoryUser && (
              <>
                <TouchableOpacity 
                  style={styles.historyBackButton}
                  onPress={() => setSelectedHistoryUser(null)}
                >
                  <Ionicons name="arrow-back" size={18} color={colors.accent} />
                  <Text style={styles.historyBackText}>Back to players</Text>
                </TouchableOpacity>

                <View style={styles.historyUserHeader}>
                  <View style={styles.historyAvatarLarge}>
                    <Text style={styles.historyAvatarLargeText}>
                      {selectedHistoryUser.username[0].toUpperCase()}
                    </Text>
                  </View>
                  <Text style={styles.historyUserName}>{selectedHistoryUser.username}</Text>
                  <Text style={styles.historyUserStats}>
                    {selectedHistoryUser.total_points || 0} pts{pool?.has_lives !== false ? ` • ${selectedHistoryUser.lives_left || 0} lives` : ''}
                  </Text>
                </View>

                {/* All picks for this user */}
                {[...Array(currentGameweek)].map((_, i) => {
                  const gw = currentGameweek - i;
                  const picks = allPoolPicks.filter(p => p.user_id === selectedHistoryUser.user_id && p.gameweek === gw);

                  return (
                    <View key={gw} style={styles.historyWeekRow}>
                      <View style={styles.historyWeekBadge}>
                        <Text style={styles.historyWeekBadgeText}>GW{gw}</Text>
                      </View>
                      {renderHistoryPicks(picks, styles.historyWeekTeam, 'flex-start')}
                    </View>
                  );
                })}
              </>
            )}
          </>
        )}

        {/* INFO TAB */}
        {activeTab === 'info' && (
          <>
            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>Pool Rules</Text>
              <View style={styles.infoRow}>
                <Ionicons name="heart" size={18} color={colors.heart} />
                <Text style={styles.infoText}>Starting Lives: {pool?.total_lives || 3}</Text>
              </View>
              <View style={styles.infoRow}>
                <Ionicons name="repeat" size={18} color={colors.accent} />
                <Text style={styles.infoText}>Max picks per team: {pool?.max_picks_per_team || 2}</Text>
              </View>
              {isPointsPool && (
                <View style={styles.infoRow}>
                  <Ionicons name="flash" size={18} color={colors.warning} />
                  <Text style={styles.infoText}>
                    {pool?.double_weeks
                      ? `Double weeks: ${pool.double_weeks} per player (${doubleWeeks.remaining} left for you)`
                      : 'Double weeks: off'}
                  </Text>
                </View>
              )}
              <View style={styles.infoRow}>
                <Ionicons name="people" size={18} color={colors.info} />
                <Text style={styles.infoText}>Players: {leaderboard.length}</Text>
              </View>
            </View>

            {isPoolCreator && isPointsPool && adminDoubleWeeks !== null && (
              <View style={styles.infoCard}>
                <Text style={styles.infoTitle}>Double Weeks</Text>
                <Text style={styles.infoSubtitle}>
                  Let every player pick two teams in a gameweek and score both. Set to 0 to switch off - weeks already played stay scored.
                </Text>
                <View style={styles.doubleWeekRow}>
                  <TouchableOpacity
                    style={styles.counterButton}
                    onPress={() => setAdminDoubleWeeks(Math.max(0, adminDoubleWeeks - 1))}
                  >
                    <Ionicons name="remove" size={20} color={colors.textPrimary} />
                  </TouchableOpacity>
                  <Text style={styles.counterValue}>{adminDoubleWeeks}</Text>
                  <TouchableOpacity
                    style={styles.counterButton}
                    onPress={() => setAdminDoubleWeeks(Math.min(5, adminDoubleWeeks + 1))}
                  >
                    <Ionicons name="add" size={20} color={colors.textPrimary} />
                  </TouchableOpacity>
                  <View style={{ flex: 1 }} />
                  <TouchableOpacity
                    style={[styles.doubleWeekButton, adminDoubleWeeks === (pool?.double_weeks ?? 0) && styles.doubleWeekButtonDisabled]}
                    onPress={handleSaveDoubleWeekAllowance}
                    disabled={adminDoubleWeeks === (pool?.double_weeks ?? 0)}
                  >
                    <Text style={styles.doubleWeekButtonText}>Save</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}

            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>Session Code</Text>
              <Text style={styles.infoSubtitle}>Share this code to invite friends</Text>
              <View style={styles.sessionCodeContainer}>
                <Text style={styles.sessionCode}>{pool?.session_code || '------'}</Text>
                <TouchableOpacity 
                  style={styles.copyButton}
                  onPress={async () => {
                    if (pool?.session_code) {
                      await Clipboard.setStringAsync(pool.session_code);
                      Toast.show({
                        type: 'success',
                        text1: 'Copied!',
                        text2: 'Session code copied to clipboard',
                      });
                    }
                  }}
                >
                  <Ionicons name="copy" size={20} color={colors.accent} />
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>Pool Members</Text>
              {leaderboard.map((entry) => (
                <View key={entry.user_id} style={styles.memberRow}>
                  <View style={styles.memberAvatar}>
                    <Text style={styles.memberAvatarText}>
                      {entry.username[0].toUpperCase()}
                    </Text>
                  </View>
                  <Text style={styles.memberName}>{entry.username}</Text>
                  {entry.user_id === pool?.created_by && (
                    <View style={styles.creatorBadge}>
                      <Text style={styles.creatorBadgeText}>Creator</Text>
                    </View>
                  )}
                  {isPoolCreator && (
                    <TouchableOpacity
                      style={{ marginLeft: 10, padding: 4 }}
                      onPress={() => navigation.navigate('AdminEditPicks', {
                        poolId,
                        targetUserId: entry.user_id,
                        targetUsername: entry.username,
                      })}
                    >
                      <Ionicons name="create-outline" size={20} color={colors.accent} />
                    </TouchableOpacity>
                  )}
                </View>
              ))}
            </View>

            {/* Pool Actions */}
            <View style={styles.infoCard}>
              <Text style={styles.infoTitle}>Pool Actions</Text>
              <View style={styles.poolActionsContainer}>
                {isPoolCreator ? (
                  <TouchableOpacity style={styles.deleteButton} onPress={handleDeletePool}>
                    <Ionicons name="trash" size={20} color={colors.error} />
                    <Text style={styles.deleteButtonText}>Delete Pool</Text>
                  </TouchableOpacity>
                ) : (
                  <TouchableOpacity style={styles.leaveButton} onPress={handleLeavePool}>
                    <Ionicons name="exit" size={20} color={colors.warning} />
                    <Text style={styles.leaveButtonText}>Leave Pool</Text>
                  </TouchableOpacity>
                )}
              </View>
            </View>
          </>
        )}

        {/* Bottom spacing */}
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}
