import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';

const ILLUSTRATIONS = {
  noPools: {
    icon: 'football-outline',
    title: 'No Pools Yet',
    subtitle: 'Join a pool with a session code or create your own to start competing!',
  },
  noLeaderboard: {
    icon: 'trophy-outline',
    title: 'No Rankings Yet',
    subtitle: 'Rankings will appear once players start making picks.',
  },
  noPicks: {
    icon: 'hand-left-outline',
    title: 'No Picks Made',
    subtitle: 'Make your first pick to get started in this pool!',
  },
  noHistory: {
    icon: 'time-outline',
    title: 'No History',
    subtitle: 'Your pick history will appear here after each gameweek.',
  },
  noResults: {
    icon: 'search-outline',
    title: 'No Results Found',
    subtitle: 'Try adjusting your search or filters.',
  },
  noNotifications: {
    icon: 'notifications-outline',
    title: 'All Caught Up!',
    subtitle: 'You have no new notifications.',
  },
  error: {
    icon: 'alert-circle-outline',
    title: 'Something Went Wrong',
    subtitle: 'Please try again or contact support if the problem persists.',
  },
  offline: {
    icon: 'cloud-offline-outline',
    title: 'You\'re Offline',
    subtitle: 'Check your internet connection and try again.',
  },
};

export function EmptyState({ 
  type = 'noPools', 
  title, 
  subtitle, 
  icon,
  actionLabel, 
  onAction,
  compact = false,
}) {
  const { colors } = useTheme();
  const illustration = ILLUSTRATIONS[type] || ILLUSTRATIONS.noPools;
  
  const displayIcon = icon || illustration.icon;
  const displayTitle = title || illustration.title;
  const displaySubtitle = subtitle || illustration.subtitle;

  return (
    <View style={[styles.container, compact && styles.containerCompact]}>
      <View style={[
        styles.iconContainer, 
        { backgroundColor: colors.accent + '15' },
        compact && styles.iconContainerCompact,
      ]}>
        <Ionicons 
          name={displayIcon} 
          size={compact ? 32 : 48} 
          color={colors.accent} 
        />
      </View>
      
      <Text style={[
        styles.title, 
        { color: colors.textPrimary },
        compact && styles.titleCompact,
      ]}>
        {displayTitle}
      </Text>
      
      <Text style={[
        styles.subtitle, 
        { color: colors.textMuted },
        compact && styles.subtitleCompact,
      ]}>
        {displaySubtitle}
      </Text>
      
      {actionLabel && onAction && (
        <TouchableOpacity 
          style={[styles.actionButton, { backgroundColor: colors.accent }]}
          onPress={onAction}
        >
          <Text style={[styles.actionButtonText, { color: colors.textOnAccent }]}>
            {actionLabel}
          </Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  containerCompact: {
    paddingVertical: 24,
    paddingHorizontal: 20,
  },
  iconContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
  },
  iconContainerCompact: {
    width: 64,
    height: 64,
    borderRadius: 32,
    marginBottom: 12,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    textAlign: 'center',
    marginBottom: 8,
  },
  titleCompact: {
    fontSize: 16,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 15,
    textAlign: 'center',
    lineHeight: 22,
    maxWidth: 280,
  },
  subtitleCompact: {
    fontSize: 13,
    lineHeight: 18,
    maxWidth: 240,
  },
  actionButton: {
    marginTop: 24,
    paddingVertical: 14,
    paddingHorizontal: 28,
    borderRadius: 12,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
});
