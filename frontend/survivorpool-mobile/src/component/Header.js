import { View, Text, TouchableOpacity } from 'react-native';
import { styles } from './styles/Header.styles';
import { Ionicons } from '@expo/vector-icons';

export default function Header({ currentWeek, totalWeeks, sessionCode, user, onLogout, onProfile }) {
  const getUserInitial = () => {
    return user?.username?.charAt(0).toUpperCase() || user?.email?.charAt(0).toUpperCase() || 'U';
  };

  return (
    <View style={styles.header}>
      <View style={styles.container}>
        {/* Left side - Logo and Title */}
        <View style={styles.leftSection}>
          <Ionicons name="trophy" size={24} color="#00ff85" />
          <Text style={styles.title}>Survivor Pool</Text>
        </View>

        {/* Right side - Session Code, Week, and User */}
        <View style={styles.rightSection}>
          {sessionCode && (
            <View style={styles.sessionBadge}>
              <Ionicons name="people" size={14} color="#fff" />
              <Text style={styles.sessionText}>Session: {sessionCode}</Text>
            </View>
          )}
          
          <Text style={styles.weekText}>
            Week {currentWeek}/{totalWeeks}
          </Text>

          {/* User Avatar */}
          <TouchableOpacity style={styles.avatar} onPress={onProfile}>
            <Text style={styles.avatarText}>{getUserInitial()}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </View>
  );
}

