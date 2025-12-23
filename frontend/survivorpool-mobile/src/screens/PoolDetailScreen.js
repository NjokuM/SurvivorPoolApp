import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, RefreshControl, Image } from 'react-native';
import { useEffect, useState, useCallback } from 'react';
import { Ionicons } from '@expo/vector-icons';
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
  const [currentGameweek, setCurrentGameweek] = useState(18);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [historyWeek, setHistoryWeek] = useState(null);
  const [historyFilter, setHistoryFilter] = useState('week'); // 'week' or 'user'
  const [selectedHistoryUser, setSelectedHistoryUser] = useState(null);

  const loadData = useCallback(async () => {
    try {
      const data = await apiService.getHomeScreenData(userId, poolId);
      setPool(data.pool);
      setUserStats(data.userStats);
      setLeaderboard(data.leaderboard);
      setTeams(data.teams);
      setFixtures(data.fixtures);
      setUserPicks(data.userPicks);
      setCurrentGameweek(data.currentGameweek);
      setHistoryWeek(data.currentGameweek - 1);
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

  const handleMakePick = async () => {
    if (!selectedTeam) {
      alert('Please select a team');
      return;
    }

    try {
      const fixture = fixtures.find(f => 
        f.home_team_id === selectedTeam || f.away_team_id === selectedTeam
      );
      
      await apiService.createPick({
        pool_id: poolId,
        user_id: userId,
        team_id: selectedTeam,
        fixture_id: fixture?.id || 1,
      });
      alert('Pick submitted successfully!');
      setSelectedTeam(null);
      loadData();
    } catch (error) {
      alert(error.message || 'Failed to submit pick');
    }
  };

  const getUsedTeamIds = () => {
    return userPicks.map(p => p.team_id);
  };

  const getDeadlineCountdown = () => {
    const now = new Date();
    const deadline = new Date();
    deadline.setDate(deadline.getDate() + 1);
    deadline.setHours(15, 0, 0, 0);
    
    const diff = deadline - now;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      return `${Math.floor(hours / 24)}d ${hours % 24}h`;
    }
    return `${hours}h ${minutes}m`;
  };

  const livesLeft = userStats?.lives_left || pool?.total_lives || 3;
  const usedTeamIds = getUsedTeamIds();

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
            {/* Deadline Alert */}
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
                <Text style={styles.statsValue}>#{userStats?.rank || '-'}</Text>
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

            {/* Recent Pick */}
            {userPicks.length > 0 && (
              <View style={styles.recentPickCard}>
                <Text style={styles.cardTitle}>Your Last Pick</Text>
                <View style={styles.recentPickContent}>
                  <View style={styles.teamBadge}>
                    <Text style={styles.teamBadgeText}>
                      {teams.find(t => t.id === userPicks[userPicks.length - 1]?.team_id)?.name || 'Team'}
                    </Text>
                  </View>
                  <Text style={styles.recentPickWeek}>
                    Gameweek {userPicks[userPicks.length - 1]?.gameweek || currentGameweek - 1}
                  </Text>
                </View>
              </View>
            )}

            {/* Top 3 Leaderboard Preview */}
            <View style={styles.leaderboardPreview}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Leaderboard</Text>
                <TouchableOpacity onPress={() => setActiveTab('standings')}>
                  <Text style={styles.seeAllText}>See All</Text>
                </TouchableOpacity>
              </View>
              {leaderboard.slice(0, 3).map((entry, index) => (
                <View key={entry.user_id} style={styles.leaderboardRow}>
                  <View style={[styles.rankBadge, index === 0 && styles.rankBadgeGold]}>
                    <Text style={styles.rankText}>{index + 1}</Text>
                  </View>
                  <Text style={styles.leaderboardName}>{entry.username}</Text>
                  <View style={styles.leaderboardLives}>
                    <Ionicons name="heart" size={14} color={colors.heart} />
                    <Text style={styles.leaderboardLivesText}>{entry.lives_remaining}</Text>
                  </View>
                </View>
              ))}
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

            {/* Teams Grid */}
            <View style={styles.teamsGrid}>
              {teams.map((team) => {
                const isSelected = selectedTeam === team.id;
                const isUsed = usedTeamIds.includes(team.id);
                const usedCount = usedTeamIds.filter(id => id === team.id).length;
                const isMaxed = usedCount >= (pool?.max_picks_per_team || 2);
                
                return (
                  <TouchableOpacity
                    key={team.id}
                    style={[
                      styles.teamCard,
                      isSelected && styles.teamCardSelected,
                      isMaxed && styles.teamCardDisabled,
                    ]}
                    onPress={() => !isMaxed && setSelectedTeam(isSelected ? null : team.id)}
                    disabled={isMaxed}
                    activeOpacity={0.7}
                  >
                    {isMaxed && (
                      <View style={styles.teamCardOverlay}>
                        <Ionicons name="close-circle" size={24} color={colors.error} />
                      </View>
                    )}
                    <Image
                      source={{ uri: team.logo }}
                      style={styles.teamLogo}
                      resizeMode="contain"
                    />
                    <Text style={styles.teamName} numberOfLines={1}>{team.name}</Text>
                    <Text style={styles.teamFixture} numberOfLines={1}>{team.nextMatch}</Text>
                    {usedCount > 0 && (
                      <View style={styles.usedBadge}>
                        <Text style={styles.usedBadgeText}>Used {usedCount}x</Text>
                      </View>
                    )}
                    {isSelected && (
                      <View style={styles.selectedIndicator}>
                        <Ionicons name="checkmark-circle" size={20} color={colors.accent} />
                      </View>
                    )}
                  </TouchableOpacity>
                );
              })}
            </View>

            {/* Confirm Button */}
            {selectedTeam && (
              <View style={styles.confirmContainer}>
                <TouchableOpacity style={styles.confirmButton} onPress={handleMakePick}>
                  <Text style={styles.confirmButtonText}>
                    Confirm Pick: {teams.find(t => t.id === selectedTeam)?.name}
                  </Text>
                </TouchableOpacity>
              </View>
            )}
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
                  <Text style={styles.standingsStatText}>-</Text>
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
                      onPress={() => setHistoryWeek(Math.min(currentGameweek - 1, historyWeek + 1))}
                    >
                      <Ionicons name="chevron-forward" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Week's picks */}
                {leaderboard.map((entry) => {
                  const pick = userPicks.find(p => p.user_id === entry.user_id && p.gameweek === historyWeek);
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
                                {pick?.result === 'win' ? '✓' : pick?.result === 'draw' ? '=' : pick?.result === 'loss' ? '✗' : '-'}
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
                {[...Array(currentGameweek - 1)].map((_, i) => {
                  const gw = currentGameweek - 1 - i;
                  const pick = userPicks.find(p => p.user_id === selectedHistoryUser.user_id && p.gameweek === gw);
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
                              {pick?.result === 'win' ? '✓' : pick?.result === 'draw' ? '=' : pick?.result === 'loss' ? '✗' : '-'}
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
                <Text style={styles.sessionCode}>{pool?.session_code || 'ABC123'}</Text>
                <TouchableOpacity style={styles.copyButton}>
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
                  {entry.user_id === pool?.creator_id && (
                    <View style={styles.creatorBadge}>
                      <Text style={styles.creatorBadgeText}>Creator</Text>
                    </View>
                  )}
                </View>
              ))}
            </View>
          </>
        )}

        {/* Bottom spacing */}
        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}
