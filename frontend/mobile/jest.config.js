module.exports = {
  preset: 'react-native',
  setupFilesAfterEnv: ['./jest.setup.js'],
  testEnvironment: 'node',
  transform: {
    '^.+\\.(js|jsx|ts|tsx)$': 'babel-jest',
  },
  transformIgnorePatterns: [
    'node_modules/(?!(react-native|@react-native|@react-native-community|expo|@expo|@unimodules|react-navigation|@react-navigation|@testing-library/react-native|react-redux|expo-modules-core|@expo/vector-icons|react-native-paper|react-native-reanimated|react-native-gesture-handler|react-native-safe-area-context)/)'
  ],
  collectCoverage: false,
  coverageThreshold: {
    global: {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0
    }
  }
};
