import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';

// Show notifications as a banner + sound while the app is in the
// foreground too, not just when backgrounded.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

// Registers this device for push notifications and returns the Expo push
// token, or null if permission was denied / this is a simulator (push
// tokens don't work in the iOS Simulator or most Android emulators).
export async function registerForPushNotificationsAsync() {
  if (!Device.isDevice) {
    console.log('Push notifications require a physical device - skipping on simulator/emulator.');
    return null;
  }

  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  if (existingStatus !== 'granted') {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== 'granted') {
    console.log('Push notification permission was not granted.');
    return null;
  }

  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('default', {
      name: 'default',
      importance: Notifications.AndroidImportance.DEFAULT,
    });
  }

  try {
    const { data: token } = await Notifications.getExpoPushTokenAsync();
    return token;
  } catch (error) {
    console.error('Failed to get Expo push token:', error);
    return null;
  }
}
