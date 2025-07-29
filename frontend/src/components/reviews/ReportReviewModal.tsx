import React, { useState } from 'react';
import { X, Flag, AlertCircle } from 'lucide-react';

interface ReportReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: { reason: string; description: string }) => Promise<void>;
  loading?: boolean;
  error?: string;
}

const ReportReviewModal: React.FC<ReportReviewModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  loading = false,
  error,
}) => {
  const [formData, setFormData] = useState({
    reason: '',
    description: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const reportReasons = [
    { value: 'spam', label: 'Spam or fake review' },
    { value: 'inappropriate', label: 'Inappropriate content' },
    { value: 'offensive', label: 'Offensive language' },
    { value: 'fake', label: 'Fake or misleading review' },
    { value: 'irrelevant', label: 'Not relevant to the product' },
    { value: 'other', label: 'Other reason' },
  ];

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.reason) {
      newErrors.reason = 'Please select a reason for reporting';
    }

    if (!formData.description.trim()) {
      newErrors.description = 'Please provide additional details';
    } else if (formData.description.length < 10) {
      newErrors.description = 'Description should be at least 10 characters long';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await onSubmit(formData);
      // Reset form on success
      setFormData({ reason: '', description: '' });
      setErrors({});
      onClose();
    } catch (err) {
      // Error handling is done by parent component
    }
  };

  const handleClose = () => {
    if (!loading) {
      setFormData({ reason: '', description: '' });
      setErrors({});
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <Flag className="w-5 h-5 text-red-500" />
            <h2 className="text-lg font-semibold text-gray-900">Report Review</h2>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-1 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2 text-red-700">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          <p className="text-sm text-gray-600 mb-4">
            Help us maintain a safe and helpful community by reporting reviews that violate our guidelines.
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Reason Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Why are you reporting this review? *
              </label>
              <div className="space-y-2">
                {reportReasons.map((reason) => (
                  <label key={reason.value} className="flex items-center gap-3">
                    <input
                      type="radio"
                      name="reason"
                      value={reason.value}
                      checked={formData.reason === reason.value}
                      onChange={(e) => handleInputChange('reason', e.target.value)}
                      className="text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">{reason.label}</span>
                  </label>
                ))}
              </div>
              {errors.reason && (
                <p className="text-red-500 text-xs mt-1">{errors.reason}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                Additional details *
              </label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => handleInputChange('description', e.target.value)}
                placeholder="Please provide more details about why you're reporting this review..."
                rows={4}
                className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical ${
                  errors.description ? 'border-red-500' : 'border-gray-300'
                }`}
                maxLength={500}
              />
              <div className="flex justify-between items-center mt-1">
                {errors.description && (
                  <p className="text-red-500 text-xs">{errors.description}</p>
                )}
                <p className="text-xs text-gray-500 ml-auto">
                  {formData.description.length}/500
                </p>
              </div>
            </div>

            {/* Submit Buttons */}
            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={handleClose}
                disabled={loading}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Reporting...' : 'Report Review'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ReportReviewModal;