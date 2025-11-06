# Synapse Mobile App

A React Native mobile application built with Expo and React Navigation for capturing and processing web content, videos, and audio files.

## Features

- **Tab Navigation**: Home and Explore tabs for easy navigation
- **Content Capture**: Capture web pages, videos, audio files, and voice memos
- **Modal Support**: Modal screens for additional functionality
- **Cross-Platform**: Works on iOS, Android, and Web
- **TypeScript**: Full TypeScript support for type safety
- **Testing**: Comprehensive test suite with Jest and React Native Testing Library

## Tech Stack

- **React Native**: 0.81.4
- **Expo**: ~54.0.13
- **React Navigation**: v7 (Native Stack + Bottom Tabs)
- **TypeScript**: ~5.9.2
- **Jest**: Testing framework
- **React Native Testing Library**: Component testing

## Project Structure

```
frontend/mobile/
├── App.tsx                 # Main app component with navigation
├── index.js               # App entry point
├── screens/               # Screen components
│   ├── HomeScreen.tsx     # Home tab screen
│   ├── ExploreScreen.tsx  # Explore tab screen
│   ├── CaptureScreen.tsx  # Content capture screen
│   └── ModalScreen.tsx    # Modal screen
├── __tests__/             # Test files
├── hooks/                 # Custom hooks
├── constants/             # App constants
├── assets/               # Images and fonts
└── package.json          # Dependencies and scripts
```

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- Expo CLI (`npm install -g @expo/cli`)

### Installation

1. Clone the repository and navigate to the mobile app directory:
   ```bash
   cd frontend/mobile
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

4. Run on specific platforms:
   ```bash
   npm run web      # Web browser
   npm run ios      # iOS simulator
   npm run android  # Android emulator
   ```

## Available Scripts

- `npm start` - Start Expo development server
- `npm run web` - Run on web browser
- `npm run ios` - Run on iOS simulator
- `npm run android` - Run on Android emulator
- `npm test` - Run tests
- `npm run test:watch` - Run tests in watch mode
- `npm run lint` - Run ESLint

## Navigation Structure

The app uses React Navigation with the following structure:

```
App (NavigationContainer)
└── Stack Navigator
    ├── Tabs (Tab Navigator)
    │   ├── Home Screen
    │   └── Explore Screen
    ├── Capture Screen
    └── Modal Screen
```

### Navigation Flow

1. **Home Tab**: Welcome screen with navigation to capture and modal
2. **Explore Tab**: Feature discovery with capture functionality
3. **Capture Screen**: Content capture with source type selection
4. **Modal Screen**: Modal presentation for additional features

## Content Capture

The capture screen supports multiple source types:

- **Webpage**: Capture web page content
- **Video**: Process video URLs (YouTube, Vimeo, etc.)
- **Audio**: Transcribe audio content
- **Voicememo**: Record and process voice memos

### Source Type Selection

Users can select from four source types:
- Webpage (default)
- Video
- Audio
- Voicememo

Each type has specific validation and helper text to guide users.

## Testing

The app includes comprehensive tests for all screens and navigation:

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm test -- --coverage
```

### Test Structure

- **App.test.tsx**: Main app component tests
- **HomeScreen.test.tsx**: Home screen functionality
- **ExploreScreen.test.tsx**: Explore screen functionality
- **CaptureScreen.test.tsx**: Capture screen with source type selection
- **ModalScreen.test.tsx**: Modal screen functionality

## Code Quality

### ESLint Configuration

The project uses ESLint with TypeScript support:

```bash
npm run lint
```

### TypeScript

Full TypeScript support with strict type checking:

```bash
npx tsc --noEmit
```

## Platform Support

- **iOS**: Native iOS app
- **Android**: Native Android app
- **Web**: Web application (single-page output)

## Development

### Adding New Screens

1. Create a new screen component in `screens/`
2. Add navigation types in the screen component
3. Register the screen in `App.tsx`
4. Add tests in `__tests__/`

### Adding New Dependencies

```bash
# Add a dependency
npm install package-name

# Add a dev dependency
npm install --save-dev package-name
```

## Troubleshooting

### Common Issues

1. **Metro bundler issues**: Clear cache with `npx expo start --clear`
2. **Navigation errors**: Ensure all screens are properly registered
3. **TypeScript errors**: Check type definitions and imports

### Debugging

- Use React Native Debugger for advanced debugging
- Check Expo logs in the terminal
- Use `console.log` for basic debugging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is part of the Synapse application suite.