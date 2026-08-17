// Global test setup — mock AsyncStorage for all tests
jest.mock('@react-native-async-storage/async-storage', () => {
  const store = {};
  return {
    setItem: jest.fn((key, value) => {
      store[key] = value;
      return Promise.resolve();
    }),
    getItem: jest.fn((key) => Promise.resolve(store[key] || null)),
    removeItem: jest.fn((key) => {
      delete store[key];
      return Promise.resolve();
    }),
    multiSet: jest.fn((pairs) => {
      pairs.forEach(([key, value]) => { store[key] = value; });
      return Promise.resolve();
    }),
    multiRemove: jest.fn((keys) => {
      keys.forEach((key) => { delete store[key]; });
      return Promise.resolve();
    }),
    clear: jest.fn(() => {
      Object.keys(store).forEach((key) => delete store[key]);
      return Promise.resolve();
    }),
    __getStore: () => store,
  };
});

// Mock expo-constants
jest.mock('expo-constants', () => ({
  expoConfig: { extra: {} },
}));
