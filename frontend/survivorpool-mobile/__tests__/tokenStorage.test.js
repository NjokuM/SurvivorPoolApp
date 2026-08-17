import AsyncStorage from '@react-native-async-storage/async-storage';
import {
  storeTokens,
  getAccessToken,
  getRefreshToken,
  storeUser,
  getStoredUser,
  clearAuth,
} from '../src/utils/tokenStorage';

beforeEach(() => {
  jest.clearAllMocks();
  AsyncStorage.clear();
});

describe('tokenStorage', () => {
  // ── storeTokens / getAccessToken / getRefreshToken ──
  describe('storeTokens + getAccessToken + getRefreshToken', () => {
    it('stores and retrieves access token', async () => {
      await storeTokens('access_abc', 'refresh_xyz');
      const token = await getAccessToken();
      expect(token).toBe('access_abc');
    });

    it('stores and retrieves refresh token', async () => {
      await storeTokens('access_abc', 'refresh_xyz');
      const token = await getRefreshToken();
      expect(token).toBe('refresh_xyz');
    });

    it('overwrites previous tokens', async () => {
      await storeTokens('old_access', 'old_refresh');
      await storeTokens('new_access', 'new_refresh');
      expect(await getAccessToken()).toBe('new_access');
      expect(await getRefreshToken()).toBe('new_refresh');
    });
  });

  // ── storeUser / getStoredUser ──
  describe('storeUser + getStoredUser', () => {
    it('stores and retrieves user object', async () => {
      const user = { id: 1, email: 'test@example.com' };
      await storeUser(user);
      const stored = await getStoredUser();
      expect(stored).toEqual(user);
    });

    it('returns null when no user stored', async () => {
      const stored = await getStoredUser();
      expect(stored).toBeNull();
    });
  });

  // ── clearAuth ──
  describe('clearAuth', () => {
    it('clears tokens and user data', async () => {
      await storeTokens('access', 'refresh');
      await storeUser({ id: 1 });

      await clearAuth();

      expect(await getAccessToken()).toBeNull();
      expect(await getRefreshToken()).toBeNull();
      expect(await getStoredUser()).toBeNull();
    });

    it('does not throw when nothing is stored', async () => {
      await expect(clearAuth()).resolves.not.toThrow();
    });
  });
});
