import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

type RootStackParamList = {
  Tabs: undefined;
  Capture: undefined;
  Modal: undefined;
};

type ExploreScreenNavigationProp = NativeStackNavigationProp<RootStackParamList>;

export default function ExploreScreen() {
  const navigation = useNavigation<ExploreScreenNavigationProp>();

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Explore Synapse</Text>
      <Text style={styles.subtitle}>Discover the features and capabilities of Synapse.</Text>
      
      <Pressable
        style={styles.button}
        onPress={() => navigation.navigate('Capture')}
      >
        <Text style={styles.buttonText}>📸 Capture Content</Text>
      </Pressable>
      
      <Text style={styles.description}>
        Capture web pages, videos, and audio files for processing and analysis.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 10,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginBottom: 30,
    lineHeight: 22,
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 24,
    marginBottom: 16,
    minWidth: 200,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  description: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
});
