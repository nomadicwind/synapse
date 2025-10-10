import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, Alert, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { useColorScheme } from '@/hooks/use-color-scheme';
import { ThemedView } from '@/components/themed-view';
import { ThemedText } from '@/components/themed-text';
import { apiClient } from '@/api/APIClient.js';

export default function WebCapturePage() {
  const [url, setUrl] = useState('');
  const [sourceType, setSourceType] = useState<'webpage' | 'video' | 'audio'>('webpage');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();
  const colorScheme = useColorScheme();

  const handleSubmit = async () => {
    if (!url.trim()) {
      Alert.alert('Error', 'Please enter a URL');
      return;
    }

    // Basic URL validation
    try {
      new URL(url);
    } catch (e) {
      Alert.alert('Error', 'Please enter a valid URL');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiClient.captureItem({
        source_type: sourceType,
        url: url
      });

      Alert.alert(
        'Success',
        'Content capture request submitted successfully!',
        [
          {
            text: 'OK',
            onPress: () => {
              setUrl('');
              router.push('/'); // Navigate back to home
            }
          }
        ]
      );
    } catch (error: any) {
      Alert.alert(
        'Error',
        error.response?.data?.detail || 'Failed to submit capture request. Please try again.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedText type="title" style={styles.title}>
        Capture Content
      </ThemedText>
      
      <ThemedText style={styles.description}>
        Paste a URL or local file path to capture content
      </ThemedText>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <ThemedText style={styles.label}>URL or File Path</ThemedText>
          <TextInput
            style={[
              styles.input,
              { backgroundColor: colorScheme === 'dark' ? '#1a1a1a' : '#f5f5f5' }
            ]}
            value={url}
            onChangeText={setUrl}
            placeholder="https://example.com"
            placeholderTextColor={colorScheme === 'dark' ? '#888' : '#666'}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />
        </View>

        <View style={styles.inputGroup}>
          <ThemedText style={styles.label}>Content Type</ThemedText>
          <View style={styles.radioGroup}>
            {(['webpage', 'video', 'audio'] as const).map((type) => (
              <TouchableOpacity
                key={type}
                style={[
                  styles.radioButton,
                  sourceType === type && styles.radioButtonSelected,
                  { 
                    borderColor: colorScheme === 'dark' ? '#444' : '#ccc',
                    backgroundColor: sourceType === type 
                      ? (colorScheme === 'dark' ? '#333' : '#e0e0e0')
                      : (colorScheme === 'dark' ? '#1a1a1a' : '#f5f5f5')
                  }
                ]}
                onPress={() => setSourceType(type)}
              >
                <ThemedText style={[
                  styles.radioLabel,
                  sourceType === type && styles.radioLabelSelected
                ]}>
                  {type.charAt(0).toUpperCase() + type.slice(1)}
                </ThemedText>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        <TouchableOpacity
          style={[
            styles.submitButton,
            isLoading && styles.submitButtonDisabled
          ]}
          onPress={handleSubmit}
          disabled={isLoading}
        >
          <ThemedText style={styles.submitButtonText}>
            {isLoading ? 'Submitting...' : 'Capture Content'}
          </ThemedText>
        </TouchableOpacity>
      </View>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  title: {
    marginBottom: 20,
    textAlign: 'center',
  },
  description: {
    marginBottom: 30,
    textAlign: 'center',
    fontSize: 16,
    opacity: 0.8,
  },
  form: {
    gap: 20,
  },
  inputGroup: {
    gap: 8,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#000',
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
  },
  radioButton: {
    borderWidth: 2,
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    minWidth: 100,
  },
  radioButtonSelected: {
    borderColor: '#007AFF',
  },
  radioLabel: {
    fontSize: 14,
    textAlign: 'center',
  },
  radioLabelSelected: {
    color: '#007AFF',
    fontWeight: '600',
  },
  submitButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
    marginTop: 20,
  },
  submitButtonDisabled: {
    backgroundColor: '#ccc',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
  },
});
