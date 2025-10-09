import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import CaptureForm from '../components/CaptureForm';
import { useStore } from '../store/useStore';

export default function CaptureScreen() {
  const { user, isAuthenticated } = useStore();

  if (!isAuthenticated) {
    return (
      <View style={styles.container}>
        <Text>Please log in to capture content</Text>
      </View>
    );
  }

  const handleCaptureSuccess = (item) => {
    // Handle successful capture
    console.log('Capture successful:', item);
    // Navigate to item detail or show success message
  };

  const handleCaptureError = (error) => {
    // Handle capture error
    console.error('Capture error:', error);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Capture New Content</Text>
      <CaptureForm 
        onCaptureSuccess={handleCaptureSuccess}
        onCaptureError={handleCaptureError}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
});
