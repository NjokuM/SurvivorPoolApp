import { View, Text, Image, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/PlayerSelection.styles';

// Mock teams data - replace with your actual teams import
const teams = [
  { id: 1, name: 'Arsenal', logo: 'https://example.com/arsenal.png' },
  { id: 2, name: 'Liverpool', logo: 'https://media.api-sports.io/football/leagues/39.png' },
  // Add more teams as needed
];

const leagueColors = {
  england: '#37003c',
  spain: '#FF4444',
  germany: '#D20515',
  italy: '#024494',
  france: '#DCDDE1'
};

export default function PlayerSelections({
  players = [],
  currentWeek,
  leagueCountry = 'england',
  leagueId,
  currentUserId
}) {
  const getTeamName = (teamId) => {
    const team = teams.find(t => t.id === teamId);
    return team ? team.name : 'Unknown';
  };

  const getTeamLogo = (teamId) => {
    const team = teams.find(t => t.id === teamId);
    return team ? team.logo : '';
  };

  const getCurrentWeekSelection = (user) => {
    if (!user.selections) return null;
    return user.selections.find(s => 
      s.week === currentWeek && (!leagueId || s.leagueId === leagueId)
    );
  };

  const getResultStyles = (result) => {
    switch (result) {
      case 'win':
        return {
          badge: styles.resultBadgeWin,
          text: styles.resultTextWin
        };
      case 'draw':
        return {
          badge: styles.resultBadgeDraw,
          text: styles.resultTextDraw
        };
      case 'loss':
        return {
          badge: styles.resultBadgeLoss,
          text: styles.resultTextLoss
        };
      default:
        return {
          badge: styles.resultBadgePending,
          text: styles.resultTextPending
        };
    }
  };

  const primaryColor = leagueColors[leagueCountry] || '#37003c';

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Ionicons name="calendar" size={20} color={primaryColor} />
        <Text style={styles.title}>Week {currentWeek} Selections</Text>
      </View>

      {/* Table */}
      <View style={styles.table}>
        {/* Table Header */}
        <View style={styles.tableHeader}>
          <View style={styles.playerColumn}>
            <Text style={styles.tableHeaderCell}>Player</Text>
          </View>
          <View style={styles.selectionColumn}>
            <Text style={styles.tableHeaderCell}>Selection</Text>
          </View>
          <View style={styles.resultColumn}>
            <Text style={[styles.tableHeaderCell, { textAlign: 'right' }]}>Result</Text>
          </View>
        </View>

        {/* Table Body */}
        <ScrollView style={{ maxHeight: 400 }}>
          {players.map((player, index) => {
            const selection = getCurrentWeekSelection(player);
            const isCurrentUser = player.id === currentUserId;
            const resultStyles = getResultStyles(selection?.result);

            return (
              <View
                key={player.id}
                style={[
                  styles.tableRow,
                  !player.isActive && styles.tableRowInactive,
                  isCurrentUser && styles.tableRowCurrentUser,
                  index === players.length - 1 && { borderBottomWidth: 0 }
                ]}
              >
                {/* Player */}
                <View style={styles.playerColumn}>
                  <View style={styles.playerCell}>
                    {isCurrentUser && <View style={styles.currentUserDot} />}
                    <View style={styles.playerInfo}>
                      <Text style={styles.playerName}>{player.username}</Text>
                      <Text style={styles.playerStatus}>
                        {player.isActive
                          ? `${player.remainingLives} lives left`
                          : 'Eliminated'}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Selection */}
                <View style={styles.selectionColumn}>
                  {selection ? (
                    <View style={styles.selectionCell}>
                      <Image
                        source={{ uri: getTeamLogo(selection.teamId) }}
                        style={styles.teamLogo}
                        resizeMode="contain"
                      />
                      <Text style={styles.teamName} numberOfLines={1}>
                        {getTeamName(selection.teamId)}
                      </Text>
                    </View>
                  ) : (
                    <Text style={styles.notSelectedText}>Not selected yet</Text>
                  )}
                </View>

                {/* Result */}
                <View style={styles.resultColumn}>
                  <View style={[styles.resultBadge, resultStyles.badge]}>
                    <Text style={[styles.resultText, resultStyles.text]}>
                      {selection?.result || 'Pending'}
                    </Text>
                  </View>
                </View>
              </View>
            );
          })}
        </ScrollView>
      </View>
    </View>
  );
}