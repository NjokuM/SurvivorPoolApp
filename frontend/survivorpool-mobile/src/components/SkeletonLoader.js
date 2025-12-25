import { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet } from 'react-native';
import { useTheme } from '../theme/colors';

export function SkeletonLoader({ width, height, borderRadius = 8, style }) {
  const { colors } = useTheme();
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 0.7,
          duration: 800,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 800,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [opacity]);

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: colors.border,
          opacity,
        },
        style,
      ]}
    />
  );
}

export function PoolCardSkeleton() {
  const { colors } = useTheme();
  
  return (
    <View style={[styles.poolCard, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <View style={styles.poolCardHeader}>
        <SkeletonLoader width={140} height={20} />
        <SkeletonLoader width={60} height={24} borderRadius={12} />
      </View>
      <View style={styles.poolCardBody}>
        <SkeletonLoader width={100} height={14} />
        <SkeletonLoader width={80} height={14} />
      </View>
      <View style={styles.poolCardFooter}>
        <SkeletonLoader width={70} height={12} />
        <SkeletonLoader width={90} height={12} />
      </View>
    </View>
  );
}

export function LeaderboardSkeleton() {
  const { colors } = useTheme();
  
  return (
    <View style={[styles.leaderboardRow, { backgroundColor: colors.surface, borderColor: colors.border }]}>
      <SkeletonLoader width={32} height={32} borderRadius={16} />
      <View style={{ flex: 1, marginLeft: 12 }}>
        <SkeletonLoader width={120} height={16} />
        <SkeletonLoader width={80} height={12} style={{ marginTop: 4 }} />
      </View>
      <SkeletonLoader width={50} height={20} />
    </View>
  );
}

export function ProfileSkeleton() {
  return (
    <View style={styles.profileContainer}>
      <SkeletonLoader width={80} height={80} borderRadius={40} />
      <SkeletonLoader width={150} height={24} style={{ marginTop: 16 }} />
      <SkeletonLoader width={200} height={14} style={{ marginTop: 8 }} />
      <View style={styles.statsRow}>
        <SkeletonLoader width={80} height={60} borderRadius={12} />
        <SkeletonLoader width={80} height={60} borderRadius={12} />
        <SkeletonLoader width={80} height={60} borderRadius={12} />
      </View>
    </View>
  );
}

export function TeamGridSkeleton() {
  return (
    <View style={styles.teamGrid}>
      {[...Array(8)].map((_, i) => (
        <View key={i} style={styles.teamCardSkeleton}>
          <SkeletonLoader width={32} height={32} borderRadius={16} />
          <SkeletonLoader width={50} height={10} style={{ marginTop: 6 }} />
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  poolCard: {
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  poolCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  poolCardBody: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  poolCardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  leaderboardRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
  },
  profileContainer: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  statsRow: {
    flexDirection: 'row',
    gap: 16,
    marginTop: 20,
  },
  teamGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  teamCardSkeleton: {
    width: '23%',
    alignItems: 'center',
    padding: 12,
  },
});
