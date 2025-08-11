import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import configureStore from 'redux-mock-store';
import { thunk } from 'redux-thunk';
import KYCVerification from '../KYCVerification';
import { uploadKYCDocument } from '../../../store/slices/sellerSlice';
import type { Middleware } from '@reduxjs/toolkit';

// Mock the dispatch function
jest.mock('react-redux', () => ({
  ...jest.requireActual('react-redux'),
  useDispatch: () => jest.fn().mockReturnValue(() => Promise.resolve()),
}));

// Create mock store
const middlewares: Middleware[] = [thunk];
const mockStore = configureStore(middlewares);

describe('KYCVerification Component', () => {
  let store: any;

  beforeEach(() => {
    store = mockStore({
      seller: {
        kycDocuments: [
          {
            id: '1',
            document_type: 'ID_PROOF',
            document_type_display: 'ID Proof',
            document_number: 'ABC123',
            document_name: 'Aadhar Card',
            verification_status: 'PENDING',
            verification_status_display: 'Pending',
            created_at: '2023-01-01T00:00:00Z',
          },
          {
            id: '2',
            document_type: 'ADDRESS_PROOF',
            document_type_display: 'Address Proof',
            document_number: 'XYZ456',
            document_name: 'Utility Bill',
            verification_status: 'VERIFIED',
            verification_status_display: 'Verified',
            created_at: '2023-01-02T00:00:00Z',
          },
        ],
        loading: false,
        error: null,
      },
    });
  });

  test('renders the component correctly', () => {
    render(
      <Provider store={store}>
        <KYCVerification />
      </Provider>
    );

    // Check if component elements are displayed
    expect(screen.getByText('KYC Verification')).toBeInTheDocument();
    expect(screen.getByText('Upload KYC Document')).toBeInTheDocument();
    expect(screen.getByText('Uploaded Documents')).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Number/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document File/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Upload Document/i })).toBeInTheDocument();
  });

  test('displays uploaded documents', () => {
    render(
      <Provider store={store}>
        <KYCVerification />
      </Provider>
    );

    // Check if uploaded documents are displayed
    expect(screen.getByText('ID Proof')).toBeInTheDocument();
    expect(screen.getByText('Aadhar Card')).toBeInTheDocument();
    expect(screen.getByText('ABC123')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    
    expect(screen.getByText('Address Proof')).toBeInTheDocument();
    expect(screen.getByText('Utility Bill')).toBeInTheDocument();
    expect(screen.getByText('XYZ456')).toBeInTheDocument();
    expect(screen.getByText('Verified')).toBeInTheDocument();
  });

  test('displays error message when there is an error', () => {
    const errorStore = mockStore({
      seller: {
        kycDocuments: [],
        loading: false,
        error: 'Failed to load KYC documents',
      },
    });

    render(
      <Provider store={errorStore}>
        <KYCVerification />
      </Provider>
    );

    // Check if error message is displayed
    expect(screen.getByText('Failed to load KYC documents')).toBeInTheDocument();
  });

  test('displays success message after document upload', async () => {
    // Mock successful document upload
    const successStore = mockStore({
      seller: {
        kycDocuments: [],
        loading: false,
        error: null,
      },
    });

    render(
      <Provider store={successStore}>
        <KYCVerification />
      </Provider>
    );

    // Fill out the form
    fireEvent.change(screen.getByLabelText(/Document Type/i), {
      target: { value: 'ID_PROOF' },
    });
    fireEvent.change(screen.getByLabelText(/Document Name/i), {
      target: { value: 'Aadhar Card' },
    });
    fireEvent.change(screen.getByLabelText(/Document Number/i), {
      target: { value: 'ABC123' },
    });

    // Create a mock file
    const file = new File(['dummy content'], 'document.pdf', { type: 'application/pdf' });
    fireEvent.change(screen.getByLabelText(/Document File/i), {
      target: { files: [file] },
    });

    // Submit the form
    fireEvent.click(screen.getByRole('button', { name: /Upload Document/i }));

    // Wait for the success message to appear
    await waitFor(() => {
      expect(screen.getByText('Document uploaded successfully!')).toBeInTheDocument();
    });
  });

  test('disables submit button when loading', () => {
    const loadingStore = mockStore({
      seller: {
        kycDocuments: [],
        loading: true,
        error: null,
      },
    });

    render(
      <Provider store={loadingStore}>
        <KYCVerification />
      </Provider>
    );

    // Check if submit button is disabled
    expect(screen.getByRole('button', { name: /Uploading/i })).toBeDisabled();
  });
});