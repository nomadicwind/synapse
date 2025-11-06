import React from 'react';
import { render, fireEvent } from '@testing-library/react-native';
import ModalScreen from '../screens/ModalScreen';

// Mock navigation
const mockGoBack = jest.fn();
jest.mock('@react-navigation/native', () => ({
  useNavigation: () => ({
    goBack: mockGoBack,
  }),
}));

describe('ModalScreen', () => {
  beforeEach(() => {
    mockGoBack.mockClear();
  });

  it('renders modal title', () => {
    const { getByText } = render(<ModalScreen />);
    expect(getByText('This is a modal')).toBeTruthy();
  });

  it('renders go back button', () => {
    const { getByText } = render(<ModalScreen />);
    expect(getByText('Go back')).toBeTruthy();
  });

  it('navigates back when go back button is pressed', () => {
    const { getByText } = render(<ModalScreen />);
    const goBackButton = getByText('Go back');
    
    fireEvent.press(goBackButton);
    expect(mockGoBack).toHaveBeenCalled();
  });
});
