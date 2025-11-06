import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import ExploreScreen from '../screens/ExploreScreen';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

describe('ExploreScreen', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('renders explore title', () => {
    const { getByText } = render(<ExploreScreen />);
    expect(getByText('Explore Synapse')).toBeTruthy();
  });

  it('renders capture button', () => {
    const { getByText } = render(<ExploreScreen />);
    expect(getByText('📸 Capture Content')).toBeTruthy();
  });

  it('renders description', () => {
    const { getByText } = render(<ExploreScreen />);
    expect(getByText('Capture web pages, videos, and audio files for processing and analysis.')).toBeTruthy();
  });

  it('navigates to capture screen when capture button is pressed', () => {
    const { getByText } = render(<ExploreScreen />);
    const captureButton = getByText('📸 Capture Content');
    
    fireEvent.press(captureButton);
    expect(mockNavigate).toHaveBeenCalledWith('Capture');
  });
});
