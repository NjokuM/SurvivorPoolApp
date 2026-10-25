import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator, StatusBar, KeyboardAvoidingView, Platform } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import apiService from '../api/apiService';
// Same card layout as the login screen this is reached from.
import { createStyles } from './styles/LoginScreen.styles';

const MIN_PASSWORD_LENGTH = 8;

export default function ForgotPasswordScreen({ route, navigation }) {
  const { colors } = useTheme();
  const styles = createStyles(colors);

  const [step, setStep] = useState('email'); // 'email' -> 'reset'
  const [email, setEmail] = useState(route.params?.email || '');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');

  const sendCode = async () => {
    setError('');
    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }
    setIsLoading(true);
    try {
      await apiService.forgotPassword(email);
      setInfo(`If an account exists for ${email.trim()}, we've emailed it a 6-digit code. It expires in 15 minutes.`);
      setStep('reset');
    } catch (err) {
      setError(err.message || 'Failed to send reset code');
    } finally {
      setIsLoading(false);
    }
  };

  const resetPassword = async () => {
    setError('');
    if (!/^\d{6}$/.test(code.trim())) {
      setError('Enter the 6-digit code from the email');
      return;
    }
    if (newPassword.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters`);
      return;
    }
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    setIsLoading(true);
    try {
      const result = await apiService.resetPassword(email, code, newPassword);
      navigation.reset({
        index: 0,
        routes: [{ name: 'Main', params: { userId: result.user.id } }],
      });
    } catch (err) {
      setError(err.message || 'Failed to reset password');
    } finally {
      setIsLoading(false);
    }
  };

  const renderInput = (label, value, onChange, props = {}) => (
    <View style={styles.inputGroup}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={styles.input}
        placeholderTextColor={colors.placeholder}
        value={value}
        onChangeText={onChange}
        autoCapitalize="none"
        autoCorrect={false}
        {...props}
      />
    </View>
  );

  return (
    <>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={{ flex: 1, backgroundColor: colors.background }}
      >
        <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
          <View style={styles.container}>
            <View style={styles.header}>
              <View style={styles.iconContainer}>
                <Ionicons name="key" size={36} color={colors.accent} />
              </View>
              <Text style={styles.mainTitle}>Reset Password</Text>
            </View>

            <View style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>
                  {step === 'email' ? 'Forgot your password?' : 'Enter your code'}
                </Text>
                <Text style={styles.cardDescription}>
                  {step === 'email' ? "We'll email you a code to reset it" : info}
                </Text>
              </View>

              <View style={styles.form}>
                {step === 'email' ? (
                  renderInput('Email', email, setEmail, {
                    placeholder: 'email@example.com',
                    keyboardType: 'email-address',
                  })
                ) : (
                  <>
                    {renderInput('Code', code, setCode, {
                      placeholder: '123456',
                      keyboardType: 'number-pad',
                      maxLength: 6,
                      textContentType: 'oneTimeCode',
                    })}
                    {renderInput('New Password', newPassword, setNewPassword, {
                      placeholder: '••••••••',
                      secureTextEntry: true,
                    })}
                    {renderInput('Confirm Password', confirmPassword, setConfirmPassword, {
                      placeholder: '••••••••',
                      secureTextEntry: true,
                    })}
                  </>
                )}

                {error ? (
                  <Text style={[styles.footerText, { color: colors.error, marginBottom: 12 }]}>{error}</Text>
                ) : null}

                <TouchableOpacity
                  style={[styles.button, isLoading && styles.buttonDisabled]}
                  onPress={step === 'email' ? sendCode : resetPassword}
                  disabled={isLoading}
                  activeOpacity={0.8}
                >
                  {isLoading ? (
                    <ActivityIndicator color={colors.textOnAccent} />
                  ) : (
                    <Text style={styles.buttonText}>
                      {step === 'email' ? 'Send Code' : 'Reset Password'}
                    </Text>
                  )}
                </TouchableOpacity>
              </View>

              <View style={styles.cardFooter}>
                {step === 'reset' && (
                  <Text style={[styles.linkText, { marginBottom: 12 }]} onPress={sendCode}>
                    Didn't get it? Send a new code
                  </Text>
                )}
                <Text style={styles.linkText} onPress={() => navigation.goBack()}>
                  Back to sign in
                </Text>
              </View>
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </>
  );
}
