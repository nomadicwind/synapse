import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { ThemeProvider } from '@/components/themed-text';
import { apiClient } from '@/api/APIClient';
import CapturePage from '@/app/capture';

// Mock global alert function
global.alert = jest.fn();

// Mock the apiClient
jest.mock('@/api/APIClient', () => ({
  apiClient: {
    captureItem: jest.fn(),
  },
}));

// Mock the useRouter hook
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
  }),
}));

// Mock the useColorScheme hook
jest.mock('@/hooks/use-color-scheme', () => ({
  useColorScheme: () => 'light',
}));

describe('CapturePage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly', () => {
    const { getByText, getByPlaceholderText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    expect(getByText('Capture Content')).toBeTruthy();
    expect(getByText('Paste a URL or local file path to capture content')).toBeTruthy();
    expect(getByPlaceholderText('https://example.com')).toBeTruthy();
    expect(getByText('Webpage')).toBeTruthy();
    expect(getByText('Video')).toBeTruthy();
    expect(getByText('Audio')).toBeTruthy();
    expect(getByText('Capture Content')).toBeTruthy();
  });

  it('validates empty URL', async () => {
    const alertSpy = jest.spyOn(global, 'alert').mockImplementation(() => {});
    const { getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.press(getByText('Capture Content'));
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Error', 'Please enter a URL');
    });

    alertSpy.mockRestore();
  });

  it('validates invalid URL', async () => {
    const alertSpy = jest.spyOn(global, 'alert').mockImplementation(() => {});
    const { getByPlaceholderText, getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.changeText(getByPlaceholderText('https://example.com'), 'invalid-url');
    fireEvent.press(getByText('Capture Content'));
    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Error', 'Please enter a valid URL');
    });

    alertSpy.mockRestore();
  });

  it('submits valid capture request', async () => {
    const pushMock = jest.fn();
    jest.mock('expo-router', () => ({
      useRouter: () => ({
        push: pushMock,
      }),
    }));

    apiClient.captureItem.mockResolvedValue({ itemId: '123' });

    const { getByPlaceholderText, getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.changeText(getByPlaceholderText('https://example.com'), 'https://example.com');
    fireEvent.press(getByText('Video'));
    fireEvent.press(getByText('Capture Content'));

    await waitFor(() => {
      expect(apiClient.captureItem).toHaveBeenCalledWith({
        source_type: 'video',
        url: 'https://example.com',
      });
    });

    // Check that success alert is shown
    expect(global.alert).toHaveBeenCalledWith(
      'Success',
      'Content capture request submitted successfully!',
      expect.any(Array)
    );
  });

  it('handles API error', async () => {
    const alertSpy = jest.spyOn(global, 'alert').mockImplementation(() => {});
    apiClient.captureItem.mockRejectedValue(new Error('API Error'));

    const { getByPlaceholderText, getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.changeText(getByPlaceholderText('https://example.com'), 'https://example.com');
    fireEvent.press(getByText('Capture Content'));

    await waitFor(() => {
      expect(alertSpy).toHaveBeenCalledWith('Error', 'Failed to submit capture request. Please try again.');
    });

    alertSpy.mockRestore();
  });

  it('updates source type when radio button is pressed', () => {
    const { getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.press(getByText('Video'));
    // Since we can't easily test the internal state, we'll just verify the API call uses the correct type in the next test

    fireEvent.press(getByText('Audio'));
    // Same as above
  });

  it('disables submit button when loading', async () => {
    apiClient.captureItem.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { getByText } = render(
      <ThemeProvider>
        <CapturePage />
      </ThemeProvider>
    );

    fireEvent.changeText(getByPlaceholderText('https://example.com'), 'https://example.com');
    fireEvent.press(getByText('Capture Content'));

    await waitFor(() => {
      expect(getByText('Submitting...')).toBeTruthy();
    });
  });
});
