import React, { useState } from 'react';
import { Camera, X, AlertCircle } from 'lucide-react';
import StarRating from '../ui/StarRating';
import { ReviewCreateData, ReviewUpdateData, Review } from '../../types';

interface ReviewFormProps {
  productId: string;
  existingReview?: Review;
  onSubmit: (data: ReviewCreateData | ReviewUpdateData) => Promise<void>;
  onCancel?: () => void;
  loading?: boolean;
  error?: string;
}

const ReviewForm: React.FC<ReviewFormProps> = ({
  productId,
  existingReview,
  onSubmit,
  onCancel,
  loading = false,
  error,
}) => {
  const [formData, setFormData] = useState({
    rating: existingReview?.rating || 0,
    title: existingReview?.title || '',
    comment: existingReview?.comment || '',
    pros: existingReview?.pros || '',
    cons: existingReview?.cons || '',
  });
  
  const [images, setImages] = useState<File[]>([]);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    const maxImages = 5;
    
    if (images.length + files.length > maxImages) {
      setErrors(prev => ({ 
        ...prev, 
        images: `You can upload a maximum of ${maxImages} images` 
      }));
      return;
    }

    // Validate file types and sizes
    const validFiles: File[] = [];
    const validPreviews: string[] = [];

    files.forEach(file => {
      if (!file.type.startsWith('image/')) {
        setErrors(prev => ({ 
          ...prev, 
          images: 'Only image files are allowed' 
        }));
        return;
      }

      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setErrors(prev => ({ 
          ...prev, 
          images: 'Image size should be less than 5MB' 
        }));
        return;
      }

      validFiles.push(file);
      validPreviews.push(URL.createObjectURL(file));
    });

    setImages(prev => [...prev, ...validFiles]);
    setImagePreviews(prev => [...prev, ...validPreviews]);
    setErrors(prev => ({ ...prev, images: '' }));
  };

  const removeImage = (index: number) => {
    URL.revokeObjectURL(imagePreviews[index]);
    setImages(prev => prev.filter((_, i) => i !== index));
    setImagePreviews(prev => prev.filter((_, i) => i !== index));
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (formData.rating === 0) {
      newErrors.rating = 'Please select a rating';
    }

    if (!formData.title.trim()) {
      newErrors.title = 'Review title is required';
    } else if (formData.title.length < 5) {
      newErrors.title = 'Title should be at least 5 characters long';
    }

    if (!formData.comment.trim()) {
      newErrors.comment = 'Review comment is required';
    } else if (formData.comment.length < 10) {
      newErrors.comment = 'Comment should be at least 10 characters long';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    const submitData = existingReview 
      ? {
          ...formData,
          images: images.length > 0 ? images : undefined,
        } as ReviewUpdateData
      : {
          product: productId,
          ...formData,
          images: images.length > 0 ? images : undefined,
        } as ReviewCreateData;

    try {
      await onSubmit(submitData);
    } catch (err) {
      // Error handling is done by parent component
    }
  };

  React.useEffect(() => {
    // Cleanup image previews on unmount
    return () => {
      imagePreviews.forEach(preview => URL.revokeObjectURL(preview));
    };
  }, []);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4">
        {existingReview ? 'Edit Your Review' : 'Write a Review'}
      </h3>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md flex items-center gap-2 text-red-700">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Rating */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Rating *
          </label>
          <StarRating
            rating={formData.rating}
            interactive
            onRatingChange={(rating) => handleInputChange('rating', rating)}
            size="lg"
            className="mb-1"
          />
          {errors.rating && (
            <p className="text-red-500 text-xs mt-1">{errors.rating}</p>
          )}
        </div>

        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Review Title *
          </label>
          <input
            type="text"
            id="title"
            value={formData.title}
            onChange={(e) => handleInputChange('title', e.target.value)}
            placeholder="Summarize your review in a few words"
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              errors.title ? 'border-red-500' : 'border-gray-300'
            }`}
            maxLength={200}
          />
          {errors.title && (
            <p className="text-red-500 text-xs mt-1">{errors.title}</p>
          )}
        </div>

        {/* Comment */}
        <div>
          <label htmlFor="comment" className="block text-sm font-medium text-gray-700 mb-1">
            Review Comment *
          </label>
          <textarea
            id="comment"
            value={formData.comment}
            onChange={(e) => handleInputChange('comment', e.target.value)}
            placeholder="Share your experience with this product"
            rows={4}
            className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical ${
              errors.comment ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.comment && (
            <p className="text-red-500 text-xs mt-1">{errors.comment}</p>
          )}
        </div>

        {/* Pros */}
        <div>
          <label htmlFor="pros" className="block text-sm font-medium text-gray-700 mb-1">
            What did you like? (Optional)
          </label>
          <textarea
            id="pros"
            value={formData.pros}
            onChange={(e) => handleInputChange('pros', e.target.value)}
            placeholder="What were the positive aspects?"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
          />
        </div>

        {/* Cons */}
        <div>
          <label htmlFor="cons" className="block text-sm font-medium text-gray-700 mb-1">
            What could be improved? (Optional)
          </label>
          <textarea
            id="cons"
            value={formData.cons}
            onChange={(e) => handleInputChange('cons', e.target.value)}
            placeholder="What were the areas for improvement?"
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-vertical"
          />
        </div>

        {/* Image Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Add Photos (Optional)
          </label>
          
          {/* Image Previews */}
          {imagePreviews.length > 0 && (
            <div className="grid grid-cols-3 gap-2 mb-3">
              {imagePreviews.map((preview, index) => (
                <div key={index} className="relative">
                  <img
                    src={preview}
                    alt={`Preview ${index + 1}`}
                    className="w-full h-20 object-cover rounded-md border"
                  />
                  <button
                    type="button"
                    onClick={() => removeImage(index)}
                    className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition-colors"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Upload Button */}
          {images.length < 5 && (
            <label className="flex items-center justify-center w-full h-20 border-2 border-dashed border-gray-300 rounded-md cursor-pointer hover:border-gray-400 transition-colors">
              <div className="flex flex-col items-center">
                <Camera className="w-6 h-6 text-gray-400 mb-1" />
                <span className="text-sm text-gray-500">Add Photos</span>
              </div>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
              />
            </label>
          )}
          
          {errors.images && (
            <p className="text-red-500 text-xs mt-1">{errors.images}</p>
          )}
          <p className="text-xs text-gray-500 mt-1">
            You can upload up to 5 images. Max size: 5MB per image.
          </p>
        </div>

        {/* Submit Buttons */}
        <div className="flex gap-3 pt-4">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Submitting...' : existingReview ? 'Update Review' : 'Submit Review'}
          </button>
          
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={loading}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default ReviewForm;