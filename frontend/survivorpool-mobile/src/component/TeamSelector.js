import { View, Text, TouchableOpacity, Image, Alert, ScrollView } from 'react-native';
import { useState } from 'react';
import { styles } from './styles/TeamSelector.styles';

export default function TeamSelector({
  teams,
  usedTeamIds = [],
  onSelectTeam,
  isSelectionLocked = false,
  currentWeek,
  leagueCountry = 'england',
  maxSelections = 2
}) {
  const [selectedTeam, setSelectedTeam] = useState(null);

  const handleTeamClick = (team) => {
    if (isSelectionLocked) {
      Alert.alert('Selection Locked', 'Selection is locked for this week');
      return;
    }

    if (team.usedCount >= maxSelections) {
      Alert.alert(
        'Team Unavailable',
        `You've already used ${team.name} ${maxSelections} times this season`
      );
      return;
    }

    setSelectedTeam(team.id);
  };

  const handleConfirmSelection = () => {
    if (!selectedTeam) {
      Alert.alert('No Selection', 'Please select a team first');
      return;
    }

    if (onSelectTeam) {
      onSelectTeam(selectedTeam);
    }

    Alert.alert('Success', 'Team selection confirmed!');
    setSelectedTeam(null);
  };

  const isTeamDisabled = (team) => {
    return team.usedCount >= maxSelections || isSelectionLocked;
  };

  const isTeamSelected = (team) => {
    return selectedTeam === team.id;
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Select a Team</Text>
        <TouchableOpacity
          style={[
            styles.confirmButton,
            (!selectedTeam || isSelectionLocked) && styles.confirmButtonDisabled
          ]}
          onPress={handleConfirmSelection}
          disabled={!selectedTeam || isSelectionLocked}
        >
          <Text style={styles.confirmButtonText}>Confirm Selection</Text>
        </TouchableOpacity>
      </View>

      {/* Teams Grid */}
      <ScrollView showsVerticalScrollIndicator={false}>
        <View style={styles.teamsGrid}>
          {teams.map((team) => {
            const disabled = isTeamDisabled(team);
            const selected = isTeamSelected(team);

            return (
              <TouchableOpacity
                key={team.id}
                style={[
                  styles.teamCard,
                  selected && styles.teamCardSelected,
                  disabled && styles.teamCardDisabled
                ]}
                onPress={() => !disabled && handleTeamClick(team)}
                disabled={disabled}
                activeOpacity={0.7}
              >
                {/* Team Logo */}
                <Image
                  source={{ uri: team.logo }}
                  style={styles.teamLogo}
                  resizeMode="contain"
                />

                {/* Team Name */}
                <Text style={styles.teamName} numberOfLines={2}>
                  {team.name}
                </Text>

                {/* Next Match */}
                {team.nextMatch && (
                  <Text style={styles.teamMatch} numberOfLines={1}>
                    {team.nextMatch}
                  </Text>
                )}

                {/* Used Count Badge */}
                {team.usedCount > 0 && (
                  <View style={styles.usedBadge}>
                    <Text style={styles.usedBadgeText}>{team.usedCount}</Text>
                  </View>
                )}
              </TouchableOpacity>
            );
          })}
        </View>
      </ScrollView>
    </View>
  );
}