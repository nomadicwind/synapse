import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { Provider } from 'react-redux';
import { useStore } from '../../store/useStore';
import CaptureForm from '../CaptureForm';

// Mock the useStore hook
jest.mock('../../store/useStore', () => ({
  useStore: jest.fn(),
}));

// Mock Alert
jest.mock('react-native', () => {
  const actualReactNative = jest.requireActual('react-native');
  return {
    ...actualReactNative,
    Alert: {
      alert: jest.fn(),
    },
  };
});

describe('CaptureForm', () => {
  const mockCaptureItem = jest.fn();
  const mockOnCaptureSuccess = jest.fn();
  const mockOnCaptureError = jest.fn();

  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Mock useStore
    useStore.mockReturnValue({
      captureItem: mockCaptureItem,
    });
  });

  it('renders correctly', () => {
    const { getByPlaceholderText, getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    expect(getByPlaceholderText('Enter URL (https://...)')).toBeTruthy();
    expect(getByText('Webpage')).toBeTruthy();
    expect(getByText('Video')).toBeTruthy();
    expect(getByText('Audio')).toBeTruthy();
    expect(getByText('Capture')).toBeTruthy();
  });

  it('validates empty URL', () => {
    const { getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    fireEvent.press(getByText('Capture'));
    
    // Check if Alert.alert was called
    expect(require('react-native').Alert.alert).toHaveBeenCalledWith(
      'Error', 
      'Please enter a URL'
    );
  });

  it('handles successful capture', async () => {
    const mockResponse = {
      id: '123',
      source_type: 'webpage',
      source_url: 'https://example.com',
      status: 'processing'
    };
    
    mockCaptureItem.mockResolvedValue(mockResponse);

    const { getByPlaceholderText, getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    // Enter URL
    fireEvent.changeText(getByPlaceholderText('Enter URL (https://...)'), 'https://example.com');
    
    // Submit form
    fireEvent.press(getByText('Capture'));

    // Wait for async operations
    await waitFor(() => {
      expect(mockCaptureItem).toHaveBeenCalledWith({
        source_type: 'webpage',
        url: 'https://example.com',
      });
      expect(mockOnCaptureSuccess).toHaveBeenCalledWith(mockResponse);
    });
  });

  it('handles capture error', async () => {
    const mockError = new Error('Capture failed');
    mockCaptureItem.mockRejectedValue(mockError);

    const { getByPlaceholderText, getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    // Enter URL
    fireEvent.changeText(getByPlaceholderText('Enter URL (https://...)'), 'https://example.com');
    
    // Submit form
    fireEvent.press(getByText('Capture'));

    // Wait for async operations
    await waitFor(() => {
      expect(mockOnCaptureError).toHaveBeenCalledWith(mockError);
    });
  });

  it('updates source type', () => {
    const { getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    // Click Video button
    fireEvent.press(getByText('Video'));
    expect(getByText('Video').props.color).toBe('#007AFF');
    expect(getByText('Webpage').props.color).toBe('#ccc');
    expect(getByText('Audio').props.color).toBe('#ccc');

    // Click Audio button
    fireEvent.press(getByText('Audio'));
    expect(getByText('Audio').props.color).toBe('#007AFF');
    expect(getByText('Webpage').props.color).toBe('#ccc');
    expect(getByText('Video').props.color).toBe('#ccc');
  });

  it('disables button during loading', () => {
    const { getByText } = render(
      <CaptureForm 
        onCaptureSuccess={mockOnCaptureSuccess}
        onCaptureError={mockOnCaptureError}
      />
    );

    const captureButton = getByText('Capture');
    
    // Start loading
    fireEvent.press(captureButton);
    
    // Button should show loading state
    expect(getByText('Capturing...')).toBeTruthy();
    expect(captureButton.props.disabled).toBe(true);
    
    // After loading completes, button should be enabled again
    mockCaptureItem.mockResolvedValue({});
  });
});
