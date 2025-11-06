import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import HomeScreen from '../screens/HomeScreen';

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

describe('HomeScreen', () => {
  beforeEach(() => {
    mockNavigate.mockClear();
  });

  it('renders welcome message', () => {
    const { getByText } = render(<HomeScreen />);
    expect(getByText('Welcome to Synapse!')).toBeTruthy();
  });

  it('renders capture button', () => {
    const { getByText } = render(<HomeScreen />);
    expect(getByText('Start Capturing Content')).toBeTruthy();
  });

  it('renders modal button', () => {
    const { getByText } = render(<HomeScreen />);
    expect(getByText('Open Modal')).toBeTruthy();
  });

  it('navigates to capture screen when capture button is pressed', () => {
    const { getByText } = render(<HomeScreen />);
    const captureButton = getByText('Start Capturing Content');
    
    fireEvent.press(captureButton);
    expect(mockNavigate).toHaveBeenCalledWith('Capture');
  });

  it('navigates to modal screen when modal button is pressed', () => {
    const { getByText } = render(<HomeScreen />);
    const modalButton = getByText('Open Modal');
    
    fireEvent.press(modalButton);
    expect(mockNavigate).toHaveBeenCalledWith('Modal');
  });
});
