import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ReportReviewModal from '../ReportReviewModal';

describe('ReportReviewModal', () => {
  const mockOnSubmit = jest.fn();
  const mockOnClose = jest.fn();
  
  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    onSubmit: mockOnSubmit,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders modal when open', () => {
    render(<ReportReviewModal {...defaultProps} />);
    
    expect(screen.getByText('Report Review')).toBeInTheDocument();
    expect(screen.getByText('Why are you reporting this review?')).toBeInTheDocument();
    expect(screen.getByText('Additional details')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<ReportReviewModal {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText('Report Review')).not.toBeInTheDocument();
  });

  it('displays all report reason options', () => {
    render(<ReportReviewModal {...defaultProps} />);
    
    expect(screen.getByText('Spam or fake review')).toBeInTheDocument();
    expect(screen.getByText('Inappropriate content')).toBeInTheDocument();
    expect(screen.getByText('Offensive language')).toBeInTheDocument();
    expect(screen.getByText('Fake or misleading review')).toBeInTheDocument();
    expect(screen.getByText('Not relevant to the product')).toBeInTheDocument();
    expect(screen.getByText('Other reason')).toBeInTheDocument();
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const submitButton = screen.getByText('Report Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please select a reason for reporting')).toBeInTheDocument();
      expect(screen.getByText('Please provide additional details')).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('validates minimum description length', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    // Select a reason
    const spamRadio = screen.getByLabelText('Spam or fake review');
    await user.click(spamRadio);
    
    // Enter short description
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, 'Too short');
    
    const submitButton = screen.getByText('Report Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Description should be at least 10 characters long')).toBeInTheDocument();
    });
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReportReviewModal {...defaultProps} />);
    
    // Select reason
    const inappropriateRadio = screen.getByLabelText('Inappropriate content');
    await user.click(inappropriateRadio);
    
    // Enter description
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, 'This review contains inappropriate language and content that violates community guidelines.');
    
    const submitButton = screen.getByText('Report Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        reason: 'inappropriate',
        description: 'This review contains inappropriate language and content that violates community guidelines.',
      });
    });
  });

  it('closes modal after successful submission', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReportReviewModal {...defaultProps} />);
    
    // Fill form
    const spamRadio = screen.getByLabelText('Spam or fake review');
    await user.click(spamRadio);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, 'This is clearly a fake review posted by the seller.');
    
    const submitButton = screen.getByText('Report Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it('calls onClose when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('calls onClose when X button is clicked', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const closeButton = screen.getByRole('button', { name: '' }); // X icon button
    await user.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('shows loading state', () => {
    render(<ReportReviewModal {...defaultProps} loading />);
    
    expect(screen.getByText('Reporting...')).toBeInTheDocument();
    expect(screen.getByText('Reporting...')).toBeDisabled();
    expect(screen.getByText('Cancel')).toBeDisabled();
  });

  it('displays error message', () => {
    const errorMessage = 'Failed to report review';
    render(<ReportReviewModal {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it('clears field errors when user starts typing', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    // Trigger validation errors
    const submitButton = screen.getByText('Report Review');
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Please provide additional details')).toBeInTheDocument();
    });
    
    // Start typing in description field
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, 'A');
    
    // Error should be cleared
    expect(screen.queryByText('Please provide additional details')).not.toBeInTheDocument();
  });

  it('shows character count', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    // Initially shows 0/500
    expect(screen.getByText('0/500')).toBeInTheDocument();
    
    // Type some text
    await user.type(descriptionTextarea, 'This is a test description');
    
    // Should update character count
    expect(screen.getByText('26/500')).toBeInTheDocument();
  });

  it('enforces maximum character limit', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    // Try to type more than 500 characters
    const longText = 'a'.repeat(600);
    await user.type(descriptionTextarea, longText);
    
    // Should be limited to 500 characters
    expect(descriptionTextarea).toHaveValue('a'.repeat(500));
    expect(screen.getByText('500/500')).toBeInTheDocument();
  });

  it('resets form when modal is closed and reopened', async () => {
    const user = userEvent.setup();
    const { rerender } = render(<ReportReviewModal {...defaultProps} />);
    
    // Fill form
    const spamRadio = screen.getByLabelText('Spam or fake review');
    await user.click(spamRadio);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, 'Test description');
    
    // Close modal
    rerender(<ReportReviewModal {...defaultProps} isOpen={false} />);
    
    // Reopen modal
    rerender(<ReportReviewModal {...defaultProps} isOpen={true} />);
    
    // Form should be reset
    const newSpamRadio = screen.getByLabelText('Spam or fake review');
    const newDescriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    expect(newSpamRadio).not.toBeChecked();
    expect(newDescriptionTextarea).toHaveValue('');
  });

  it('prevents closing when loading', async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} loading />);
    
    const closeButton = screen.getByRole('button', { name: '' }); // X icon button
    const cancelButton = screen.getByText('Cancel');
    
    expect(closeButton).toBeDisabled();
    expect(cancelButton).toBeDisabled();
    
    // Clicking should not call onClose
    await user.click(closeButton);
    await user.click(cancelButton);
    
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});