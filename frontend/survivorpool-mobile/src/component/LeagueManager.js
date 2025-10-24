import { View, Text, TextInput, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/LeagueManager.styles';

const countryOptions = [
  { value: 'england', label: 'England - Premier League', prefix: 'PL', color: '#37003c' },
  { value: 'spain', label: 'Spain - LaLiga', prefix: 'LL', color: '#FF4444' },
  { value: 'germany', label: 'Germany - Bundesliga', prefix: 'BL', color: '#D20515' },
  { value: 'italy', label: 'Italy - Serie A', prefix: 'SA', color: '#024494' },
  { value: 'france', label: 'France - Ligue 1', prefix: 'L1', color: '#DCDDE1' }
];

export default function LeagueManager({ onJoinLeague, onCreateLeague }) {
  // Join League State
  const [sessionCode, setSessionCode] = useState('');
  const [username, setUsername] = useState('');

  // Create League State
  const [createLeagueName, setCreateLeagueName] = useState('');
  const [createLeagueCountry, setCreateLeagueCountry] = useState('england');

  // Generate a random 6-digit code
  const generateRandomCode = (prefix) => {
    const randomDigits = Math.floor(100000 + Math.random() * 900000);
    return `${prefix}${randomDigits}`;
  };

  const handleJoinLeague = () => {
    if (!sessionCode || !username) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    // Determine country from session code prefix
    const prefix = sessionCode.substring(0, 2);
    const country = countryOptions.find(option => option.prefix === prefix)?.value || 'england';

    if (onJoinLeague) {
      onJoinLeague({ sessionCode, username, country });
    }

    Alert.alert('Success', `Joined league with code: ${sessionCode}`);
    setSessionCode('');
    setUsername('');
  };

  const handleCreateLeague = () => {
    if (!createLeagueName) {
      Alert.alert('Error', 'Please enter a league name');
      return;
    }

    // Get the prefix for the selected country
    const prefix = countryOptions.find(option => option.value === createLeagueCountry)?.prefix || 'PL';

    // Generate a session code
    const generatedSessionCode = generateRandomCode(prefix);

    if (onCreateLeague) {
      onCreateLeague({
        name: createLeagueName,
        country: createLeagueCountry,
        sessionCode: generatedSessionCode
      });
    }

    const countryLabel = countryOptions.find(option => option.value === createLeagueCountry)?.label || createLeagueCountry;
    Alert.alert(
      'Success',
      `Created ${countryLabel} league "${createLeagueName}" with code: ${generatedSessionCode}`
    );
    
    setCreateLeagueName('');
    setCreateLeagueCountry('england');
  };

  const getCountryColor = (country) => {
    return countryOptions.find(option => option.value === country)?.color || '#37003c';
  };

  return (
    <ScrollView style={styles.container}>
      {/* Join League Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleRow}>
            <Ionicons name="people" size={20} color="#37003c" />
            <Text style={styles.cardTitle}>Join Existing League</Text>
          </View>
          <Text style={styles.cardDescription}>Enter the session code to join a league</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <TextInput
              style={styles.input}
              placeholder="Session Code (e.g., PL123456)"
              value={sessionCode}
              onChangeText={(text) => setSessionCode(text.toUpperCase())}
              autoCapitalize="characters"
            />
            <Text style={styles.helperText}>
              Session codes start with league initials (PL, LL, BL, SA, L1)
            </Text>
          </View>

          <View style={styles.inputGroup}>
            <TextInput
              style={styles.input}
              placeholder="Your Username"
              value={username}
              onChangeText={setUsername}
            />
          </View>

          <TouchableOpacity
            style={[styles.button, { backgroundColor: '#37003c' }]}
            onPress={handleJoinLeague}
          >
            <Text style={styles.buttonText}>Join League</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Create League Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <View style={styles.cardTitleRow}>
            <Ionicons name="add-circle" size={20} color="#37003c" />
            <Text style={styles.cardTitle}>Create New League</Text>
          </View>
          <Text style={styles.cardDescription}>Start a new league and invite friends</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputGroup}>
            <TextInput
              style={styles.input}
              placeholder="League Name"
              value={createLeagueName}
              onChangeText={setCreateLeagueName}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Select League</Text>
            <View style={styles.radioGroup}>
              {countryOptions.map((option) => (
                <TouchableOpacity
                  key={option.value}
                  style={[
                    styles.radioOption,
                    createLeagueCountry === option.value && styles.radioOptionSelected
                  ]}
                  onPress={() => setCreateLeagueCountry(option.value)}
                >
                  <View style={[
                    styles.radioCircle,
                    createLeagueCountry === option.value && styles.radioCircleSelected
                  ]}>
                    {createLeagueCountry === option.value && (
                      <View style={styles.radioCircleInner} />
                    )}
                  </View>
                  <View style={styles.radioLabelRow}>
                    <Ionicons name="flag" size={16} color={option.color} />
                    <Text style={styles.radioLabel}>{option.label}</Text>
                  </View>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <TouchableOpacity
            style={[styles.button, { backgroundColor: getCountryColor(createLeagueCountry) }]}
            onPress={handleCreateLeague}
          >
            <Text style={styles.buttonText}>Create League</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}