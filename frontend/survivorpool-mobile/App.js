import { useEffect, useState } from 'react';
import { View, ActivityIndicator } from 'react-native';
import { NavigationContainer, createNavigationContainerRef } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import Toast from 'react-native-toast-message';
import { GoogleSignin } from '@react-native-google-signin/google-signin';
import { AppProvider } from './src/context/AppContext';
import { ThemeProvider, useTheme } from './src/theme/colors';
import apiService from './src/api/apiService';
import { authEvents } from './src/api/api';
import { GOOGLE_WEB_CLIENT_ID } from './src/config/google';
import LoginScreen from './src/screens/LoginScreen';
import SignupScreen from './src/screens/SignupScreen';
import MyPoolsScreen from './src/screens/MyPoolsScreen';
import PoolDetailScreen from './src/screens/PoolDetailScreen';
import JoinCreatePoolScreen from './src/screens/JoinCreatePoolScreen';
import ProfileScreen from './src/screens/ProfileScreen';
import EditProfileScreen from './src/screens/EditProfileScreen';
import ChangePasswordScreen from './src/screens/ChangePasswordScreen';

const Stack = createNativeStackNavigator();
const Tab = createBottomTabNavigator();
const navigationRef = createNavigationContainerRef();

GoogleSignin.configure({ webClientId: GOOGLE_WEB_CLIENT_ID });

// If a refresh attempt fails (refresh token expired/invalid), bounce the
// user back to Login from wherever they are in the app.
authEvents.onSessionExpired = () => {
  if (navigationRef.isReady()) {
    navigationRef.reset({ index: 0, routes: [{ name: 'Login' }] });
  }
};

// Bottom Tab Navigator (Main App after login)
function MainTabs({ route }) {
  const { userId } = route.params;
  const { colors } = useTheme();
  
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          borderTopWidth: 1,
          paddingTop: 8,
          paddingBottom: 28,
          height: 80,
        },
        tabBarActiveTintColor: colors.accent,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 4,
        },
        tabBarIcon: ({ focused, color, size }) => {
          let iconName;
          if (route.name === 'MyPools') {
            iconName = focused ? 'home' : 'home-outline';
          } else if (route.name === 'JoinCreate') {
            iconName = focused ? 'add-circle' : 'add-circle-outline';
          } else if (route.name === 'Profile') {
            iconName = focused ? 'person' : 'person-outline';
          }
          return <Ionicons name={iconName} size={24} color={color} />;
        },
      })}
    >
      <Tab.Screen 
        name="MyPools" 
        component={MyPoolsScreen}
        initialParams={{ userId }}
        options={{ tabBarLabel: 'My Pools' }}
      />
      <Tab.Screen 
        name="JoinCreate" 
        component={JoinCreatePoolScreen}
        initialParams={{ userId }}
        options={{ tabBarLabel: 'Join/Create' }}
      />
      <Tab.Screen 
        name="Profile" 
        component={ProfileScreen}
        initialParams={{ userId }}
        options={{ tabBarLabel: 'Profile' }}
      />
    </Tab.Navigator>
  );
}

function AppNavigator({ initialRouteName, initialMainParams }) {
  const { colors } = useTheme();

  return (
    <NavigationContainer ref={navigationRef}>
      <Stack.Navigator
        initialRouteName={initialRouteName}
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: colors.background },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="Login" component={LoginScreen} />
        <Stack.Screen name="Signup" component={SignupScreen} />
        <Stack.Screen name="Main" component={MainTabs} initialParams={initialMainParams} />
        <Stack.Screen name="PoolDetail" component={PoolDetailScreen} />
        <Stack.Screen name="EditProfile" component={EditProfileScreen} />
        <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

// Simple full-screen spinner shown while we check for a persisted session.
function SplashLoader() {
  const { colors } = useTheme();
  return (
    <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.background }}>
      <ActivityIndicator size="large" color={colors.accent} />
    </View>
  );
}

export default function App() {
  const [isReady, setIsReady] = useState(false);
  const [initialRouteName, setInitialRouteName] = useState('Login');
  const [initialMainParams, setInitialMainParams] = useState(undefined);

  useEffect(() => {
    let isMounted = true;
    (async () => {
      // Silently resume a persisted session (season-long refresh token) so
      // users land straight in the app instead of re-entering credentials.
      const user = await apiService.restoreSession();
      if (isMounted && user) {
        setInitialRouteName('Main');
        setInitialMainParams({ userId: user.id });
      }
      if (isMounted) setIsReady(true);
    })();
    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <ThemeProvider>
      <AppProvider>
        {isReady ? (
          <AppNavigator initialRouteName={initialRouteName} initialMainParams={initialMainParams} />
        ) : (
          <SplashLoader />
        )}
        <Toast />
      </AppProvider>
    </ThemeProvider>
  );
}