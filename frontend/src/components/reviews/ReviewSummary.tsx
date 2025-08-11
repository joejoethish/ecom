import React from 'react';
import { Star, CheckCircle } from 'lucide-react';
import StarRating from '../ui/StarRating';
import { ProductReviewSummary } from '../../types';

interface ReviewSummaryProps {
  summary: ProductReviewSummary;
  onRatingFilter?: (rating: number | undefined) => void;
  selectedRating?: number;
  className?: string;
}

  summary,
  onRatingFilter,
  selectedRating,
  className = &apos;&apos;,
}) => {
  const ratingLabels = {
    5: &apos;Excellent&apos;,
    4: &apos;Very Good&apos;,
    3: &apos;Good&apos;,
    2: &apos;Fair&apos;,
    1: &apos;Poor&apos;,
  };

  const handleRatingClick = (rating: number) => {
    if (onRatingFilter) {
      // Toggle filter: if same rating is clicked, clear filter
      onRatingFilter(selectedRating === rating ? undefined : rating);
    }
  };

  return (
    <div className={`bg-white border border-gray-200 rounded-lg p-6 ${className}`}>
      <h3 className="text-lg font-semibold mb-4">Customer Reviews</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Overall Rating */}
        <div className="text-center lg:text-left">
          <div className="flex flex-col lg:flex-row lg:items-center gap-4">
            <div className="text-center">
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {summary.average_rating.toFixed(1)}
              </div>
              <StarRating 
                rating={summary.average_rating} 
                size="lg" 
                className="justify-center lg:justify-start mb-2"
              />
              <p className="text-sm text-gray-600">
                Based on {summary.total_reviews.toLocaleString()} review{summary.total_reviews !== 1 ? &apos;s&apos; : &apos;&apos;}
              </p>
            </div>
            
            {/* Verified Purchase Percentage */}
            <div className="text-center lg:text-left">
              <div className="flex items-center justify-center lg:justify-start gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="text-sm font-medium text-gray-900">
                  {summary.verified_purchase_percentage.toFixed(0)}% Verified Purchases
                </span>
              </div>
              <p className="text-xs text-gray-600">
                Reviews from customers who purchased this item
              </p>
            </div>
          </div>
        </div>

        {/* Rating Distribution */}
        <div className="space-y-2">
          {[5, 4, 3, 2, 1].map((rating) => {
            const count = summary.rating_distribution[rating] || 0;
            const percentage = summary.total_reviews > 0 ? (count / summary.total_reviews) * 100 : 0;
            const isSelected = selectedRating === rating;
            
            return (
              <button
                key={rating}
                onClick={() => handleRatingClick(rating)}
                className={`w-full flex items-center gap-3 p-2 rounded-md transition-colors ${
                  onRatingFilter 
                    ? `hover:bg-gray-50 ${isSelected ? &apos;bg-blue-50 border border-blue-200&apos; : &apos;&apos;}` 
                    : &apos;&apos;
                }`}
                disabled={!onRatingFilter}
              >
                <div className="flex items-center gap-1 min-w-[80px]">
                  <span className="text-sm font-medium">{rating}</span>
                  <Star className="w-4 h-4 text-yellow-400 fill-current" />
                </div>
                
                <div className="flex-1 flex items-center gap-3">
                  {/* Progress Bar */}
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-300 ${
                        isSelected ? 'bg-blue-500' : 'bg-yellow-400'
                      }`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                  
                  {/* Count and Percentage */}
                  <div className="text-sm text-gray-600 min-w-[60px] text-right">
                    <span className="font-medium">{count.toLocaleString()}</span>
                    <span className="text-xs ml-1">({percentage.toFixed(0)}%)</span>
                  </div>
                </div>
                
                {/* Rating Label */}
                <div className="text-xs text-gray-500 min-w-[60px] text-right">
                  {ratingLabels[rating as keyof typeof ratingLabels]}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Filter Indicator */}
      {selectedRating && onRatingFilter && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-sm text-blue-800">
                Showing {selectedRating}-star reviews only
              </span>
            </div>
            <button
              onClick={() => onRatingFilter(undefined)}
              className=&quot;text-sm text-blue-600 hover:text-blue-800 transition-colors&quot;
            >
              Show all reviews
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewSummary;