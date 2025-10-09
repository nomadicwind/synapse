import React, { useState, useRef } from 'react';
import { View, TextInput, Alert, StyleSheet, Platform } from 'react-native';
import { Button } from 'react-native-paper';
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
    <View className="p-4 bg-white rounded-lg shadow-sm">
      {sourceType !== 'voicememo' && (
        <View className="mb-4">
          <TextInput
            ref={inputRef}
            className="border border-gray-300 rounded-lg p-4 text-lg mb-2"
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
            <Text className="text-red-500 text-sm mb-2">{error}</Text>
          ) : (
            <Text className="text-gray-500 text-sm">
              {sourceType === 'webpage' && 'Enter a webpage URL to capture its content'}
              {sourceType === 'video' && 'Enter a video URL (YouTube, Vimeo, etc.)'}
              {sourceType === 'audio' && 'Enter an audio URL to transcribe its content'}
            </Text>
          )}
        </View>
      )}

      <View className="flex-row flex-wrap justify-center mb-4 gap-2">
        {['webpage', 'video', 'audio', 'voicememo'].map((type) => (
          <Button
            key={type}
            mode={sourceType === type ? "contained" : "outlined"}
            onPress={() => handleSourceTypeChange(type)}
            className="mr-2 mb-2"
            style={{ minWidth: 80 }}
          >
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </Button>
        ))}
      </View>

      <Button
        mode="contained"
        onPress={handleSubmit}
        loading={isLoading}
        disabled={isLoading}
        className="bg-blue-600"
      >
        {isLoading ? "Capturing..." : "Capture"}
      </Button>
    </View>
  );
};

export default CaptureForm;
