import { View, Text, TouchableOpacity, FlatList, ScrollView } from 'react-native';
import { useEffect, useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import API from '../api/api';
import Header from '../component/Header';
import HomeNav from '../nav/HomeNav';
import Leaderboard from '../component/Leaderboard';
import { styles } from './styles/HomeScreen.styles';

export default function HomeScreen({ route, navigation }) {
  const { userId } = route.params;
  const [user, setUser] = useState(null);
  const [userPools, setUserPools] = useState([]);
  const [availablePools, setAvailablePools] = useState([]);
  const [currentWeek, setCurrentWeek] = useState(1);
  const [totalWeeks] = useState(38); // Premier League season weeks
  
  // HomeNav specific state
  const [activeTab, setActiveTab] = useState('standings');
  const [league, setLeague] = useState(null);
  const [teams, setTeams] = useState([]);
  const [usedTeamIds, setUsedTeamIds] = useState([]);
  const [isSelectionLocked, setIsSelectionLocked] = useState(false);
  const [maxSelections, setMaxSelections] = useState(2);

  useEffect(() => {
    fetchUserData();
    fetchPools();
    fetchAvailablePools();
    fetchLeagueData();
    fetchTeams();
  }, [userId]);

  const fetchUserData = async () => {
    try {
      const res = await API.get(`/users/${userId}`);
      setUser(res.data);
    } catch (err) {
      console.error("Error fetching user:", err);
    }
  };

  const fetchPools = async () => {
    try {
      const res = await API.get(`/users/${userId}/pools`);
      setUserPools(res.data || []);
    } catch (err) {
      console.error("Error fetching user pools:", err);
    }
  };

  const fetchAvailablePools = async () => {
    try {
      const res = await API.get(`/pools/available`);
      setAvailablePools(res.data || []);
    } catch (err) {
      console.error("Error fetching available pools:", err);
    }
  };

  const fetchLeagueData = async () => {
    try {
      // Fetch the first league the user is in (or modify to select specific league)
      const res = await API.get(`/users/${userId}/leagues/current`);
      if (res.data) {
        setLeague(res.data);
        setMaxSelections(res.data.maxSelections || 2);
        setCurrentWeek(res.data.currentWeek || 1);
      } else {
        // Mock league data if API doesn't return anything
        setLeague({
          id: 'league1',
          name: 'Premier League Survivors',
          sessionCode: 'PL123456',
          participants: [],
          country: 'england',
          maxLives: 3,
          maxSelections: 2,
          currentWeek: 1
        });
      }
    } catch (err) {
      console.error("Error fetching league data:", err);
      // Set mock data on error
      setLeague({
        id: 'league1',
        name: 'Premier League Survivors',
        sessionCode: 'PL123456',
        participants: [],
        country: 'england',
        maxLives: 3,
        maxSelections: 2,
        currentWeek: 1
      });
    }
  };

  const fetchTeams = async () => {
    try {
      const res = await API.get('/teams');
      setTeams(res.data || []);
    } catch (err) {
      console.error("Error fetching teams:", err);
      // Mock teams data
      setTeams([
        { id: 1, name: 'Arsenal', logo: 'https://example.com/arsenal.png', usedCount: 0, nextMatch: 'vs Chelsea' },
        { id: 2, name: 'Liverpool', logo: 'https://example.com/liverpool.png', usedCount: 1, nextMatch: 'vs Man Utd' },
        // Add more teams as needed
      ]);
    }
  };

  const handleSelectTeam = (teamId) => {
    console.log('Team selected:', teamId);
    // Add your team selection logic here
    // Update usedTeamIds
    setUsedTeamIds([...usedTeamIds, teamId]);
    
    // Send to API
    try {
      API.post('/selections', {
        userId,
        teamId,
        week: currentWeek,
        leagueId: league?.id
      });
    } catch (err) {
      console.error('Error saving selection:', err);
    }
  };

  const handleJoinPool = async (poolId, poolName) => {
    try {
      await API.post(`/pools/${poolId}/join`, { userId });
      alert(`Successfully joined ${poolName}!`);
      fetchPools();
    } catch (err) {
      console.error("Error joining pool:", err);
      alert("Failed to join pool");
    }
  };

  const handleLogout = () => {
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  const handleProfile = () => {
    alert('Profile menu');
  };

  const renderUserPool = ({ item }) => (
    <TouchableOpacity 
      style={styles.poolCard}
      onPress={() => navigation.navigate('PoolDetails', { poolId: item.id })}
    >
      <Text style={styles.poolName}>{item.name}</Text>
      <View style={styles.poolInfo}>
        <Ionicons name="people" size={16} color="#666" />
        <Text style={styles.poolInfoText}>
          {item.participantCount || 0} participants
        </Text>
      </View>
      <View style={styles.poolInfo}>
        <Ionicons name="calendar" size={16} color="#666" />
        <Text style={styles.poolInfoText}>Week {currentWeek}</Text>
      </View>
    </TouchableOpacity>
  );

  const renderAvailablePool = ({ item }) => (
    <View style={styles.availablePoolCard}>
      <View style={styles.availablePoolHeader}>
        <Text style={styles.poolName}>{item.name}</Text>
        <TouchableOpacity 
          style={styles.joinButton}
          onPress={() => handleJoinPool(item.id, item.name)}
        >
          <Text style={styles.joinButtonText}>Join</Text>
        </TouchableOpacity>
      </View>
      <View style={styles.poolInfo}>
        <Ionicons name="people" size={16} color="#666" />
        <Text style={styles.poolInfoText}>
          {item.participantCount || 0} participants
        </Text>
      </View>
      {item.sessionCode && (
        <View style={styles.poolInfo}>
          <Ionicons name="key" size={16} color="#666" />
          <Text style={styles.poolInfoText}>Code: {item.sessionCode}</Text>
        </View>
      )}
    </View>
  );

  // Show loading state while data is being fetched
  if (!league || !user) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <Text>Loading...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Header
        currentWeek={currentWeek}
        totalWeeks={totalWeeks}
        sessionCode={league?.sessionCode}
        user={user}
        onLogout={handleLogout}
        onProfile={handleProfile}
      />

      <ScrollView style={styles.content}>
        {/* User Stats Card */}
        <View style={styles.userStatsCard}>
          <View style={styles.statsHeader}>
            <Text style={styles.statsTitle}>Your Stats</Text>
            <View style={styles.livesContainer}>
              <Ionicons name="heart" size={20} color="#e90052" />
              <Text style={styles.livesText}>
                {user?.remainingLives || 3} Lives
              </Text>
            </View>
          </View>
        </View>

        {/* Leaderboard */}
        <Leaderboard
          participants={league?.participants || []}
          leagueCountry={league?.country}
          sessionCode={league?.sessionCode}
          currentUserId={userId}
        />

        {/* Navigation Tabs */}
        <HomeNav
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          league={league}
          teams={teams}
          usedTeamIds={usedTeamIds}
          onSelectTeam={handleSelectTeam}
          isSelectionLocked={isSelectionLocked}
          currentWeek={currentWeek}
          user={user}
          maxSelections={maxSelections}
        />

        {/* Your Pools Section */}
        <Text style={styles.sectionTitle}>Your Pools</Text>
        {userPools.length === 0 ? (
          <Text style={styles.emptyText}>You haven't joined any pools yet.</Text>
        ) : (
          <FlatList
            data={userPools}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderUserPool}
            scrollEnabled={false}
          />
        )}

        <View style={styles.divider} />

        {/* Create Pool Button */}
        <TouchableOpacity 
          style={styles.createButton} 
          onPress={() => navigation.navigate('CreatePool', { userId })}
        >
          <Text style={styles.createButtonText}>Create New Pool</Text>
        </TouchableOpacity>

        {/* Available Pools Section */}
        <Text style={styles.sectionTitle}>Available Pools</Text>
        {availablePools.length === 0 ? (
          <Text style={styles.emptyText}>No pools available to join.</Text>
        ) : (
          <FlatList
            data={availablePools}
            keyExtractor={(item) => item.id.toString()}
            renderItem={renderAvailablePool}
            scrollEnabled={false}
          />
        )}
      </ScrollView>
    </View>
  );
}