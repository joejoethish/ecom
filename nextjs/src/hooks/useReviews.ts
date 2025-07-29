import { useState, useEffect, useCallback } from 'react';
import { reviewApi } from '../services/reviewApi';
import {
  Review,
  ReviewCreateData,
  ReviewUpdateData,
  ReviewFilters,
  ProductReviewSummary,
} from '../types';

interface UseReviewsOptions {
  productId?: string;
  initialFilters?: ReviewFilters;
  autoFetch?: boolean;
}

interface UseReviewsReturn {
  // Data
  reviews: Review[];
  summary: ProductReviewSummary | null;
  totalCount: number;
  
  // Loading states
  loading: boolean;
  summaryLoading: boolean;
  actionLoading: boolean;
  
  // Error states
  error: string | null;
  summaryError: string | null;
  
  // Filters
  filters: ReviewFilters;
  setFilters: (filters: ReviewFilters) => void;
  
  // Actions
  fetchReviews: () => Promise<void>;
  fetchSummary: () => Promise<void>;
  createReview: (data: ReviewCreateData) => Promise<Review>;
  updateReview: (id: string, data: ReviewUpdateData) => Promise<Review>;
  deleteReview: (id: string) => Promise<void>;
  voteHelpful: (reviewId: string, vote: 'helpful' | 'not_helpful') => Promise<void>;
  reportReview: (reviewId: string, data: { reason: 'spam' | 'inappropriate' | 'fake' | 'offensive' | 'irrelevant' | 'other'; description: string }) => Promise<void>;
  moderateReview: (reviewId: string, action: 'approve' | 'reject' | 'flag') => Promise<void>;
  
  // Utilities
  refresh: () => Promise<void>;
  clearError: () => void;
}

