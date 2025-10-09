module.exports = {
  preset: 'jest-expo',
  setupFiles: ['./jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg|@react-native|@react-native-firebase|@react-native-masked-view|@react-native-picker|@react-native-reanimated|@react-native-safe-area-context|@react-native-screens|@react-native-vector-icons|@react-native-community|@react-native-async-storage|@react-native-clipboard|@react-native-cookies|@react-native-device-info|@react-native-fs|@react-native-google-signin|@react-native-image-picker|@react-native-netinfo|@react-native-picker|@react-native-push-notification|@react-native-segmented-control|@react-native-share|@react-native-voice|@react-native-webview|react-native-reanimated|react-native-safe-area-context|react-native-screens|react-native-svg|react-native-vector-icons|@react-native-masked-view/masked-view|@react-native-picker/picker|@react-native-reanimated|@react-native-safe-area-context|@react-native-screens|@react-native-vector-icons|@react-native-community/async-storage|@react-native-community/clipboard|@react-native-community/cookies|@react-native-community/netinfo|@react-native-community/picker|@react-native-community/push-notification-ios|@react-native-community/segmented-control|@react-native-community/share|@react-native-community/voice|react-native-webview)'
  ],
  collectCoverage: true,
  collectCoverageFrom: [
    '**/*.{js,jsx,ts,tsx}',
    '!**/node_modules/**',
    '!**/vendor/**',
    '!**/coverage/**',
    '!**/build/**',
    '!**/dist/**',
    '!**/assets/**',
    '!**/App.tsx',
    '!**/index.js',
    '!**/babel.config.js',
    '!**/jest.config.js',
    '!**/metro.config.js',
    '!**/tailwind.config.js'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
};
