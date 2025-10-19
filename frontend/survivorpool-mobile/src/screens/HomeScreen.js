import { View, Text, TouchableOpacity, FlatList, StyleSheet } from 'react-native';
import { useEffect, useState } from 'react';
import API from '../api/api';

export default function HomeScreen({ route, navigation }) {
  const { userId } = route.params;
  const [userPools, setUserPools] = useState([]);
  const [availablePools, setAvailablePools] = useState([]);

  useEffect(() => {
    // Fetch user's pools
    const fetchPools = async () => {
      try {
        const res = await API.get(`/users/${userId}/pools`);
        setUserPools(res.data || []);
      } catch (err) {
        console.error("Error fetching user pools:", err);
      }
    };

    // Fetch other pools that can be joined
    const fetchAvailablePools = async () => {
      try {
        const res = await API.get(`/pools/available`);
        setAvailablePools(res.data || []);
      } catch (err) {
        console.error("Error fetching available pools:", err);
      }
    };

    fetchPools();
    fetchAvailablePools();
  }, []);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Your Pools</Text>
      {userPools.length === 0 ? (
        <Text>You have no pools yet.</Text>
      ) : (
        <FlatList
          data={userPools}
          keyExtractor={(item) => item.id.toString()}
          renderItem={({ item }) => <Text style={styles.pool}>{item.name}</Text>}
        />
      )}

      <Text style={[styles.title, { marginTop: 30 }]}>Join or Create a Pool</Text>
      <TouchableOpacity style={styles.button} onPress={() => navigation.navigate('CreatePool')}>
        <Text style={styles.buttonText}>Create Pool</Text>
      </TouchableOpacity>

      <FlatList
        data={availablePools}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={styles.poolButton}
            onPress={() => alert(`Joining pool: ${item.name}`)}
          >
            <Text>{item.name}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 20, backgroundColor: '#fff' },
  title: { fontSize: 24, fontWeight: 'bold', color: '#3F1F93', marginBottom: 10 },
  pool: { fontSize: 18, paddingVertical: 5 },
  button: {
    backgroundColor: '#3F1F93',
    paddingVertical: 15,
    borderRadius: 12,
    marginBottom: 15,
    alignItems: 'center',
  },
  buttonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  poolButton: {
    padding: 10,
    borderWidth: 1,
    borderColor: '#3F1F93',
    borderRadius: 8,
    marginBottom: 10,
  },
});