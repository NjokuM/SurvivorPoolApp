import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
    header: {
      backgroundColor: '#37003c',
      paddingVertical: 16,
      paddingHorizontal: 16,
      paddingTop: 50, // Account for status bar
    },
    container: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
    },
    leftSection: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 8,
    },
    title: {
      fontSize: 20,
      fontWeight: 'bold',
      color: '#fff',
    },
    rightSection: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 12,
    },
    sessionBadge: {
      flexDirection: 'row',
      alignItems: 'center',
      gap: 4,
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      paddingHorizontal: 8,
      paddingVertical: 4,
      borderRadius: 4,
    },
    sessionText: {
      fontSize: 12,
      color: '#fff',
    },
    weekText: {
      fontSize: 14,
      fontWeight: '600',
      color: '#fff',
    },
    avatar: {
      width: 32,
      height: 32,
      borderRadius: 16,
      backgroundColor: 'rgba(255, 255, 255, 0.2)',
      justifyContent: 'center',
      alignItems: 'center',
    },
    avatarText: {
      fontSize: 16,
      fontWeight: '600',
      color: '#fff',
    },
  });