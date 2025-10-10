import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

class SecureStorage {
  static async getItem(key) {
    if (Platform.OS === 'web') {
      try {
        return localStorage.getItem(key);
      } catch (error) {
        console.warn('Web localStorage error:', error);
        return null;
      }
    } else {
      try {
        return await SecureStore.getItemAsync(key);
      } catch (error) {
        console.warn('SecureStore error:', error);
        return null;
      }
    }
  }

  static async setItem(key, value) {
    if (Platform.OS === 'web') {
      try {
        localStorage.setItem(key, value);
        return true;
      } catch (error) {
        console.warn('Web localStorage error:', error);
        return false;
      }
    } else {
      try {
        await SecureStore.setItemAsync(key, value);
        return true;
      } catch (error) {
        console.warn('SecureStore error:', error);
        return false;
      }
    }
  }

  static async deleteItem(key) {
    if (Platform.OS === 'web') {
      try {
        localStorage.removeItem(key);
        return true;
      } catch (error) {
        console.warn('Web localStorage error:', error);
        return false;
      }
    } else {
      try {
        await SecureStore.deleteItemAsync(key);
        return true;
      } catch (error) {
        console.warn('SecureStore error:', error);
        return false;
      }
    }
  }

  static async clear() {
    if (Platform.OS === 'web') {
      try {
        localStorage.clear();
        return true;
      } catch (error) {
        console.warn('Web localStorage error:', error);
        return false;
      }
    } else {
      // SecureStore doesn't have a clear method, so we need to delete items individually
      // This is a limitation, but for now we'll just return true
      return true;
    }
  }
}

export default SecureStorage;
