import React, { useState, useRef } from 'react';
import { View, Text, TextInput, Alert, StyleSheet, Platform, Pressable } from 'react-native';
import { useStore } from '../store/useStore';

const CaptureForm = ({ onCaptureSuccess, onCaptureError }) => {
  const [url, setUrl] = useState('');
  const [sourceType, setSourceType] = useState('webpage');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const { captureItem } = useStore();
  const inputRef = useRef(null);

  // URL validation
  const isValidUrl = (string) => {
    try {
      new URL(string);
      return true;
    } catch (_) {
      return false;
    }
  };

  const handleSubmit = async () => {
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
      const captureData = {
        source_type: sourceType,
        url: url.trim(),
      };
      
      const result = await captureItem(captureData);
      
      if (onCaptureSuccess) {
        onCaptureSuccess(result);
      }
      
      // Reset form
      setUrl('');
    } catch (error) {
      setError(error.message || 'Failed to capture item');
      if (onCaptureError) {
        onCaptureError(error);
      } else {
        Alert.alert('Error', error.message || 'Failed to capture item');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSourceTypeChange = (type) => {
    setSourceType(type);
    setError('');
    // Focus on input when changing source type (except for voicememo)
    if (type !== 'voicememo' && inputRef.current) {
      inputRef.current.focus();
    }
  };

  return (
    <View style={styles.container}>
      {sourceType !== 'voicememo' && (
        <View style={styles.inputSection}>
          <TextInput
            ref={inputRef}
            style={styles.textInput}
            placeholder="Enter URL (https://...)"
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
          styles.submitButton,
          isLoading && styles.submitButtonDisabled,
          pressed && !isLoading && styles.submitButtonPressed
        ]}
        onPress={handleSubmit}
        disabled={isLoading}
        accessibilityRole="button"
        accessibilityLabel="Capture content"
      >
        <Text style={styles.submitButtonText}>
          {isLoading ? "Capturing..." : "Capture"}
        </Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    backgroundColor: '#ffffff',
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  inputSection: {
    marginBottom: 16,
  },
  textInput: {
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
  submitButton: {
    backgroundColor: '#3b82f6',
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      cursor: 'pointer',
      userSelect: 'none',
    }),
  },
  submitButtonDisabled: {
    backgroundColor: '#9ca3af',
    // Web-specific styles
    ...(Platform.OS === 'web' && {
      cursor: 'not-allowed',
    }),
  },
  submitButtonPressed: {
    opacity: 0.8,
  },
  submitButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default CaptureForm;
