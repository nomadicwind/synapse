import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient } from '../api/APIClient';

// Define the initial state
const initialState = {
  user: null,
  isAuthenticated: false,
  knowledgeItems: [],
  isLoading: false,
  error: null,
};

// Create the store
export const useStore = create(
  persist(
    (set, get) => ({
      ...initialState,
      
      // Actions
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      clearUser: () => set({ user: null, isAuthenticated: false }),
      setKnowledgeItems: (items) => set({ knowledgeItems: items }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
      
      // Async actions
      login: async (credentials) => {
        try {
          set({ isLoading: true, error: null });
          const { user, token } = await apiClient.login(credentials);
          set({ user, isAuthenticated: true });
        } catch (error) {
          set({ error: error.message || 'Login failed' });
        } finally {
          set({ isLoading: false });
        }
      },
      
      logout: async () => {
        try {
          await apiClient.logout();
          get().clearUser();
        } catch (error) {
          set({ error: error.message || 'Logout failed' });
        }
      },
      
      fetchKnowledgeItems: async () => {
        try {
          set({ isLoading: true, error: null });
          const items = await apiClient.getKnowledgeItems();
          set({ knowledgeItems: items });
        } catch (error) {
          set({ error: error.message || 'Failed to fetch knowledge items' });
        } finally {
          set({ isLoading: false });
        }
      },
      
      captureItem: async (captureData) => {
        try {
          set({ isLoading: true, error: null });
          const response = await apiClient.captureItem(captureData);
          // Add the new item to the knowledge items list
          const currentItems = get().knowledgeItems;
          set({ knowledgeItems: [...currentItems, response] });
          return response;
        } catch (error) {
          set({ error: error.message || 'Failed to capture item' });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },
    }),
    {
      name: 'synapse-storage', // name of the item in storage
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
