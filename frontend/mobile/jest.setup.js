/* eslint-disable no-undef */

// Mock NativeWind and CSS interop early to prevent loading issues
jest.mock('nativewind', () => ({}));
jest.mock('nativewind/jsx-runtime', () => ({}));
jest.mock('react-native-css-interop', () => ({}));

// Mock all the CSS interop internal modules
jest.mock('react-native-css-interop/src/runtime/native/appearance-observables', () => ({
  resetAppearanceListeners: jest.fn(),
}));
jest.mock('react-native-css-interop/src/runtime/native/api', () => ({}));
jest.mock('react-native-css-interop/src/runtime/api.native', () => ({}));
jest.mock('react-native-css-interop/src/runtime/wrap-jsx', () => ({}));
jest.mock('react-native-css-interop/src/runtime/jsx-runtime', () => ({}));

// Mock React Native completely
jest.mock('react-native', () => {
  return {
    // Basic components
    View: 'View',
    Text: 'Text',
    TextInput: 'TextInput',
    TouchableOpacity: 'TouchableOpacity',
    Pressable: 'Pressable',
    Button: 'Button',
    ScrollView: 'ScrollView',
    FlatList: 'FlatList',
    Image: 'Image',
    ActivityIndicator: 'ActivityIndicator',
    
    // StyleSheet
    StyleSheet: {
      create: jest.fn(styles => styles),
      flatten: jest.fn(styles => styles),
      absoluteFill: {},
      hairlineWidth: 1,
    },
    
    // Dimensions
    Dimensions: {
      get: jest.fn(() => ({
        width: 390,
        height: 844,
        scale: 3,
        fontScale: 1,
      })),
      set: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
    
    // Platform
    Platform: {
      OS: 'ios',
      select: jest.fn((obj) => obj.ios || obj.default),
    },
    
    // Alert
    Alert: {
      alert: jest.fn(),
    },
    
    // PixelRatio
    PixelRatio: {
      get: jest.fn(() => 3),
      getFontScale: jest.fn(() => 1),
    },
    
    // Appearance
    Appearance: {
      getColorScheme: jest.fn(() => 'light'),
      addChangeListener: jest.fn(),
      removeChangeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
    },
    
    // Animated
    Animated: {
      createAnimatedComponent: jest.fn((component) => component),
      Value: jest.fn(() => ({
        setValue: jest.fn(),
        interpolate: jest.fn(),
        addListener: jest.fn(),
        removeListener: jest.fn(),
      })),
      timing: jest.fn(() => ({
        start: jest.fn(),
        stop: jest.fn(),
      })),
      spring: jest.fn(() => ({
        start: jest.fn(),
        stop: jest.fn(),
      })),
      View: 'Animated.View',
      Text: 'Animated.Text',
    },
    
    // Native modules
    NativeModules: {
      UIManager: {
        getConstants: jest.fn(() => ({})),
      },
    },
  };
});

// Mock react-native-gesture-handler
jest.mock('react-native-gesture-handler', () => ({
  Swipeable: 'Swipeable',
  DrawerLayout: 'DrawerLayout',
  State: {},
  ScrollView: 'ScrollView',
  Slider: 'Slider',
  Switch: 'Switch',
  TextInput: 'TextInput',
  ToolbarAndroid: 'ToolbarAndroid',
  ViewPagerAndroid: 'ViewPagerAndroid',
  DrawerLayoutAndroid: 'DrawerLayoutAndroid',
  WebView: 'WebView',
  NativeViewGestureHandler: 'NativeViewGestureHandler',
  TapGestureHandler: 'TapGestureHandler',
  FlingGestureHandler: 'FlingGestureHandler',
  ForceTouchGestureHandler: 'ForceTouchGestureHandler',
  LongPressGestureHandler: 'LongPressGestureHandler',
  PanGestureHandler: 'PanGestureHandler',
  PinchGestureHandler: 'PinchGestureHandler',
  RotationGestureHandler: 'RotationGestureHandler',
  RawButton: 'RawButton',
  BaseButton: 'BaseButton',
  RectButton: 'RectButton',
  BorderlessButton: 'BorderlessButton',
  FlatList: 'FlatList',
  gestureHandlerRootHOC: jest.fn(component => component),
  Directions: {},
}));

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  return {
    createAnimatedComponent: jest.fn((component) => component),
    useSharedValue: jest.fn((initialValue) => ({ value: initialValue })),
    useAnimatedStyle: jest.fn(() => ({})),
    withTiming: jest.fn((value) => value),
    withSpring: jest.fn((value) => value),
    runOnJS: jest.fn((fn) => fn),
    default: {
      createAnimatedComponent: jest.fn((component) => component),
    },
  };
});

// Mock react-native-safe-area-context
jest.mock('react-native-safe-area-context', () => {
  const inset = { top: 0, right: 0, bottom: 0, left: 0 };
  return {
    SafeAreaProvider: ({ children }) => children,
    SafeAreaConsumer: ({ children }) => children,
    useSafeAreaInsets: () => inset,
    useSafeAreaFrame: () => ({ x: 0, y: 0, width: 390, height: 844 }),
    initialWindowMetrics: {
      frame: { x: 0, y: 0, width: 390, height: 844 },
      insets: inset,
    },
  };
});

// Mock react-native-paper
jest.mock('react-native-paper', () => ({
  Button: 'Button',
  Card: 'Card',
  Text: 'Text',
  Provider: ({ children }) => children,
  DefaultTheme: {},
}));

// Mock Expo modules
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

jest.mock('expo-web-browser', () => ({
  openBrowserAsync: jest.fn(),
}));

jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    back: jest.fn(),
    replace: jest.fn(),
  }),
  Link: 'Link',
  Redirect: 'Redirect',
}));

// Mock global fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({}),
    ok: true,
    status: 200,
  })
);

// Mock console methods for testing
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Setup React for JSX (moved outside of mock factory)
// This will be available globally for tests