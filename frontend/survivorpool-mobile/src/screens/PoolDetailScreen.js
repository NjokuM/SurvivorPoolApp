import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl, Image, Alert } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import * as Clipboard from 'expo-clipboard';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/PoolDetailScreen.styles';

export default function PoolDetailScreen({ route, navigation }) {
  const { poolId, userId, poolName } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);
  
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState('summary'); // 'summary', 'pick', 'standings', 'history', 'info'
  
  // Data state
  const [pool, setPool] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
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

  const loadData = useCallback(async () => {
    try {
      const data = await apiService.getHomeScreenData(userId, poolId);
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
      
      // Check if user already has a pick for this gameweek (edit scenario)
      const existingPick = userPicks.find(p => p.gameweek === pickGameweek);
      
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
          text1: 'Pick Submitted!',
          text2: `Your pick for Gameweek ${pickGameweek} is locked in`,
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
            <Ionicons name="heart" size={16} color={colors.heart} />
            <Text style={styles.livesText}>{livesLeft}</Text>
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
                const memberPick = allPoolPicks.find(p => p.user_id === entry.user_id && p.gameweek === currentGameweek);
                const memberTeam = memberPick ? teams.find(t => t.id === memberPick.team_id) : null;
                const isCurrentUser = entry.user_id === userId;
                const pickResult = memberPick?.result?.toUpperCase();
                
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
                    {memberTeam ? (
                      <View style={[
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
                          {memberTeam.short_name || memberTeam.name}
                        </Text>
                      </View>
                    ) : (
                      <Text style={styles.weekPickNoPick}>No pick</Text>
                    )}
                  </View>
                );
              })}
            </View>

            {/* Top 3 Leaderboard Preview */}
            <View style={styles.leaderboardPreview}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Leaderboard</Text>
                <TouchableOpacity onPress={() => setActiveTab('standings')}>
                  <Text style={styles.seeAllText}>See All</Text>
                </TouchableOpacity>
              </View>
              {leaderboard.slice(0, 3).map((entry, index) => {
                const userPickCount = allPoolPicks.filter(p => p.user_id === entry.user_id).length;
                return (
                  <View key={entry.user_id} style={styles.leaderboardRow}>
                    <View style={[styles.rankBadge, index === 0 && styles.rankBadgeGold]}>
                      <Text style={styles.rankText}>{index + 1}</Text>
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.leaderboardName}>{entry.username}</Text>
                      <Text style={{ fontSize: 11, color: colors.textMuted }}>
                        {userPickCount} picks • {entry.total_points || 0} pts
                      </Text>
                    </View>
                    <View style={styles.leaderboardLives}>
                      <Ionicons name="heart" size={14} color={colors.heart} />
                      <Text style={styles.leaderboardLivesText}>{entry.lives_left}</Text>
                    </View>
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
                  onPress={() => setPickGameweek(Math.max(currentGameweek, pickGameweek - 1))}
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
                  onPress={() => setPickGameweek(Math.min(38, pickGameweek + 1))}
                >
                  <Ionicons name="chevron-forward" size={20} color={colors.textPrimary} />
                </TouchableOpacity>
              </View>
            </View>

            {/* Teams Grid */}
            {(() => {
              // Check if user's current pick for this gameweek has already started (lock editing)
              const existingPick = userPicks.find(p => p.gameweek === pickGameweek);
              const existingPickFixture = existingPick ? fixtures.find(f => f.id === existingPick.fixture_id) : null;
              const currentPickStarted = existingPickFixture && new Date(existingPickFixture.kickoff_time) <= new Date();
              
              return (
                <View style={styles.teamsGrid}>
                  {teams.map((team) => {
                    const isSelected = selectedTeam === team.id;
                    const isUsed = usedTeamIds.includes(team.id);
                    const usedCount = usedTeamIds.filter(id => id === team.id).length;
                    const isMaxed = usedCount >= (pool?.max_picks_per_team || 2);
                    
                    // Check if this is the user's pick for this gameweek
                    const isUserPick = existingPick && existingPick.team_id === team.id;
                    
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
                    const isDisabled = isMaxed || !gameweekFixture || matchStarted || (currentPickStarted && !isUserPick) || isUserPick;
                    
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
              const existingPickForGameweek = userPicks.find(p => p.gameweek === pickGameweek);
              const isEditMode = !!existingPickForGameweek;
              
              return (
                <View style={styles.confirmContainer}>
                  <TouchableOpacity 
                    style={[styles.confirmButton, isEditMode && styles.confirmButtonEdit]} 
                    onPress={handleMakePick}
                  >
                    <Text style={styles.confirmButtonText}>
                      {isEditMode 
                        ? `Confirm Pick Edit: ${teams.find(t => t.id === selectedTeam)?.name}`
                        : `Confirm Pick: ${teams.find(t => t.id === selectedTeam)?.name}`
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
              <Text style={[styles.columnHeaderText, { width: 60, textAlign: 'center' }]}>Lives</Text>
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
                  <View style={styles.standingsLives}>
                    {[...Array(entry.lives_left || 0)].map((_, i) => (
                      <Ionicons key={i} name="heart" size={12} color={colors.heart} />
                    ))}
                    {[...Array(Math.max(0, (pool?.total_lives || 3) - (entry.lives_left || 0)))].map((_, i) => (
                      <Ionicons key={`e-${i}`} name="heart-outline" size={12} color={colors.heartEmpty} />
                    ))}
                  </View>
                </View>
              );
            })}
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
                  const pick = allPoolPicks.find(p => p.user_id === entry.user_id && p.gameweek === historyWeek);
                  const team = pick ? teams.find(t => t.id === pick.team_id) : null;
                  
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
                      <View style={styles.historyPick}>
                        {team ? (
                          <>
                            <Text style={styles.historyTeam}>{team.name}</Text>
                            <View style={[
                              styles.historyResult,
                              pick?.result === 'win' && styles.historyResultWin,
                              pick?.result === 'draw' && styles.historyResultDraw,
                              pick?.result === 'loss' && styles.historyResultLoss,
                            ]}>
                              <Text style={styles.historyResultText}>
                                {pick?.result === 'win' ? '✓' : pick?.result === 'draw' ? 'D' : pick?.result === 'loss' ? '✗' : '-'}
                              </Text>
                            </View>
                          </>
                        ) : (
                          <Text style={styles.historyNoPick}>No pick</Text>
                        )}
                      </View>
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
                        {entry.total_points || 0} pts • {entry.lives_left || 0} lives
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
                    {selectedHistoryUser.total_points || 0} pts • {selectedHistoryUser.lives_left || 0} lives
                  </Text>
                </View>

                {/* All picks for this user */}
                {[...Array(currentGameweek)].map((_, i) => {
                  const gw = currentGameweek - i;
                  const pick = allPoolPicks.find(p => p.user_id === selectedHistoryUser.user_id && p.gameweek === gw);
                  const team = pick ? teams.find(t => t.id === pick.team_id) : null;
                  
                  return (
                    <View key={gw} style={styles.historyWeekRow}>
                      <View style={styles.historyWeekBadge}>
                        <Text style={styles.historyWeekBadgeText}>GW{gw}</Text>
                      </View>
                      {team ? (
                        <>
                          <Text style={styles.historyWeekTeam}>{team.name}</Text>
                          <View style={[
                            styles.historyResult,
                            pick?.result === 'win' && styles.historyResultWin,
                            pick?.result === 'draw' && styles.historyResultDraw,
                            pick?.result === 'loss' && styles.historyResultLoss,
                          ]}>
                            <Text style={styles.historyResultText}>
                              {pick?.result === 'win' ? '✓' : pick?.result === 'draw' ? 'D' : pick?.result === 'loss' ? '✗' : '-'}
                            </Text>
                          </View>
                        </>
                      ) : (
                        <Text style={styles.historyNoPick}>No pick</Text>
                      )}
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
              <View style={styles.infoRow}>
                <Ionicons name="people" size={18} color={colors.info} />
                <Text style={styles.infoText}>Players: {leaderboard.length}</Text>
              </View>
            </View>

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
