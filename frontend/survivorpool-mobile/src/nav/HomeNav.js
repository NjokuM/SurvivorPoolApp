import { View, Text, TouchableOpacity, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/HomeNav.styles';
import TeamSelector from '../component/TeamSelector';
import LeagueManager from '../component/LeagueManager';
// Commented out until we create these components:
// import Leaderboard from '../component/Leaderboard';
// import RulesBanner from '../component/RulesBanner';
// import PlayerSelections from '../component/PlayerSelections';
// import SelectionHistory from '../component/SelectionHistory';

export default function HomeNav({
  activeTab,
  setActiveTab,
  league,
  teams,
  usedTeamIds,
  onSelectTeam,
  isSelectionLocked,
  currentWeek,
  user,
  maxSelections
}) {
  const tabs = [
    { id: 'standings', label: 'Standings', icon: 'trophy' },
    { id: 'leagues', label: 'Leagues', icon: 'people' },
    { id: 'week', label: `Week ${currentWeek}`, icon: 'calendar' },
    { id: 'history', label: 'History', icon: 'list' }
  ];

  const renderTabButton = (tab) => {
    const isActive = activeTab === tab.id;
    return (
      <TouchableOpacity
        key={tab.id}
        style={[styles.tabButton, isActive && styles.tabButtonActive]}
        onPress={() => setActiveTab(tab.id)}
      >
        <Ionicons
          name={tab.icon}
          size={18}
          color={isActive ? '#fff' : '#666'}
        />
        <Text style={[styles.tabText, isActive && styles.tabTextActive]}>
          {tab.label}
        </Text>
      </TouchableOpacity>
    );
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'standings':
        return (
          <View style={{ padding: 20, alignItems: 'center' }}>
            <Text style={{ fontSize: 16, color: '#666' }}>
              Standings - Coming Soon
            </Text>
            {/* Uncomment when RulesBanner and Leaderboard are ready:
            <RulesBanner
              maxLives={league?.maxLives}
              maxSelections={maxSelections}
            />
            <Leaderboard
              participants={league?.participants}
              leagueCountry={league?.country}
              sessionCode={league?.sessionCode}
              currentUserId={user?.id}
            />
            */}
          </View>
        );

      case 'league':
        return <LeagueManager />;

      case 'week':
        return (
          <>
            <TeamSelector
              teams={teams}
              usedTeamIds={usedTeamIds}
              onSelectTeam={onSelectTeam}
              isSelectionLocked={isSelectionLocked}
              currentWeek={currentWeek}
              leagueCountry={league?.country}
              maxSelections={maxSelections}
            />
            {/* Uncomment when PlayerSelections is ready:
            <PlayerSelections
              players={league?.participants}
              currentWeek={currentWeek}
              leagueCountry={league?.country}
              leagueId={league?.id}
            />
            */}
          </>
        );

      case 'history':
        return (
          <View style={{ padding: 20, alignItems: 'center' }}>
            <Text style={{ fontSize: 16, color: '#666' }}>
              History - Coming Soon
            </Text>
            {/* Uncomment when SelectionHistory is ready:
            <SelectionHistory
              user={user}
              username={user?.username}
              leagueCountry={league?.country}
              leagueId={league?.id}
            />
            */}
          </View>
        );

      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      {/* Tab Bar */}
      <View style={styles.tabBar}>
        {tabs.map(renderTabButton)}
      </View>

      {/* Tab Content */}
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {renderContent()}
      </ScrollView>
    </View>
  );
}