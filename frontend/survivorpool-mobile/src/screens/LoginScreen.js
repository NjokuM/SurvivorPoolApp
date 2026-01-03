import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
import { createStyles } from './styles/LoginScreen.styles';

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

            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}