export const useReviews = ({
  productId,
  initialFilters = {},
  autoFetch = true,
}: UseReviewsOptions = {}): UseReviewsReturn => {
  // State
  const [reviews, setReviews] = useState<Review[]>([]);
  const [summary, setSummary] = useState<ProductReviewSummary | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [filters, setFilters] = useState<ReviewFilters>({
    ...initialFilters,
    ...(productId && { product: productId }),
  });

  // Fetch reviews
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = productId 
        ? await reviewApi.getProductReviews(productId, filters)
        : await reviewApi.getReviews(filters);
      
      if (response.success && response.data) {
        setReviews(response.data.results);
        setTotalCount(response.data.pagination.count);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch reviews');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch reviews';
      setError(errorMessage);
      setReviews([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  }, [productId, filters]);

  // Fetch review summary
  const fetchSummary = useCallback(async () => {
    if (!productId) return;
    
    setSummaryLoading(true);
    setSummaryError(null);
    
    try {
      const response = await reviewApi.getProductReviewSummary(productId);
      
      if (response.success && response.data) {
        setSummary(response.data);
      } else {
        throw new Error(response.error?.message || 'Failed to fetch review summary');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch review summary';
      setSummaryError(errorMessage);
      setSummary(null);
    } finally {
      setSummaryLoading(false);
    }
  }, [productId]);

  // Create review
  const createReview = useCallback(async (data: ReviewCreateData): Promise<Review> => {
    setActionLoading(true);
    setError(null);
    
    try {
      const response = await reviewApi.createReview(data);
      
      if (response.success && response.data) {
        // Refresh reviews and summary after creation
        await Promise.all([fetchReviews(), fetchSummary()]);
        return response.data;
      } else {
        throw new Error(response.error?.message || 'Failed to create review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create review';
      setError(errorMessage);
      throw err;
    } finally {
      setActionLoading(false);
    }
  }, [fetchReviews, fetchSummary]);

  // Update review
  const updateReview = useCallback(async (id: string, data: ReviewUpdateData): Promise<Review> => {
    setActionLoading(true);
    setError(null);
    
    try {
      const response = await reviewApi.updateReview(id, data);
      
      if (response.success && response.data) {
        // Update the review in the local state
        setReviews(prev => prev.map(review => 
          review.id === id ? response.data! : review
        ));
        return response.data;
      } else {
        throw new Error(response.error?.message || 'Failed to update review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to update review';
      setError(errorMessage);
      throw err;
    } finally {
      setActionLoading(false);
    }
  }, []);

  // Delete review
  const deleteReview = useCallback(async (id: string): Promise<void> => {
    setActionLoading(true);
    setError(null);
    
    try {
      const response = await reviewApi.deleteReview(id);
      
      if (response.success) {
        // Remove the review from local state and refresh summary
        setReviews(prev => prev.filter(review => review.id !== id));
        setTotalCount(prev => prev - 1);
        await fetchSummary();
      } else {
        throw new Error(response.error?.message || 'Failed to delete review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete review';
      setError(errorMessage);
      throw err;
    } finally {
      setActionLoading(false);
    }
  }, [fetchSummary]);

  // Vote on review helpfulness
  const voteHelpful = useCallback(async (reviewId: string, vote: 'helpful' | 'not_helpful'): Promise<void> => {
    try {
      const response = await reviewApi.voteReviewHelpfulness(reviewId, vote);
      
      if (response.success) {
        // Update the review in local state
        setReviews(prev => prev.map(review => {
          if (review.id === reviewId) {
            const updatedReview = { ...review };
            
            // Remove previous vote counts
            if (review.user_vote === 'helpful') {
              updatedReview.helpful_count = Math.max(0, updatedReview.helpful_count - 1);
            } else if (review.user_vote === 'not_helpful') {
              updatedReview.not_helpful_count = Math.max(0, updatedReview.not_helpful_count - 1);
            }
            
            // Add new vote count
            if (vote === 'helpful') {
              updatedReview.helpful_count += 1;
            } else {
              updatedReview.not_helpful_count += 1;
            }
            
            updatedReview.user_vote = vote;
            
            // Recalculate helpfulness score
            const totalVotes = updatedReview.helpful_count + updatedReview.not_helpful_count;
            updatedReview.helpfulness_score = totalVotes > 0 
              ? Math.round((updatedReview.helpful_count / totalVotes) * 100 * 10) / 10
              : 0;
            
            return updatedReview;
          }
          return review;
        }));
      } else {
        throw new Error(response.error?.message || 'Failed to vote on review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to vote on review';
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Report review
  const reportReview = useCallback(async (reviewId: string, data: { reason: 'spam' | 'inappropriate' | 'fake' | 'offensive' | 'irrelevant' | 'other'; description: string }): Promise<void> => {
    try {
      const response = await reviewApi.reportReview(reviewId, data);
      
      if (!response.success) {
        throw new Error(response.error?.message || 'Failed to report review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to report review';
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Moderate review
  const moderateReview = useCallback(async (reviewId: string, action: 'approve' | 'reject' | 'flag'): Promise<void> => {
    try {
      const response = await reviewApi.moderateReview(reviewId, { action });
      
      if (response.success && response.data) {
        // Update the review in local state
        setReviews(prev => prev.map(review => 
          review.id === reviewId ? response.data! : review
        ));
      } else {
        throw new Error(response.error?.message || 'Failed to moderate review');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to moderate review';
      setError(errorMessage);
      throw err;
    }
  }, []);

  // Refresh all data
  const refresh = useCallback(async () => {
    await Promise.all([fetchReviews(), fetchSummary()]);
  }, [fetchReviews, fetchSummary]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
    setSummaryError(null);
  }, []);

  // Update filters
  const handleSetFilters = useCallback((newFilters: ReviewFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  }, []);

  // Effects
  useEffect(() => {
    if (autoFetch) {
      fetchReviews();
    }
  }, [fetchReviews, autoFetch]);

  useEffect(() => {
    if (autoFetch && productId) {
      fetchSummary();
    }
  }, [fetchSummary, autoFetch, productId]);

  return {
    // Data
    reviews,
    summary,
    totalCount,
    
    // Loading states
    loading,
    summaryLoading,
    actionLoading,
    
    // Error states
    error,
    summaryError,
    
    // Filters
    filters,
    setFilters: handleSetFilters,
    
    // Actions
    fetchReviews,
    fetchSummary,
    createReview,
    updateReview,
    deleteReview,
    voteHelpful,
    reportReview,
    moderateReview,
    
    // Utilities
    refresh,
    clearError,
  };
};