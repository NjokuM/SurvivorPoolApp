import { View, Text, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/Leaderboard.styles';

export default function Leaderboard({ 
  participants = [], 
  leagueCountry = 'england',
  sessionCode,
  currentUserId 
}) {
  // Sort users by remaining lives (descending) and then by username
  const sortedUsers = [...participants].sort((a, b) => {
    if (b.remainingLives !== a.remainingLives) {
      return b.remainingLives - a.remainingLives;
    }
    return a.username.localeCompare(b.username);
  });

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Ionicons name="people" size={20} color="#37003c" />
          <Text style={styles.title}>League Standings</Text>
        </View>
        {sessionCode && (
          <View style={styles.sessionBadge}>
            <Text style={styles.sessionText}>Session: {sessionCode}</Text>
          </View>
        )}
      </View>

      {/* Table */}
      <View style={styles.table}>
        {/* Table Header */}
        <View style={styles.tableHeader}>
          <View style={styles.rankColumn}>
            <Text style={styles.tableHeaderCell}>Rank</Text>
          </View>
          <View style={styles.playerColumn}>
            <Text style={styles.tableHeaderCell}>Player</Text>
          </View>
          <View style={styles.livesColumn}>
            <Text style={[styles.tableHeaderCell, { textAlign: 'right' }]}>Lives</Text>
          </View>
          <View style={styles.statusColumn}>
            <Text style={[styles.tableHeaderCell, { textAlign: 'right' }]}>Status</Text>
          </View>
        </View>

        {/* Table Body */}
        <ScrollView style={{ maxHeight: 400 }}>
          {sortedUsers.map((user, index) => {
            const isCurrentUser = user.id === currentUserId;
            
            return (
              <View
                key={user.id}
                style={[
                  styles.tableRow,
                  !user.isActive && styles.tableRowInactive,
                  index === sortedUsers.length - 1 && { borderBottomWidth: 0 }
                ]}
              >
                {/* Rank */}
                <View style={styles.rankColumn}>
                  <Text style={[styles.tableCell, styles.rankCell]}>
                    {index + 1}
                  </Text>
                </View>

                {/* Player */}
                <View style={styles.playerColumn}>
                  <View style={styles.playerCell}>
                    {isCurrentUser && (
                      <Ionicons name="checkmark-circle" size={16} color="#37003c" />
                    )}
                    <Text style={styles.tableCell}>{user.username}</Text>
                  </View>
                </View>

                {/* Lives */}
                <View style={styles.livesColumn}>
                  <Text style={styles.tableCell}>{user.remainingLives}</Text>
                </View>

                {/* Status */}
                <View style={styles.statusColumn}>
                  <View
                    style={[
                      styles.statusBadge,
                      user.isActive
                        ? styles.statusBadgeActive
                        : styles.statusBadgeEliminated
                    ]}
                  >
                    <Text
                      style={[
                        styles.statusText,
                        user.isActive
                          ? styles.statusTextActive
                          : styles.statusTextEliminated
                      ]}
                    >
                      {user.isActive ? 'Active' : 'Eliminated'}
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