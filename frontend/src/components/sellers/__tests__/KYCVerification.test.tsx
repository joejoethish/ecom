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
  ...jest.requireActual(&apos;react-redux&apos;),
  useDispatch: () => jest.fn().mockReturnValue(() => Promise.resolve()),
}));

// Create mock store
const mockStore = configureStore(middlewares);

describe(&apos;KYCVerification Component&apos;, () => {
  let store: unknown;

  beforeEach(() => {
    store = mockStore({
      seller: {
        kycDocuments: [
          {
            id: &apos;1&apos;,
            document_type: &apos;ID_PROOF&apos;,
            document_type_display: &apos;ID Proof&apos;,
            document_number: &apos;ABC123&apos;,
            document_name: &apos;Aadhar Card&apos;,
            verification_status: &apos;PENDING&apos;,
            verification_status_display: &apos;Pending&apos;,
            created_at: &apos;2023-01-01T00:00:00Z&apos;,
          },
          {
            id: &apos;2&apos;,
            document_type: &apos;ADDRESS_PROOF&apos;,
            document_type_display: &apos;Address Proof&apos;,
            document_number: &apos;XYZ456&apos;,
            document_name: &apos;Utility Bill&apos;,
            verification_status: &apos;VERIFIED&apos;,
            verification_status_display: &apos;Verified&apos;,
            created_at: &apos;2023-01-02T00:00:00Z&apos;,
          },
        ],
        loading: false,
        error: null,
      },
    });
  });

  test(&apos;renders the component correctly&apos;, () => {
    render(
      <Provider store={store}>
        <KYCVerification />
      </Provider>
    );

    // Check if component elements are displayed
    expect(screen.getByText(&apos;KYC Verification&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Upload KYC Document&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Uploaded Documents&apos;)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Type/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document Number/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Document File/i)).toBeInTheDocument();
    expect(screen.getByRole(&apos;button&apos;, { name: /Upload Document/i })).toBeInTheDocument();
  });

  test(&apos;displays uploaded documents&apos;, () => {
    render(
      <Provider store={store}>
        <KYCVerification />
      </Provider>
    );

    // Check if uploaded documents are displayed
    expect(screen.getByText(&apos;ID Proof&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Aadhar Card&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;ABC123&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Pending&apos;)).toBeInTheDocument();
    
    expect(screen.getByText(&apos;Address Proof&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Utility Bill&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;XYZ456&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Verified&apos;)).toBeInTheDocument();
  });

  test(&apos;displays error message when there is an error&apos;, () => {
    const errorStore = mockStore({
      seller: {
        kycDocuments: [],
        loading: false,
        error: &apos;Failed to load KYC documents&apos;,
      },
    });

    render(
      <Provider store={errorStore}>
        <KYCVerification />
      </Provider>
    );

    // Check if error message is displayed
    expect(screen.getByText(&apos;Failed to load KYC documents&apos;)).toBeInTheDocument();
  });

  test(&apos;displays success message after document upload&apos;, async () => {
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
      target: { value: &apos;ID_PROOF&apos; },
    });
    fireEvent.change(screen.getByLabelText(/Document Name/i), {
      target: { value: &apos;Aadhar Card&apos; },
    });
    fireEvent.change(screen.getByLabelText(/Document Number/i), {
      target: { value: &apos;ABC123&apos; },
    });

    // Create a mock file
    const file = new File([&apos;dummy content&apos;], &apos;document.pdf&apos;, { type: &apos;application/pdf&apos; });
    fireEvent.change(screen.getByLabelText(/Document File/i), {
      target: { files: [file] },
    });

    // Submit the form
    fireEvent.click(screen.getByRole(&apos;button&apos;, { name: /Upload Document/i }));

    // Wait for the success message to appear
    await waitFor(() => {
      expect(screen.getByText(&apos;Document uploaded successfully!&apos;)).toBeInTheDocument();
    });
  });

  test(&apos;disables submit button when loading&apos;, () => {
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