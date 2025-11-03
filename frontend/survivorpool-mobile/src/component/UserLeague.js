import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/UserLeague.styles';

const leagueColors = {
  england: '#37003c',
  spain: '#FF4444',
  germany: '#D20515',
  italy: '#024494',
  france: '#DCDDE1'
};

export default function UserLeague({
  leagues = [],
  onSelectLeague,
  currentLeagueId
}) {
  const getLeagueColor = (country) => {
    return leagueColors[country] || '#37003c';
  };

  const capitalizeFirst = (str) => {
    return str.charAt(0).toUpperCase() + str.slice(1);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Ionicons name="people" size={20} color="#37003c" />
          <Text style={styles.title}>My Leagues</Text>
        </View>
      </View>

      {/* Leagues Grid */}
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.leaguesGrid}>
          {leagues.map((league) => {
            const primaryColor = getLeagueColor(league.country);
            const isCurrentLeague = league.id === currentLeagueId;

            return (
              <TouchableOpacity
                key={league.id}
                style={[
                  styles.leagueCard,
                  isCurrentLeague && styles.leagueCardActive,
                  { borderColor: isCurrentLeague ? primaryColor : '#e5e7eb' }
                ]}
                onPress={() => onSelectLeague(league.id)}
                activeOpacity={0.7}
              >
                {/* Header */}
                <View style={styles.leagueCardHeader}>
                  <View style={styles.leagueNameRow}>
                    <Ionicons name="flag" size={14} color={primaryColor} />
                    <Text style={styles.leagueName} numberOfLines={1}>
                      {league.name}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.badge,
                      league.isActive ? styles.badgeActive : styles.badgeFinished
                    ]}
                  >
                    <Text
                      style={[
                        styles.badgeText,
                        league.isActive
                          ? styles.badgeTextActive
                          : styles.badgeTextFinished
                      ]}
                    >
                      {league.isActive ? 'Active' : 'Finished'}
                    </Text>
                  </View>
                </View>

                {/* Footer */}
                <View style={styles.leagueFooter}>
                  <View style={styles.countryRow}>
                    <Ionicons name="trophy" size={12} color="#000" />
                    <Text style={styles.countryText}>
                      {capitalizeFirst(league.country)}
                    </Text>
                  </View>
                  <View style={styles.sessionCode}>
                    <Text style={styles.sessionCodeText}>
                      {league.sessionCode}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>
    </View>
  );
}