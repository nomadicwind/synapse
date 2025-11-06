import React, { useState } from 'react';
import { View, Text, TextInput, Pressable, Alert, StyleSheet, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Tabs: undefined;
  Capture: undefined;
  Modal: undefined;
};

type CaptureScreenNavigationProp = NativeStackNavigationProp<RootStackParamList>;

export default function CaptureScreen() {
  const [url, setUrl] = useState('');
  const [sourceType, setSourceType] = useState('webpage');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const navigation = useNavigation<CaptureScreenNavigationProp>();

  // URL validation
  const isValidUrl = (string: string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSourceTypeChange = (type: string) => {
    setSourceType(type);
    setError('');
  };

  const handleCapture = async () => {
    setError('');
    
    if (!url.trim()) {
      setError('Please enter a URL');
      return;
    }

    if (sourceType !== 'voicememo' && !isValidUrl(url)) {
      setError('Please enter a valid URL (e.g., https://example.com)');
      return;
    }

    setIsLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      Alert.alert('Success', 'Content captured successfully!');
      setUrl('');
      setError('');
    } catch (error) {
      const errorMessage = 'Failed to capture content';
      setError(errorMessage);
      Alert.alert('Error', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Capture Content</Text>
      
      {sourceType !== 'voicememo' && (
        <View style={styles.inputSection}>
          <TextInput
            style={styles.input}
            placeholder="Enter URL (https://...)"
            placeholderTextColor="#666"
            value={url}
            onChangeText={setUrl}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            accessibilityLabel="URL input field"
            accessibilityHint="Enter the URL you want to capture"
          />
          {error ? (
            <Text style={styles.errorText}>{error}</Text>
          ) : (
            <Text style={styles.helperText}>
              {sourceType === 'webpage' && 'Enter a webpage URL to capture its content'}
              {sourceType === 'video' && 'Enter a video URL (YouTube, Vimeo, etc.)'}
              {sourceType === 'audio' && 'Enter an audio URL to transcribe its content'}
            </Text>
          )}
        </View>
      )}

      <View style={styles.buttonGroup}>
        {['webpage', 'video', 'audio', 'voicememo'].map((type) => (
          <Pressable
            key={type}
            style={({ pressed }) => [
              styles.typeButton,
              sourceType === type ? styles.typeButtonSelected : styles.typeButtonUnselected,
              pressed && styles.typeButtonPressed
            ]}
            onPress={() => handleSourceTypeChange(type)}
            accessibilityRole="button"
            accessibilityLabel={`Select ${type} type`}
          >
            <Text style={[
              styles.typeButtonText,
              sourceType === type ? styles.typeButtonTextSelected : styles.typeButtonTextUnselected
            ]}>
              {type.charAt(0).toUpperCase() + type.slice(1)}
            </Text>
          </Pressable>
        ))}
      </View>
      
      <Pressable
        style={({ pressed }) => [
          styles.button,
          isLoading && styles.buttonDisabled,
          pressed && !isLoading && styles.buttonPressed
        ]}
        onPress={handleCapture}
        disabled={isLoading}
        accessibilityRole="button"
        accessibilityLabel="Capture content"
      >
        <Text style={styles.buttonText}>
          {isLoading ? 'Capturing...' : 'Capture'}
        </Text>
      </Pressable>
      
      <Pressable
        style={styles.backButton}
        onPress={() => navigation.goBack()}
      >
        <Text style={styles.backButtonText}>Go Back</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 30,
    textAlign: 'center',
  },
  inputSection: {
    marginBottom: 16,
  },
  input: {
    borderWidth: 1,
    borderColor: '#d1d5db',
    borderRadius: 8,
    padding: 16,
    fontSize: 16,
    marginBottom: 8,
    backgroundColor: '#ffffff',
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      outlineStyle: 'none',
      cursor: 'text',
    }),
  },
  errorText: {
    color: '#ef4444',
    fontSize: 14,
    marginBottom: 8,
  },
  helperText: {
    color: '#6b7280',
    fontSize: 14,
  },
  buttonGroup: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: 16,
    gap: 8,
  },
  typeButton: {
    borderWidth: 2,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    minWidth: 80,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
    marginBottom: 8,
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      cursor: 'pointer',
      userSelect: 'none',
    }),
  },
  typeButtonSelected: {
    borderColor: '#3b82f6',
    backgroundColor: '#eff6ff',
  },
  typeButtonUnselected: {
    borderColor: '#d1d5db',
    backgroundColor: '#ffffff',
  },
  typeButtonPressed: {
    opacity: 0.7,
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: '500',
  },
  typeButtonTextSelected: {
    color: '#3b82f6',
  },
  typeButtonTextUnselected: {
    color: '#374151',
  },
  button: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      cursor: 'pointer',
      userSelect: 'none',
    }),
  },
  buttonDisabled: {
    backgroundColor: '#9ca3af',
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      cursor: 'not-allowed',
    }),
  },
  buttonPressed: {
    opacity: 0.8,
  },
  buttonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  backButton: {
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  backButtonText: {
    color: '#000',
    fontSize: 16,
    fontWeight: '500',
  },
});
