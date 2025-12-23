import { View, Text, TextInput, TouchableOpacity, ScrollView, StatusBar, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';

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

const createStyles = (colors) => StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  header: {
    paddingTop: 60,
    paddingBottom: 20,
    paddingHorizontal: 20,
    backgroundColor: colors.background,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
  },
  tabSelector: {
    flexDirection: 'row',
    marginHorizontal: 20,
    backgroundColor: colors.surface,
    borderRadius: 16,
    padding: 4,
    marginBottom: 20,
  },
  tabOption: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  tabOptionActive: {
    backgroundColor: colors.accent,
  },
  tabOptionText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textMuted,
  },
  tabOptionTextActive: {
    color: colors.textOnAccent,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 20,
    paddingBottom: 100,
  },
  formCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  iconCircle: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.accent + '20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  formTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  formSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 24,
  },
  codeInput: {
    width: '100%',
    height: 64,
    backgroundColor: colors.inputBackground,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: colors.border,
    fontSize: 28,
    fontWeight: '700',
    color: colors.textPrimary,
    textAlign: 'center',
    letterSpacing: 8,
    marginBottom: 20,
  },
  inputGroup: {
    width: '100%',
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  input: {
    height: 52,
    backgroundColor: colors.inputBackground,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: 16,
    fontSize: 16,
    color: colors.textPrimary,
  },
  inputMultiline: {
    height: 80,
    paddingTop: 14,
    textAlignVertical: 'top',
  },
  inputRow: {
    flexDirection: 'row',
    gap: 12,
    width: '100%',
  },
  counterContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.inputBackground,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    overflow: 'hidden',
  },
  counterButton: {
    width: 48,
    height: 48,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: colors.border,
  },
  counterValue: {
    flex: 1,
    fontSize: 20,
    fontWeight: '700',
    color: colors.textPrimary,
    textAlign: 'center',
  },
  rulesPreview: {
    width: '100%',
    backgroundColor: colors.inputBackground,
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  rulesTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textMuted,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  ruleItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 8,
  },
  ruleText: {
    fontSize: 14,
    color: colors.textSecondary,
  },
  leagueGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  leagueOption: {
    width: '48%',
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.inputBackground,
    borderRadius: 12,
    padding: 12,
    borderWidth: 2,
    borderColor: colors.border,
    gap: 8,
  },
  leagueOptionSelected: {
    borderColor: colors.accent,
    backgroundColor: colors.accent + '15',
  },
  leagueIcon: {
    fontSize: 20,
  },
  leagueName: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textPrimary,
    flex: 1,
  },
  leagueNameSelected: {
    color: colors.accent,
  },
  primaryButton: {
    width: '100%',
    backgroundColor: colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  primaryButtonText: {
    color: colors.textOnAccent,
    fontSize: 16,
    fontWeight: '700',
  },
  successCard: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    padding: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: colors.border,
  },
  successIcon: {
    marginBottom: 16,
  },
  successTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  successSubtitle: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
    marginBottom: 24,
  },
  codeDisplay: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.accent + '15',
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    width: '100%',
  },
  codeDisplayText: {
    flex: 1,
    fontSize: 32,
    fontWeight: '700',
    color: colors.accent,
    textAlign: 'center',
    letterSpacing: 6,
  },
  copyButton: {
    padding: 8,
  },
  shareOptions: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  shareButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: colors.inputBackground,
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
  },
  shareButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  secondaryButton: {
    marginTop: 12,
    paddingVertical: 12,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.accent,
  },
});
