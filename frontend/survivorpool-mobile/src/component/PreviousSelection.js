import { View, Text, Image, ScrollView } from 'react-native';
import { styles } from './styles/PreviousSelection.styles';

// Mock teams data - replace with your actual teams import
const teams = [
  { id: 1, name: 'Arsenal', logo: 'https://example.com/arsenal.png' },
  { id: 2, name: 'Liverpool', logo: 'https://example.com/liverpool.png' },
  // Add more teams as needed
];

export default function PreviousSelection({ selections = [] }) {
  if (selections.length === 0) {
    return null;
  }

  // Sort selections by week in descending order
  const sortedSelections = [...selections].sort((a, b) => b.week - a.week);

  const getTeam = (teamId) => {
    return teams.find(team => team.id === teamId);
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

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Previous Selections</Text>
      
      <ScrollView style={styles.selectionsList} showsVerticalScrollIndicator={false}>
        {sortedSelections.map((selection, index) => {
          const team = getTeam(selection.teamId);
          if (!team) return null;

          const resultStyles = getResultStyles(selection.result);
          const isLast = index === sortedSelections.length - 1;

          return (
            <View
              key={selection.week}
              style={[
                styles.selectionItem,
                isLast && { borderBottomWidth: 0 }
              ]}
            >
              <View style={styles.selectionLeft}>
                <Text style={styles.weekText}>Week {selection.week}:</Text>
                <View style={styles.teamInfo}>
                  <Image
                    source={{ uri: team.logo }}
                    style={styles.teamLogo}
                    resizeMode="contain"
                  />
                  <Text style={styles.teamName}>{team.name}</Text>
                </View>
              </View>
              
              <View style={[styles.resultBadge, resultStyles.badge]}>
                <Text style={[styles.resultText, resultStyles.text]}>
                  {selection.result || 'Pending'}
                </Text>
              </View>
            </View>
          );
        })}
      </ScrollView>
    </View>
  );
}