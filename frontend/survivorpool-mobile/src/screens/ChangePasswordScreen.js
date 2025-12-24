import { View, Text, TextInput, TouchableOpacity, ScrollView, StatusBar, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { useTheme } from '../theme/colors';
import { createStyles } from './styles/ChangePasswordScreen.styles';

export default function ChangePasswordScreen({ route, navigation }) {
  const { userId } = route.params;
  const { colors } = useTheme();
  const styles = createStyles(colors);
  
  const [saving, setSaving] = useState(false);
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  // Password visibility toggles
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);

  const validatePassword = (password) => {
    const checks = {
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /[0-9]/.test(password),
    };
    return checks;
  };

  const passwordChecks = validatePassword(newPassword);
  const isPasswordValid = Object.values(passwordChecks).every(Boolean);

  const handleChangePassword = async () => {
    // Validation
    if (!currentPassword) {
      Alert.alert('Error', 'Please enter your current password');
      return;
    }
    if (!newPassword) {
      Alert.alert('Error', 'Please enter a new password');
      return;
    }
    if (!isPasswordValid) {
      Alert.alert('Error', 'New password does not meet requirements');
      return;
    }
    if (newPassword !== confirmPassword) {
      Alert.alert('Error', 'New passwords do not match');
      return;
    }
    if (currentPassword === newPassword) {
      Alert.alert('Error', 'New password must be different from current password');
      return;
    }

    setSaving(true);
    try {
      // TODO: Replace with actual API call when backend is ready
      // await apiService.changePassword(userId, {
      //   current_password: currentPassword,
      //   new_password: newPassword,
      // });

      // Mock success for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      Alert.alert(
        'Success',
        'Your password has been changed successfully!',
        [{ text: 'OK', onPress: () => navigation.goBack() }]
      );
    } catch (error) {
      Alert.alert('Error', error.message || 'Failed to change password. Please check your current password.');
    } finally {
      setSaving(false);
    }
  };

  const canSubmit = currentPassword && newPassword && confirmPassword && isPasswordValid && newPassword === confirmPassword;

  return (
    <View style={styles.container}>
      <StatusBar barStyle={colors.statusBar} backgroundColor={colors.background} />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Change Password</Text>
        <View style={{ width: 40 }} />
      </View>

      <KeyboardAvoidingView 
        style={styles.keyboardView}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView 
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
          showsVerticalScrollIndicator={false}
        >
          {/* Security Icon */}
          <View style={styles.iconSection}>
            <View style={styles.iconContainer}>
              <Ionicons name="shield-checkmark" size={40} color={colors.accent} />
            </View>
            <Text style={styles.iconSubtitle}>
              Choose a strong password to protect your account
            </Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            {/* Current Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Current Password</Text>
              <View style={styles.passwordContainer}>
                <TextInput
                  style={styles.passwordInput}
                  placeholder="Enter current password"
                  placeholderTextColor={colors.placeholder}
                  value={currentPassword}
                  onChangeText={setCurrentPassword}
                  secureTextEntry={!showCurrent}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <TouchableOpacity 
                  style={styles.eyeButton}
                  onPress={() => setShowCurrent(!showCurrent)}
                >
                  <Ionicons 
                    name={showCurrent ? 'eye-off' : 'eye'} 
                    size={20} 
                    color={colors.textMuted} 
                  />
                </TouchableOpacity>
              </View>
            </View>

            {/* New Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>New Password</Text>
              <View style={styles.passwordContainer}>
                <TextInput
                  style={styles.passwordInput}
                  placeholder="Enter new password"
                  placeholderTextColor={colors.placeholder}
                  value={newPassword}
                  onChangeText={setNewPassword}
                  secureTextEntry={!showNew}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <TouchableOpacity 
                  style={styles.eyeButton}
                  onPress={() => setShowNew(!showNew)}
                >
                  <Ionicons 
                    name={showNew ? 'eye-off' : 'eye'} 
                    size={20} 
                    color={colors.textMuted} 
                  />
                </TouchableOpacity>
              </View>
            </View>

            {/* Password Requirements */}
            {newPassword.length > 0 && (
              <View style={styles.requirementsCard}>
                <Text style={styles.requirementsTitle}>Password Requirements</Text>
                <View style={styles.requirementItem}>
                  <Ionicons 
                    name={passwordChecks.length ? 'checkmark-circle' : 'ellipse-outline'} 
                    size={18} 
                    color={passwordChecks.length ? colors.success : colors.textMuted} 
                  />
                  <Text style={[
                    styles.requirementText,
                    passwordChecks.length && styles.requirementMet
                  ]}>
                    At least 8 characters
                  </Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons 
                    name={passwordChecks.uppercase ? 'checkmark-circle' : 'ellipse-outline'} 
                    size={18} 
                    color={passwordChecks.uppercase ? colors.success : colors.textMuted} 
                  />
                  <Text style={[
                    styles.requirementText,
                    passwordChecks.uppercase && styles.requirementMet
                  ]}>
                    One uppercase letter
                  </Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons 
                    name={passwordChecks.lowercase ? 'checkmark-circle' : 'ellipse-outline'} 
                    size={18} 
                    color={passwordChecks.lowercase ? colors.success : colors.textMuted} 
                  />
                  <Text style={[
                    styles.requirementText,
                    passwordChecks.lowercase && styles.requirementMet
                  ]}>
                    One lowercase letter
                  </Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons 
                    name={passwordChecks.number ? 'checkmark-circle' : 'ellipse-outline'} 
                    size={18} 
                    color={passwordChecks.number ? colors.success : colors.textMuted} 
                  />
                  <Text style={[
                    styles.requirementText,
                    passwordChecks.number && styles.requirementMet
                  ]}>
                    One number
                  </Text>
                </View>
              </View>
            )}

            {/* Confirm Password */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Confirm New Password</Text>
              <View style={styles.passwordContainer}>
                <TextInput
                  style={styles.passwordInput}
                  placeholder="Confirm new password"
                  placeholderTextColor={colors.placeholder}
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry={!showConfirm}
                  autoCapitalize="none"
                  autoCorrect={false}
                />
                <TouchableOpacity 
                  style={styles.eyeButton}
                  onPress={() => setShowConfirm(!showConfirm)}
                >
                  <Ionicons 
                    name={showConfirm ? 'eye-off' : 'eye'} 
                    size={20} 
                    color={colors.textMuted} 
                  />
                </TouchableOpacity>
              </View>
              {confirmPassword.length > 0 && newPassword !== confirmPassword && (
                <Text style={styles.errorText}>Passwords do not match</Text>
              )}
              {confirmPassword.length > 0 && newPassword === confirmPassword && (
                <Text style={styles.successText}>Passwords match!</Text>
              )}
            </View>
          </View>

          {/* Submit Button */}
          <TouchableOpacity 
            style={[styles.submitButton, !canSubmit && styles.submitButtonDisabled]}
            onPress={handleChangePassword}
            disabled={!canSubmit || saving}
          >
            {saving ? (
              <ActivityIndicator size="small" color={colors.textOnAccent} />
            ) : (
              <Text style={styles.submitButtonText}>Change Password</Text>
            )}
          </TouchableOpacity>

          {/* Security Note */}
          <View style={styles.securityNote}>
            <Ionicons name="information-circle" size={18} color={colors.textMuted} />
            <Text style={styles.securityNoteText}>
              You'll be logged out of all other devices after changing your password.
            </Text>
          </View>

        </ScrollView>
      </KeyboardAvoidingView>
    </View>
  );
}
