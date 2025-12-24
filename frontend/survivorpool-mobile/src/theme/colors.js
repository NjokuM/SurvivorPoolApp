// Theme Colors - Supports Light and Dark modes
// Premier League inspired color palette

import { useColorScheme } from 'react-native';
import { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Dark Theme Colors
export const darkColors = {
  // Primary colors
  primary: '#37003c',
  primaryLight: '#5c2d6e',
  primaryDark: '#1a001d',
  
  // Accent colors
  accent: '#00ff85',
  accentDark: '#00cc6a',
  
  // Background colors
  background: '#0f0f23',
  backgroundLight: '#1a1a2e',
  backgroundCard: '#1a1a2e',
  surface: '#1a1a2e',
  
  // Text colors
  textPrimary: '#ffffff',
  textSecondary: 'rgba(255, 255, 255, 0.7)',
  textMuted: 'rgba(255, 255, 255, 0.5)',
  textDisabled: 'rgba(255, 255, 255, 0.3)',
  textOnAccent: '#0f0f23',
  
  // Status colors
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
  
  // Border colors
  border: 'rgba(255, 255, 255, 0.1)',
  borderLight: 'rgba(255, 255, 255, 0.15)',
  borderFocus: '#00ff85',
  
  // Input colors
  inputBackground: 'rgba(255, 255, 255, 0.05)',
  inputBackgroundFocus: 'rgba(0, 255, 133, 0.05)',
  placeholder: 'rgba(255, 255, 255, 0.3)',
  
  // Overlay colors
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.3)',
  
  // Lives/Hearts
  heart: '#e90052',
  heartEmpty: 'rgba(233, 0, 82, 0.3)',
  
  // Status bar
  statusBar: 'light-content',
};

// Light Theme Colors
export const lightColors = {
  // Primary colors
  primary: '#37003c',
  primaryLight: '#5a1a5e',
  primaryDark: '#1a001d',
  
  // Accent colors
  accent: '#00c853',
  accentLight: '#5efc82',
  accentDark: '#009624',
  
  // Secondary colors
  secondary: '#e90052',
  secondaryLight: '#ff3377',
  secondaryDark: '#b8003f',
  
  // Background colors
  background: '#f5f5f7',
  backgroundLight: '#ffffff',
  backgroundCard: '#ffffff',
  surface: '#ffffff',
  
  // Text colors
  textPrimary: '#1a1a2e',
  textSecondary: 'rgba(26, 26, 46, 0.7)',
  textMuted: 'rgba(26, 26, 46, 0.5)',
  textDisabled: 'rgba(26, 26, 46, 0.3)',
  textOnAccent: '#ffffff',
  
  // Status colors
  success: '#10b981',
  warning: '#f59e0b',
  error: '#ef4444',
  info: '#3b82f6',
  
  // Border colors
  border: 'rgba(0, 0, 0, 0.1)',
  borderLight: 'rgba(0, 0, 0, 0.08)',
  borderFocus: '#37003c',
  
  // Input colors
  inputBackground: 'rgba(0, 0, 0, 0.03)',
  inputBackgroundFocus: 'rgba(55, 0, 60, 0.05)',
  placeholder: 'rgba(26, 26, 46, 0.4)',
  
  // Overlay colors
  overlay: 'rgba(0, 0, 0, 0.5)',
  overlayLight: 'rgba(0, 0, 0, 0.2)',
  
  // Lives/Hearts
  heart: '#e90052',
  heartEmpty: 'rgba(233, 0, 82, 0.3)',
  
  // Status bar
  statusBar: 'dark-content',
};

// Legacy export for backwards compatibility
export const colors = lightColors;

// Theme Context
const ThemeContext = createContext({
  isDark: false,
  colors: lightColors,
  toggleTheme: () => {},
  setTheme: () => {},
});

export const useTheme = () => useContext(ThemeContext);

export const ThemeProvider = ({ children }) => {
  const systemColorScheme = useColorScheme();
  const [isDark, setIsDark] = useState(false); // Default to light
  const [isLoaded, setIsLoaded] = useState(false);

  // Load saved theme preference
  useEffect(() => {
    const loadTheme = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem('theme');
        if (savedTheme !== null) {
          setIsDark(savedTheme === 'dark');
        } else {
          // Use system preference if no saved preference
          setIsDark(systemColorScheme === 'dark');
        }
      } catch (e) {
        console.log('Error loading theme:', e);
      } finally {
        setIsLoaded(true);
      }
    };
    loadTheme();
  }, []);

  const toggleTheme = async () => {
    const newTheme = !isDark;
    setIsDark(newTheme);
    try {
      await AsyncStorage.setItem('theme', newTheme ? 'dark' : 'light');
    } catch (e) {
      console.log('Error saving theme:', e);
    }
  };

  const setTheme = async (theme) => {
    const dark = theme === 'dark';
    setIsDark(dark);
    try {
      await AsyncStorage.setItem('theme', theme);
    } catch (e) {
      console.log('Error saving theme:', e);
    }
  };

  const themeColors = isDark ? darkColors : lightColors;

  return (
    <ThemeContext.Provider value={{ isDark, colors: themeColors, toggleTheme, setTheme, isLoaded }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Shadow presets (theme-aware)
export const getShadows = (isDark) => ({
  small: {
    shadowColor: isDark ? '#000' : '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: isDark ? 0.2 : 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  medium: {
    shadowColor: isDark ? '#000' : '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: isDark ? 0.25 : 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  large: {
    shadowColor: isDark ? '#00ff85' : '#37003c',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: isDark ? 0.15 : 0.12,
    shadowRadius: 20,
    elevation: 8,
  },
  glow: {
    shadowColor: isDark ? '#00ff85' : '#37003c',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
});

// Legacy shadows export
export const shadows = getShadows(true);

// Border radius presets
export const borderRadius = {
  small: 8,
  medium: 12,
  large: 16,
  xl: 20,
  round: 9999,
};

// Spacing presets
export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  xxl: 24,
  xxxl: 32,
};

export default { colors, shadows, borderRadius, spacing };
