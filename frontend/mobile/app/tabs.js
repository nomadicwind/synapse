import React from 'react';
import { Tabs } from 'expo-router';
import { useStore } from '../store/useStore';

export default function TabLayout() {
  const { isAuthenticated } = useStore();

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#007AFF',
        headerStyle: {
          backgroundColor: '#f4f4f4',
        },
        headerShadowVisible: false,
        headerTitleStyle: {
          fontWeight: 'bold',
        },
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, focused }) => (
            <TabBarIcon name={focused ? 'home' : 'home-outline'} color={color} />
          ),
        }}
      />
      {isAuthenticated && (
        <Tabs.Screen
          name="capture"
          options={{
            title: 'Capture',
            tabBarIcon: ({ color, focused }) => (
              <TabBarIcon name={focused ? 'add-circle' : 'add-circle-outline'} color={color} />
            ),
          }}
        />
      )}
      <Tabs.Screen
        name="settings"
        options={{
          title: 'Settings',
          tabBarIcon: ({ color, focused }) => (
            <TabBarIcon name={focused ? 'settings' : 'settings-outline'} color={color} />
          ),
        }}
      />
    </Tabs>
  );
}

function TabBarIcon(props) {
  const { name, color } = props;
  // Using Ionicons from '@expo/vector-icons'
  const Ionicons = require('@expo/vector-icons/Ionicons').default;
  return <Ionicons size={28} style={{ marginBottom: -3 }} {...props} />;
}
