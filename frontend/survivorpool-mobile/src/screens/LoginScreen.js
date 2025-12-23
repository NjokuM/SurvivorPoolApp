import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, KeyboardAvoidingView, Platform, StyleSheet } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [emailFocused, setEmailFocused] = useState(false);
  const [passwordFocused, setPasswordFocused] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      alert('Please enter both email and password');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiService.login(email, password);

      console.log("Response:", response);

      if (response.success) {
        navigation.reset({
          index: 0,
          routes: [{ name: 'Main', params: { userId: response.user.id } }],
        });
      } else {
        alert(response.message || "Invalid credentials");
      }
    } catch (error) {
      console.error("Login error:", error.message);
      alert("Login failed. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const { colors, isDark, toggleTheme } = useTheme();
  const styles = createStyles(colors);

  return (
    <>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      <KeyboardAvoidingView 
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1, backgroundColor: colors.background }}
      >
        <ScrollView 
          contentContainerStyle={styles.scrollContainer}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.container}>
            {/* Header with Trophy Icon */}
            <View style={styles.header}>
              <View style={styles.iconContainer}>
                <Ionicons name="football" size={36} color={colors.accent} />
              </View>
              <Text style={styles.mainTitle}>Survivor Pool</Text>
              <Text style={styles.subtitle}>Pick winners. Survive the season.</Text>
            </View>

            {/* Card Container */}
            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>Welcome Back</Text>
                <Text style={styles.cardDescription}>Sign in to continue your journey</Text>
              </View>

              {/* Form */}
              <View style={styles.form}>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Email</Text>
                  <TextInput
                    style={[styles.input, emailFocused && styles.inputFocused]}
                    placeholder="email@example.com"
                    placeholderTextColor={colors.placeholder}
                    value={email}
                    onChangeText={setEmail}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    onFocus={() => setEmailFocused(true)}
                    onBlur={() => setEmailFocused(false)}
                  />
                </View>

                <View style={styles.inputGroup}>
                  <View style={styles.labelRow}>
                    <Text style={styles.label}>Password</Text>
                    <TouchableOpacity onPress={() => {}}>
                      <Text style={styles.forgotPassword}>Forgot password?</Text>
                    </TouchableOpacity>
                  </View>
                  <TextInput
                    style={[styles.input, passwordFocused && styles.inputFocused]}
                    placeholder="••••••••"
                    placeholderTextColor={colors.placeholder}
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                    onFocus={() => setPasswordFocused(true)}
                    onBlur={() => setPasswordFocused(false)}
                  />
                </View>

                <TouchableOpacity 
                  style={[styles.button, isLoading && styles.buttonDisabled]} 
                  onPress={handleLogin}
                  disabled={isLoading}
                  activeOpacity={0.8}
                >
                  {isLoading ? (
                    <View style={styles.loadingContainer}>
                      <ActivityIndicator color={colors.textOnAccent} style={styles.spinner} />
                      <Text style={styles.buttonText}>Signing in...</Text>
                    </View>
                  ) : (
                    <Text style={styles.buttonText}>Sign In</Text>
                  )}
                </TouchableOpacity>
              </View>

              {/* Footer */}
              <View style={styles.cardFooter}>
                <Text style={styles.footerText}>
                  Don't have an account?{' '}
                  <Text 
                    style={styles.linkText} 
                    onPress={() => navigation.navigate('Signup')}
                  >
                    Sign up
                  </Text>
                </Text>
              </View>
            </View>

            {/* Theme Toggle & Demo Credentials */}
            <View style={styles.bottomSection}>
              <TouchableOpacity style={styles.themeToggle} onPress={toggleTheme}>
                <Ionicons 
                  name={isDark ? 'sunny' : 'moon'} 
                  size={20} 
                  color={colors.accent} 
                />
                <Text style={styles.themeToggleText}>
                  {isDark ? 'Light Mode' : 'Dark Mode'}
                </Text>
              </TouchableOpacity>

              <View style={styles.demoContainer}>
                <Text style={styles.demoTitle}>Demo Credentials</Text>
                <Text style={styles.demoText}>Email: user1@example.com</Text>
                <Text style={styles.demoText}>Password: password123</Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}

// Dynamic styles based on theme
const createStyles = (colors) => StyleSheet.create({
  scrollContainer: {
    flexGrow: 1,
    backgroundColor: colors.background,
  },
  container: {
    flex: 1,
    justifyContent: 'center',
    padding: 20,
    paddingVertical: 60,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  iconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: colors.primary + '30',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 2,
    borderColor: colors.accent,
  },
  mainTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: colors.textPrimary,
    marginBottom: 8,
    letterSpacing: 0.5,
  },
  subtitle: {
    fontSize: 15,
    color: colors.textMuted,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 20,
    padding: 28,
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 20,
    elevation: 8,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cardHeader: {
    marginBottom: 28,
    alignItems: 'center',
  },
  cardTitle: {
    fontSize: 26,
    fontWeight: '700',
    color: colors.textPrimary,
    marginBottom: 8,
  },
  cardDescription: {
    fontSize: 14,
    color: colors.textMuted,
    textAlign: 'center',
  },
  form: {
    gap: 16,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 13,
    fontWeight: '600',
    color: colors.textSecondary,
    marginBottom: 10,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  forgotPassword: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: '600',
  },
  input: {
    height: 52,
    borderColor: colors.borderLight,
    borderWidth: 1.5,
    borderRadius: 12,
    paddingHorizontal: 16,
    fontSize: 16,
    color: colors.textPrimary,
    backgroundColor: colors.inputBackground,
  },
  inputFocused: {
    borderColor: colors.borderFocus,
    backgroundColor: colors.inputBackgroundFocus,
  },
  button: {
    backgroundColor: colors.accent,
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 12,
    shadowColor: colors.accent,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: colors.textOnAccent,
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  spinner: {
    marginRight: 10,
  },
  cardFooter: {
    marginTop: 28,
    alignItems: 'center',
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  footerText: {
    fontSize: 14,
    color: colors.textMuted,
  },
  linkText: {
    color: colors.accent,
    fontWeight: '700',
  },
  bottomSection: {
    marginTop: 32,
    alignItems: 'center',
  },
  themeToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    marginBottom: 16,
  },
  themeToggleText: {
    marginLeft: 8,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textPrimary,
  },
  demoContainer: {
    alignItems: 'center',
    backgroundColor: colors.primary + '30',
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.primary + '50',
  },
  demoTitle: {
    fontSize: 12,
    color: colors.accent,
    fontWeight: '600',
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  demoText: {
    fontSize: 13,
    color: colors.textSecondary,
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
  },
});
