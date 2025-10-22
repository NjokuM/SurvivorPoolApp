import { View, Text, TouchableOpacity, FlatList, ScrollView } from 'react-native';
import { useEffect, useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import API from '../api/api';
import Header from '../component/Header';
import { styles } from './styles/HomeScreen.styles';

export default function HomeScreen({ route, navigation }) {
  const { userId } = route.params;
  const [user, setUser] = useState(null);
  const [userPools, setUserPools] = useState([]);
  const [availablePools, setAvailablePools] = useState([]);
  const [currentWeek] = useState(1); // This should come from your API
  const [totalWeeks] = useState(38); // Premier League season weeks

  useEffect(() => {
    // Fetch user data
    const fetchUser = async () => {
      try {
        const res = await API.get(`/users/${userId}`);
        setUser(res.data);
      } catch (err) {
        console.error("Error fetching user:", err);
      }
    };

    // Fetch user's pools
    const fetchPools = async () => {
      try {
        const res = await API.get(`/users/${userId}/pools`);
        setUserPools(res.data || []);
      } catch (err) {
        console.error("Error fetching user pools:", err);
      }
    };

    // Fetch available pools
    const fetchAvailablePools = async () => {
      try {
        const res = await API.get(`/pools/available`);
        setAvailablePools(res.data || []);
      } catch (err) {
        console.error("Error fetching available pools:", err);
      }
    };

    fetchUser();
    fetchPools();
    fetchAvailablePools();
  }, [userId]);

  const handleJoinPool = async (poolId, poolName) => {
    try {
      await API.post(`/pools/${poolId}/join`, { userId });
      alert(`Successfully joined ${poolName}!`);
      // Refresh pools
      const res = await API.get(`/users/${userId}/pools`);
      setUserPools(res.data || []);
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
    // Navigate to profile screen or show menu
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

  return (
    <View style={styles.container}>
      <Header
        currentWeek={currentWeek}
        totalWeeks={totalWeeks}
        sessionCode={userPools[0]?.sessionCode}
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