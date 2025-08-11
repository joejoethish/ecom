import React, { useState, useEffect } from 'react';
import { Filter, Star } from 'lucide-react';
import ReviewCard from './ReviewCard';
import { Review, ReviewFilters } from '../../types';

interface ReviewListProps {
  reviews: Review[];
  totalCount: number;
  loading?: boolean;
  error?: string;
  filters?: ReviewFilters;
  onFiltersChange?: (filters: ReviewFilters) => void;
  onVoteHelpful?: (reviewId: string, vote: 'helpful' | 'not_helpful') => Promise<void>;
  onReport?: (reviewId: string) => void;
  onEdit?: (review: Review) => void;
  onDelete?: (reviewId: string) => Promise<void>;
  onModerate?: (reviewId: string, action: 'approve' | 'reject' | 'flag') => Promise<void>;
  currentUserId?: string;
  showModerationActions?: boolean;
  showFilters?: boolean;
  productId?: string;
}

const ReviewList: React.FC<ReviewListProps> = ({
  reviews,
  totalCount,
  loading = false,
  error,
  filters = {},
  onFiltersChange,
  onVoteHelpful,
  onReport,
  onEdit,
  onDelete,
  onModerate,
  currentUserId,
  showModerationActions = false,
  showFilters = true,
  productId,
}) => {
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [localFilters, setLocalFilters] = useState<ReviewFilters>(filters);

  // Sorting options
  const sortOptions = [
    { value: '-helpful_count', label: 'Most Helpful' },
    { value: '-created_at', label: 'Newest First' },
    { value: 'created_at', label: 'Oldest First' },
    { value: '-rating', label: 'Highest Rating' },
    { value: 'rating', label: 'Lowest Rating' },
  ];

  // Rating filter options
  const ratingOptions = [
    { value: undefined, label: 'All Ratings' },
    { value: 5, label: '5 Stars' },
    { value: 4, label: '4 Stars' },
    { value: 3, label: '3 Stars' },
    { value: 2, label: '2 Stars' },
    { value: 1, label: '1 Star' },
  ];

  const handleFilterChange = (key: keyof ReviewFilters, value: string | number | boolean | undefined) => {
    const newFilters = { ...localFilters, [key]: value };
    setLocalFilters(newFilters);
    onFiltersChange?.(newFilters);
  };

  const clearFilters = () => {
    const clearedFilters: ReviewFilters = {
      ordering: '-helpful_count',
    };
    setLocalFilters(clearedFilters);
    onFiltersChange?.(clearedFilters);
  };

  const getActiveFilterCount = () => {
    let count = 0;
    if (localFilters.rating) count++;
    if (localFilters.verified_only) count++;
    if (localFilters.status && localFilters.status !== 'approved') count++;
    return count;
  };

  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Filters */}
      {showFilters && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-4">
              <h3 className="text-lg font-semibold">
                Reviews ({totalCount.toLocaleString()})
              </h3>
              
              <button
                onClick={() => setShowFilterPanel(!showFilterPanel)}
                className="flex items-center gap-2 px-3 py-1.5 border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              >
                <Filter className="w-4 h-4" />
                <span>Filters</span>
                {getActiveFilterCount() > 0 && (
                  <span className="bg-blue-500 text-white text-xs rounded-full px-2 py-0.5">
                    {getActiveFilterCount()}
                  </span>
                )}
              </button>
            </div>

            {/* Sort Dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Sort by:</span>
              <select
                value={localFilters.ordering || '-helpful_count'}
                onChange={(e) => handleFilterChange('ordering', e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Filter Panel */}
          {showFilterPanel && (
            <div className="border-t border-gray-200 pt-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Rating Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rating
                  </label>
                  <select
                    value={localFilters.rating || ''}
                    onChange={(e) => handleFilterChange('rating', e.target.value ? parseInt(e.target.value) : undefined)}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {ratingOptions.map((option) => (
                      <option key={option.label} value={option.value || ''}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Verified Purchase Filter */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Purchase Status
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={localFilters.verified_only || false}
                      onChange={(e) => handleFilterChange('verified_only', e.target.checked || undefined)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-700">Verified purchases only</span>
                  </label>
                </div>

                {/* Status Filter (for moderation) */}
                {showModerationActions && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Status
                    </label>
                    <select
                      value={localFilters.status || 'approved'}
                      onChange={(e) => handleFilterChange('status', e.target.value)}
                      className="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="approved">Approved</option>
                      <option value="pending">Pending</option>
                      <option value="flagged">Flagged</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                )}
              </div>

              {/* Clear Filters */}
              {getActiveFilterCount() > 0 && (
                <div className="flex justify-end">
                  <button
                    onClick={clearFilters}
                    className="text-sm text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    Clear all filters
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Reviews List */}
      <div className="space-y-4">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse">
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-10 h-10 bg-gray-300 rounded-full"></div>
                  <div className="flex-1">
                    <div className="h-4 bg-gray-300 rounded w-32 mb-2"></div>
                    <div className="h-3 bg-gray-300 rounded w-24"></div>
                  </div>
                </div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-300 rounded w-full"></div>
                  <div className="h-3 bg-gray-300 rounded w-2/3"></div>
                </div>
              </div>
            ))}
          </div>
        ) : reviews.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <Star className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No reviews yet</h3>
            <p className="text-gray-600">
              {productId 
                ? "Be the first to review this product!" 
                : "No reviews match your current filters."
              }
            </p>
            {getActiveFilterCount() > 0 && (
              <button
                onClick={clearFilters}
                className="mt-4 text-blue-600 hover:text-blue-800 transition-colors"
              >
                Clear filters to see all reviews
              </button>
            )}
          </div>
        ) : (
          reviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              onVoteHelpful={onVoteHelpful}
              onReport={onReport}
              onEdit={onEdit}
              onDelete={onDelete}
              onModerate={onModerate}
              currentUserId={currentUserId}
              showModerationActions={showModerationActions}
            />
          ))
        )}
      </div>

      {/* Load More / Pagination could be added here */}
    </div>
  );
};

export default ReviewList;