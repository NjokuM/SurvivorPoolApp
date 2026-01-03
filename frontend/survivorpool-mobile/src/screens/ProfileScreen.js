import { View, Text, TouchableOpacity, ScrollView, StatusBar, Switch, Linking, Alert } from 'react-native';
import { useState, useEffect } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/ProfileScreen.styles';

const SUPPORT_EMAIL = 'bremorebros60@gmail.com';

export default function ProfileScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors, isDark, toggleTheme } = useTheme();
  const styles = createStyles(colors);
  
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState({ totalPools: 0, totalPicks: 0, winRate: 0 });
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [deadlineReminders, setDeadlineReminders] = useState(true);
  const [resultNotifications, setResultNotifications] = useState(true);

  useEffect(() => {
    loadUserAndStats();
  }, []);

  const loadUserAndStats = async () => {
    try {
      const [userData, userPools, userPicks] = await Promise.all([
        apiService.getUser(userId),
        apiService.getUserPools(userId),
        apiService.getUserPicks(userId),
      ]);
      setUser(userData);
      
      // Calculate stats from real data
      const totalPools = userPools.length;
      const totalPicks = userPicks.length;
      const wins = userPicks.filter(p => p.result === 'WIN' || p.result === 'win').length;
      const completedPicks = userPicks.filter(p => p.result).length;
      const winRate = completedPicks > 0 ? Math.round((wins / completedPicks) * 100) : 0;
      
      setStats({ totalPools, totalPicks, winRate });
    } catch (error) {
      console.error('Error loading user:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await apiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    }
    navigation.reset({
      index: 0,
      routes: [{ name: 'Login' }],
    });
  };

  const handleContactSupport = () => {
    Alert.alert(
      'Contact Support',
      'How can we help you?',
      [
        {
          text: 'Report a Bug',
          onPress: () => openEmailWithTemplate('bug'),
        },
        {
          text: 'Request a Feature',
          onPress: () => openEmailWithTemplate('feature'),
        },
        {
          text: 'General Inquiry',
          onPress: () => openEmailWithTemplate('general'),
        },
        {
          text: 'Cancel',
          style: 'cancel',
        },
      ]
    );
  };

  const openEmailWithTemplate = (type) => {
    const username = user?.firstName || user?.userName || 'User';
    const templates = {
      bug: {
        subject: 'Bug Report - Survivor Pool App',
        body: `Hi Survivor Pool Team,

I'd like to report a bug I encountered in the app.

**Device Info:**
- Username: ${username}
- Device: [Your device model]
- App Version: 1.0.0

**Bug Description:**
[Please describe what happened]

**Steps to Reproduce:**
1. [First step]
2. [Second step]
3. [What you expected vs what happened]

**Screenshots:**
[Attach any relevant screenshots]

Thanks for your help!`,
      },
      feature: {
        subject: 'Feature Request - Survivor Pool App',
        body: `Hi Survivor Pool Team,

I have a feature suggestion for the app!

**Username:** ${username}

**Feature Description:**
[Describe the feature you'd like to see]

**Why it would be useful:**
[Explain how this would improve your experience]

**Additional Details:**
[Any other information]

Thanks for considering!`,
      },
      general: {
        subject: 'Support Request - Survivor Pool App',
        body: `Hi Survivor Pool Team,

I have a question/issue regarding the app.

**Username:** ${username}

**My Question/Issue:**
[Please describe your inquiry]

Thanks!`,
      },
    };

    const template = templates[type];
    const mailtoUrl = `mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(template.subject)}&body=${encodeURIComponent(template.body)}`;
    
    Linking.openURL(mailtoUrl).catch(() => {
      Alert.alert('Error', 'Unable to open email client. Please email us directly at ' + SUPPORT_EMAIL);
    });
  };

  const menuItems = [
    {
      title: 'Account',
      items: [
        { 
          icon: 'person-outline', 
          label: 'Edit Profile', 
          onPress: () => navigation.navigate('EditProfile', { userId }),
        },
        { 
          icon: 'lock-closed-outline', 
          label: 'Change Password', 
          onPress: () => navigation.navigate('ChangePassword', { userId }),
        },
        { icon: 'mail-outline', label: 'Email Preferences', onPress: () => {} },
      ],
    },
    {
      title: 'Notifications',
      items: [
        { 
          icon: 'notifications-outline', 
          label: 'Push Notifications', 
          toggle: true,
          value: notificationsEnabled,
          onToggle: setNotificationsEnabled,
        },
        { 
          icon: 'alarm-outline', 
          label: 'Deadline Reminders', 
          toggle: true,
          value: deadlineReminders,
          onToggle: setDeadlineReminders,
          subtitle: 'Get reminded before pick deadlines',
        },
        { 
          icon: 'football-outline', 
          label: 'Match Results', 
          toggle: true,
          value: resultNotifications,
          onToggle: setResultNotifications,
          subtitle: 'Notifications when your picks resolve',
        },
      ],
    },
    {
      title: 'Appearance',
      items: [
        { 
          icon: isDark ? 'moon' : 'sunny', 
          label: 'Dark Mode', 
          toggle: true,
          value: isDark,
          onToggle: toggleTheme,
        },
      ],
    },
    {
      title: 'Support',
      items: [
        { 
          icon: 'chatbubble-outline', 
          label: 'Contact Support', 
          subtitle: 'Report bugs or request features',
          onPress: handleContactSupport,
        },
        { 
          icon: 'help-circle-outline', 
          label: 'Help & FAQ', 
          onPress: () => Alert.alert(
            'Help & FAQ',
            'Frequently Asked Questions\n\n' +
            '• How do I make a pick?\nGo to your pool and tap "Make Pick" to select a team.\n\n' +
            '• What happens if my team loses?\nYou lose one life. When all lives are gone, you\'re eliminated.\n\n' +
            '• Can I change my pick?\nYes, until the deadline for that gameweek.\n\n' +
            '• How do I invite friends?\nShare your pool\'s session code with them.\n\n' +
            'For more help, contact support!',
            [{ text: 'OK' }]
          ),
        },
        { 
          icon: 'document-text-outline', 
          label: 'Terms of Service', 
          onPress: () => Alert.alert(
            'Terms of Service',
            'By using Survivor Pool, you agree to:\n\n' +
            '• Use the app for entertainment purposes only\n' +
            '• Not engage in any fraudulent activity\n' +
            '• Respect other users in your pools\n' +
            '• Accept that picks are final after deadlines\n\n' +
            'Full terms available at survivorpool.app/terms (coming soon)',
            [{ text: 'OK' }]
          ),
        },
        { 
          icon: 'shield-checkmark-outline', 
          label: 'Privacy Policy', 
          onPress: () => Alert.alert(
            'Privacy Policy',
            'Your privacy matters to us.\n\n' +
            '• We collect only essential data (email, username)\n' +
            '• Your data is never sold to third parties\n' +
            '• Pick history is stored securely\n' +
            '• You can request data deletion anytime\n\n' +
            'Full policy at survivorpool.app/privacy (coming soon)\n\n' +
            'Questions? Email: ' + SUPPORT_EMAIL,
            [{ text: 'OK' }]
          ),
        },
      ],
    },
  ];

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Profile</Text>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.contentContainer}>
        {/* User Card */}
        <View style={styles.userCard}>
          <View style={styles.avatarLarge}>
            <Text style={styles.avatarLargeText}>
              {(user?.firstName || user?.userName || 'U')[0].toUpperCase()}
            </Text>
          </View>
          <View style={styles.userInfo}>
            <Text style={styles.userName}>{user?.firstName || user?.userName || 'Player'}</Text>
            <Text style={styles.userEmail}>{user?.email || 'email@example.com'}</Text>
          </View>
          <TouchableOpacity style={styles.editButton}>
            <Ionicons name="pencil" size={18} color={colors.accent} />
          </TouchableOpacity>
        </View>

        {/* Stats Summary */}
        <View style={styles.statsCard}>
          <Text style={styles.statsTitle}>Season Stats</Text>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{stats.totalPools}</Text>
              <Text style={styles.statLabel}>Pools</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{stats.totalPicks}</Text>
              <Text style={styles.statLabel}>Picks</Text>
            </View>
            <View style={styles.statDivider} />
            <View style={styles.statItem}>
              <Text style={styles.statValue}>{stats.winRate}%</Text>
              <Text style={styles.statLabel}>Win Rate</Text>
            </View>
          </View>
        </View>

        {/* Menu Sections */}
        {menuItems.map((section, sectionIndex) => (
          <View key={sectionIndex} style={styles.menuSection}>
            <Text style={styles.menuSectionTitle}>{section.title}</Text>
            <View style={styles.menuCard}>
              {section.items.map((item, itemIndex) => (
                <TouchableOpacity
                  key={itemIndex}
                  style={[
                    styles.menuItem,
                    itemIndex < section.items.length - 1 && styles.menuItemBorder,
                  ]}
                  onPress={item.toggle ? undefined : item.onPress}
                  activeOpacity={item.toggle ? 1 : 0.7}
                >
                  <View style={styles.menuItemLeft}>
                    <View style={styles.menuIconContainer}>
                      <Ionicons name={item.icon} size={20} color={colors.accent} />
                    </View>
                    <View style={styles.menuItemContent}>
                      <Text style={styles.menuItemLabel}>{item.label}</Text>
                      {item.subtitle && (
                        <Text style={styles.menuItemSubtitle}>{item.subtitle}</Text>
                      )}
                    </View>
                  </View>
                  {item.toggle ? (
                    <Switch
                      value={item.value}
                      onValueChange={item.onToggle}
                      trackColor={{ false: colors.border, true: colors.accent + '60' }}
                      thumbColor={item.value ? colors.accent : colors.textMuted}
                    />
                  ) : (
                    <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                  )}
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
          <Ionicons name="log-out-outline" size={20} color={colors.error} />
          <Text style={styles.logoutText}>Log Out</Text>
        </TouchableOpacity>

        {/* App Version */}
        <Text style={styles.versionText}>Survivor Pool v1.0.0</Text>

        {/* Bottom spacing */}
        <View style={{ height: 100 }} />
      </ScrollView>
    </View>
  );
}
