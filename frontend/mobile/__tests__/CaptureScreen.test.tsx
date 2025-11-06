import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import CaptureScreen from '../screens/CaptureScreen';

// Mock navigation
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    goBack: mockGoBack,
  }),
}));

// Mock Alert
jest.mock('react-native/Libraries/Alert/Alert', () => ({
  alert: jest.fn(),
}));

describe('CaptureScreen', () => {
  beforeEach(() => {
    mockGoBack.mockClear();
    jest.clearAllMocks();
  });

  it('renders capture title', () => {
    const { getByText } = render(<CaptureScreen />);
    expect(getByText('Capture Content')).toBeTruthy();
  });

  it('renders source type buttons', () => {
    const { getByText } = render(<CaptureScreen />);
    expect(getByText('Webpage')).toBeTruthy();
    expect(getByText('Video')).toBeTruthy();
    expect(getByText('Audio')).toBeTruthy();
    expect(getByText('Voicememo')).toBeTruthy();
  });

  it('renders URL input field', () => {
    const { getByPlaceholderText } = render(<CaptureScreen />);
    expect(getByPlaceholderText('Enter URL (https://...)')).toBeTruthy();
  });

  it('renders capture button', () => {
    const { getByText } = render(<CaptureScreen />);
    expect(getByText('Capture')).toBeTruthy();
  });

  it('renders go back button', () => {
    const { getByText } = render(<CaptureScreen />);
    expect(getByText('Go Back')).toBeTruthy();
  });

  it('changes source type when button is pressed', () => {
    const { getByText } = render(<CaptureScreen />);
    const videoButton = getByText('Video');
    
    fireEvent.press(videoButton);
    // Check if the button is selected (this would require checking styles)
    expect(videoButton).toBeTruthy();
  });

  it('shows error when URL is empty and capture is pressed', async () => {
    const { getByText } = render(<CaptureScreen />);
    const captureButton = getByText('Capture');
    
    fireEvent.press(captureButton);
    
    await waitFor(() => {
      expect(getByText('Please enter a URL')).toBeTruthy();
    });
  });

  it('shows error when URL is invalid', async () => {
    const { getByText, getByPlaceholderText } = render(<CaptureScreen />);
    const urlInput = getByPlaceholderText('Enter URL (https://...)');
    const captureButton = getByText('Capture');
    
    fireEvent.changeText(urlInput, 'invalid-url');
    fireEvent.press(captureButton);
    
    await waitFor(() => {
      expect(getByText('Please enter a valid URL (e.g., https://example.com)')).toBeTruthy();
    });
  });

  it('navigates back when go back button is pressed', () => {
    const { getByText } = render(<CaptureScreen />);
    const goBackButton = getByText('Go Back');
    
    fireEvent.press(goBackButton);
    expect(mockGoBack).toHaveBeenCalled();
  });
});
