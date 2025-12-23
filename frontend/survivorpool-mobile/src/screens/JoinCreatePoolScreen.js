import { View, Text, TextInput, TouchableOpacity, ScrollView, StatusBar, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/JoinCreatePoolScreen.styles';

export default function JoinCreatePoolScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);
  
  const [activeTab, setActiveTab] = useState('join'); // 'join' or 'create'
  const [sessionCode, setSessionCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Create pool form
  const [poolName, setPoolName] = useState('');
  const [poolDescription, setPoolDescription] = useState('');
  const [selectedLeague, setSelectedLeague] = useState(null);
  const [totalLives, setTotalLives] = useState('3');
  const [maxPicksPerTeam, setMaxPicksPerTeam] = useState('2');
  const [createdCode, setCreatedCode] = useState(null);

  const LEAGUES = [
    { id: 1, name: 'Premier League', country: 'England', icon: '🏴󠁧󠁢󠁥󠁮󠁧󠁿' },
    { id: 2, name: 'La Liga', country: 'Spain', icon: '🇪🇸' },
    { id: 3, name: 'Bundesliga', country: 'Germany', icon: '🇩🇪' },
    { id: 4, name: 'Serie A', country: 'Italy', icon: '🇮🇹' },
    { id: 5, name: 'Ligue 1', country: 'France', icon: '🇫🇷' },
  ];

  const generateSessionCode = () => {
    const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    let code = '';
    for (let i = 0; i < 6; i++) {
      code += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return code;
  };

  const handleJoinPool = async () => {
    if (!sessionCode.trim()) {
      alert('Please enter a session code');
      return;
    }

    setIsLoading(true);
    try {
      // In real app, would look up pool by session code first
      await apiService.joinPool(sessionCode, userId);
      alert('Successfully joined pool!');
      setSessionCode('');
      navigation.navigate('MyPools', { userId });
    } catch (error) {
      alert(error.message || 'Failed to join pool. Check the code and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreatePool = async () => {
    if (!poolName.trim()) {
      alert('Please enter a pool name');
      return;
    }
    if (!selectedLeague) {
      alert('Please select a league');
      return;
    }

    setIsLoading(true);
    try {
      const code = generateSessionCode();
      const newPool = await apiService.createPool({
        name: poolName,
        description: poolDescription || `${poolName} survivor pool`,
        competition_id: selectedLeague.id,
        total_lives: parseInt(totalLives) || 3,
        max_picks_per_team: parseInt(maxPicksPerTeam) || 2,
        session_code: code,
        creator_id: userId,
      });
      
      setCreatedCode(code);
      // Reset form
      setPoolName('');
      setPoolDescription('');
    } catch (error) {
      alert(error.message || 'Failed to create pool');
    } finally {
      setIsLoading(false);
    }
  };

  const copyToClipboard = () => {
    // In real app, use Clipboard API
    alert(`Code copied: ${createdCode}`);
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Join or Create Pool</Text>
        <Text style={styles.headerSubtitle}>Start competing with friends</Text>
      </View>

      {/* Tab Selector */}
      <View style={styles.tabSelector}>
        <TouchableOpacity
          style={[styles.tabOption, activeTab === 'join' && styles.tabOptionActive]}
          onPress={() => setActiveTab('join')}
        >
          <Ionicons 
            name="enter-outline" 
            size={20} 
            color={activeTab === 'join' ? colors.textOnAccent : colors.textMuted} 
          />
          <Text style={[styles.tabOptionText, activeTab === 'join' && styles.tabOptionTextActive]}>
            Join Pool
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tabOption, activeTab === 'create' && styles.tabOptionActive]}
          onPress={() => setActiveTab('create')}
        >
          <Ionicons 
            name="add-circle-outline" 
            size={20} 
            color={activeTab === 'create' ? colors.textOnAccent : colors.textMuted} 
          />
          <Text style={[styles.tabOptionText, activeTab === 'create' && styles.tabOptionTextActive]}>
            Create Pool
          </Text>
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1 }}
      >
        <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
          
          {/* JOIN TAB */}
          {activeTab === 'join' && (
            <View style={styles.formCard}>
              <View style={styles.iconCircle}>
                <Ionicons name="key" size={32} color={colors.accent} />
              </View>
              <Text style={styles.formTitle}>Enter Session Code</Text>
              <Text style={styles.formSubtitle}>
                Ask your pool admin for the 6-character code
              </Text>

              <TextInput
                style={styles.codeInput}
                placeholder="ABC123"
                placeholderTextColor={colors.placeholder}
                value={sessionCode}
                onChangeText={(text) => setSessionCode(text.toUpperCase())}
                autoCapitalize="characters"
                maxLength={6}
              />

              <TouchableOpacity
                style={[styles.primaryButton, isLoading && styles.buttonDisabled]}
                onPress={handleJoinPool}
                disabled={isLoading}
              >
                <Text style={styles.primaryButtonText}>
                  {isLoading ? 'Joining...' : 'Join Pool'}
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* CREATE TAB */}
          {activeTab === 'create' && !createdCode && (
            <View style={styles.formCard}>
              <View style={styles.iconCircle}>
                <Ionicons name="trophy" size={32} color={colors.accent} />
              </View>
              <Text style={styles.formTitle}>Create New Pool</Text>
              <Text style={styles.formSubtitle}>
                Set up your own survivor pool and invite friends
              </Text>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Pool Name *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., Office Champions"
                  placeholderTextColor={colors.placeholder}
                  value={poolName}
                  onChangeText={setPoolName}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Description</Text>
                <TextInput
                  style={[styles.input, styles.inputMultiline]}
                  placeholder="Optional description for your pool"
                  placeholderTextColor={colors.placeholder}
                  value={poolDescription}
                  onChangeText={setPoolDescription}
                  multiline
                  numberOfLines={2}
                />
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>League *</Text>
                <View style={styles.leagueGrid}>
                  {LEAGUES.map((league) => (
                    <TouchableOpacity
                      key={league.id}
                      style={[
                        styles.leagueOption,
                        selectedLeague?.id === league.id && styles.leagueOptionSelected,
                      ]}
                      onPress={() => setSelectedLeague(league)}
                    >
                      <Text style={styles.leagueIcon}>{league.icon}</Text>
                      <Text style={[
                        styles.leagueName,
                        selectedLeague?.id === league.id && styles.leagueNameSelected,
                      ]}>
                        {league.name}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.inputRow}>
                <View style={[styles.inputGroup, { flex: 1 }]}>
                  <Text style={styles.label}>Starting Lives</Text>
                  <View style={styles.counterContainer}>
                    <TouchableOpacity 
                      style={styles.counterButton}
                      onPress={() => setTotalLives(String(Math.max(1, parseInt(totalLives) - 1)))}
                    >
                      <Ionicons name="remove" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                    <Text style={styles.counterValue}>{totalLives}</Text>
                    <TouchableOpacity 
                      style={styles.counterButton}
                      onPress={() => setTotalLives(String(Math.min(5, parseInt(totalLives) + 1)))}
                    >
                      <Ionicons name="add" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                </View>

                <View style={[styles.inputGroup, { flex: 1 }]}>
                  <Text style={styles.label}>Max Picks/Team</Text>
                  <View style={styles.counterContainer}>
                    <TouchableOpacity 
                      style={styles.counterButton}
                      onPress={() => setMaxPicksPerTeam(String(Math.max(1, parseInt(maxPicksPerTeam) - 1)))}
                    >
                      <Ionicons name="remove" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                    <Text style={styles.counterValue}>{maxPicksPerTeam}</Text>
                    <TouchableOpacity 
                      style={styles.counterButton}
                      onPress={() => setMaxPicksPerTeam(String(Math.min(5, parseInt(maxPicksPerTeam) + 1)))}
                    >
                      <Ionicons name="add" size={20} color={colors.textPrimary} />
                    </TouchableOpacity>
                  </View>
                </View>
              </View>

              <View style={styles.rulesPreview}>
                <Text style={styles.rulesTitle}>Pool Rules Preview</Text>
                <View style={styles.ruleItem}>
                  <Ionicons name="heart" size={16} color={colors.heart} />
                  <Text style={styles.ruleText}>
                    Players start with {totalLives} lives
                  </Text>
                </View>
                <View style={styles.ruleItem}>
                  <Ionicons name="repeat" size={16} color={colors.accent} />
                  <Text style={styles.ruleText}>
                    Each team can be picked up to {maxPicksPerTeam} times
                  </Text>
                </View>
                <View style={styles.ruleItem}>
                  <Ionicons name="close-circle" size={16} color={colors.error} />
                  <Text style={styles.ruleText}>
                    Lose a life if your team loses
                  </Text>
                </View>
                <View style={styles.ruleItem}>
                  <Ionicons name="checkmark-circle" size={16} color={colors.success} />
                  <Text style={styles.ruleText}>
                    Win or draw keeps you safe
                  </Text>
                </View>
                {selectedLeague && (
                  <View style={styles.ruleItem}>
                    <Ionicons name="football" size={16} color={colors.info} />
                    <Text style={styles.ruleText}>
                      League: {selectedLeague.name}
                    </Text>
                  </View>
                )}
              </View>

              <TouchableOpacity
                style={[styles.primaryButton, isLoading && styles.buttonDisabled]}
                onPress={handleCreatePool}
                disabled={isLoading}
              >
                <Text style={styles.primaryButtonText}>
                  {isLoading ? 'Creating...' : 'Create Pool'}
                </Text>
              </TouchableOpacity>
            </View>
          )}

          {/* SUCCESS STATE - Pool Created */}
          {activeTab === 'create' && createdCode && (
            <View style={styles.successCard}>
              <View style={styles.successIcon}>
                <Ionicons name="checkmark-circle" size={64} color={colors.success} />
              </View>
              <Text style={styles.successTitle}>Pool Created!</Text>
              <Text style={styles.successSubtitle}>
                Share this code with friends to invite them
              </Text>

              <View style={styles.codeDisplay}>
                <Text style={styles.codeDisplayText}>{createdCode}</Text>
                <TouchableOpacity style={styles.copyButton} onPress={copyToClipboard}>
                  <Ionicons name="copy" size={24} color={colors.accent} />
                </TouchableOpacity>
              </View>

              <View style={styles.shareOptions}>
                <TouchableOpacity style={styles.shareButton}>
                  <Ionicons name="share-social" size={20} color={colors.textPrimary} />
                  <Text style={styles.shareButtonText}>Share</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.shareButton}>
                  <Ionicons name="chatbubble" size={20} color={colors.textPrimary} />
                  <Text style={styles.shareButtonText}>Message</Text>
                </TouchableOpacity>
              </View>

              <TouchableOpacity
                style={styles.primaryButton}
                onPress={() => {
                  setCreatedCode(null);
                  navigation.navigate('MyPools', { userId });
                }}
              >
                <Text style={styles.primaryButtonText}>Go to My Pools</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={() => setCreatedCode(null)}
              >
                <Text style={styles.secondaryButtonText}>Create Another Pool</Text>
              </TouchableOpacity>
            </View>
          )}

        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}
