import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
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

  it(&apos;renders modal when open&apos;, () => {
    render(<ReportReviewModal {...defaultProps} />);
    
    expect(screen.getByText(&apos;Report Review&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Why are you reporting this review?&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Additional details&apos;)).toBeInTheDocument();
  });

  it(&apos;does not render when closed&apos;, () => {
    render(<ReportReviewModal {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText(&apos;Report Review&apos;)).not.toBeInTheDocument();
  });

  it(&apos;displays all report reason options&apos;, () => {
    render(<ReportReviewModal {...defaultProps} />);
    
    expect(screen.getByText(&apos;Spam or fake review&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Inappropriate content&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Offensive language&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Fake or misleading review&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Not relevant to the product&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Other reason&apos;)).toBeInTheDocument();
  });

  it(&apos;validates required fields&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const submitButton = screen.getByText(&apos;Report Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Please select a reason for reporting&apos;)).toBeInTheDocument();
      expect(screen.getByText(&apos;Please provide additional details&apos;)).toBeInTheDocument();
    });
    
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it(&apos;validates minimum description length&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    // Select a reason
    const spamRadio = screen.getByLabelText(&apos;Spam or fake review&apos;);
    await user.click(spamRadio);
    
    // Enter short description
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, &apos;Too short&apos;);
    
    const submitButton = screen.getByText(&apos;Report Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Description should be at least 10 characters long&apos;)).toBeInTheDocument();
    });
  });

  it(&apos;submits form with valid data&apos;, async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReportReviewModal {...defaultProps} />);
    
    // Select reason
    const inappropriateRadio = screen.getByLabelText(&apos;Inappropriate content&apos;);
    await user.click(inappropriateRadio);
    
    // Enter description
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, &apos;This review contains inappropriate language and content that violates community guidelines.&apos;);
    
    const submitButton = screen.getByText(&apos;Report Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        reason: &apos;inappropriate&apos;,
        description: &apos;This review contains inappropriate language and content that violates community guidelines.&apos;,
      });
    });
  });

  it(&apos;closes modal after successful submission&apos;, async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockResolvedValue(undefined);
    
    render(<ReportReviewModal {...defaultProps} />);
    
    // Fill form
    const spamRadio = screen.getByLabelText(&apos;Spam or fake review&apos;);
    await user.click(spamRadio);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, &apos;This is clearly a fake review posted by the seller.&apos;);
    
    const submitButton = screen.getByText(&apos;Report Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  it(&apos;calls onClose when cancel button is clicked&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const cancelButton = screen.getByText(&apos;Cancel&apos;);
    await user.click(cancelButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it(&apos;calls onClose when X button is clicked&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const closeButton = screen.getByRole(&apos;button&apos;, { name: &apos;&apos; }); // X icon button
    await user.click(closeButton);
    
    expect(mockOnClose).toHaveBeenCalled();
  });

  it(&apos;shows loading state&apos;, () => {
    render(<ReportReviewModal {...defaultProps} loading />);
    
    expect(screen.getByText(&apos;Reporting...&apos;)).toBeInTheDocument();
    expect(screen.getByText(&apos;Reporting...&apos;)).toBeDisabled();
    expect(screen.getByText(&apos;Cancel&apos;)).toBeDisabled();
  });

  it(&apos;displays error message&apos;, () => {
    const errorMessage = &apos;Failed to report review&apos;;
    render(<ReportReviewModal {...defaultProps} error={errorMessage} />);
    
    expect(screen.getByText(errorMessage)).toBeInTheDocument();
  });

  it(&apos;clears field errors when user starts typing&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    // Trigger validation errors
    const submitButton = screen.getByText(&apos;Report Review&apos;);
    await user.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText(&apos;Please provide additional details&apos;)).toBeInTheDocument();
    });
    
    // Start typing in description field
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, &apos;A&apos;);
    
    // Error should be cleared
    expect(screen.queryByText(&apos;Please provide additional details&apos;)).not.toBeInTheDocument();
  });

  it(&apos;shows character count&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    // Initially shows 0/500
    expect(screen.getByText(&apos;0/500&apos;)).toBeInTheDocument();
    
    // Type some text
    await user.type(descriptionTextarea, &apos;This is a test description&apos;);
    
    // Should update character count
    expect(screen.getByText(&apos;26/500&apos;)).toBeInTheDocument();
  });

  it(&apos;enforces maximum character limit&apos;, async () => {
    const user = userEvent.setup();
    render(<ReportReviewModal {...defaultProps} />);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    // Try to type more than 500 characters
    const longText = &apos;a&apos;.repeat(600);
    await user.type(descriptionTextarea, longText);
    
    // Should be limited to 500 characters
    expect(descriptionTextarea).toHaveValue(&apos;a&apos;.repeat(500));
    expect(screen.getByText(&apos;500/500&apos;)).toBeInTheDocument();
  });

  it(&apos;resets form when modal is closed and reopened&apos;, async () => {
    const user = userEvent.setup();
    
    // Fill form
    const spamRadio = screen.getByLabelText(&apos;Spam or fake review&apos;);
    await user.click(spamRadio);
    
    const descriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    await user.type(descriptionTextarea, &apos;Test description&apos;);
    
    // Close modal
    rerender(<ReportReviewModal {...defaultProps} isOpen={false} />);
    
    // Reopen modal
    rerender(<ReportReviewModal {...defaultProps} isOpen={true} />);
    
    // Form should be reset
    const newSpamRadio = screen.getByLabelText(&apos;Spam or fake review&apos;);
    const newDescriptionTextarea = screen.getByPlaceholderText(/please provide more details/i);
    
    expect(newSpamRadio).not.toBeChecked();
    expect(newDescriptionTextarea).toHaveValue(&apos;&apos;);
  });

  it(&apos;prevents closing when loading&apos;, async () => {
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