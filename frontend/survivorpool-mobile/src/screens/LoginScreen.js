import { View, Text, TextInput, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { useState } from 'react';
import { Ionicons } from '@expo/vector-icons';
import { styles } from './styles/LoginScreen.styles';
import API from '../api/api';

export default function LoginScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) {
      return;
    }

    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("email", email);
      formData.append("password", password);

      const res = await API.post("/login", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      console.log("Response:", res.data);

      if (res.data.success) {
        navigation.reset({
          index: 0,
          routes: [{ name: 'Home', params: { userId: res.data.user.id } }],
        });
      } else {
        alert(res.data.message || "Invalid credentials");
      }
    } catch (error) {
      console.error("❌ Login error:", error.response?.data || error.message);
      alert("Login failed or network error.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.scrollContainer}>
      <View style={styles.container}>
        {/* Header with Trophy Icon */}
        <View style={styles.header}>
          <View style={styles.iconContainer}>
            <Ionicons name="trophy" size={40} color="#37003c" />
          </View>
          <Text style={styles.mainTitle}>Football Survivor League</Text>
          <Text style={styles.subtitle}>Sign in to access your leagues</Text>
        </View>

        {/* Card Container */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Sign In</Text>
            <Text style={styles.cardDescription}>Enter your credentials to access your account</Text>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email</Text>
              <TextInput
                style={styles.input}
                placeholder="email@example.com"
                placeholderTextColor="#999"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
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
                style={styles.input}
                placeholder="••••••••"
                placeholderTextColor="#999"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>

            <TouchableOpacity 
              style={[styles.button, isLoading && styles.buttonDisabled]} 
              onPress={handleLogin}
              disabled={isLoading}
            >
              {isLoading ? (
                <View style={styles.loadingContainer}>
                  <ActivityIndicator color="#fff" style={styles.spinner} />
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

        {/* Demo Credentials */}
        <View style={styles.demoContainer}>
          <Text style={styles.demoText}>For demo purposes you can use:</Text>
          <Text style={styles.demoText}>Email: user1@example.com</Text>
          <Text style={styles.demoText}>Password: password123</Text>
        </View>
      </View>
    </ScrollView>
  );
}
