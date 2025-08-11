import { apiClient } from '../utils/api';
import {
  Review,
  ReviewCreateData,
  ReviewUpdateData,
  ReviewHelpfulnessVote,
  ReviewReport,
  ReviewAnalytics,
  ProductReviewSummary,
  ModerationStats,
  ReviewFilters,
  ApiResponse,
  PaginatedResponse
} from '../types';



export const reviewApi = {
  // Review CRUD operations
  getReviews: async (filters?: ReviewFilters): Promise<ApiResponse<PaginatedResponse<Review>>> => {
    const queryParams = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get<PaginatedResponse<Review>>(`/reviews/?${queryParams.toString()}`);
  },

  getReview: async (id: string): Promise<ApiResponse<Review>> => {
    return apiClient.get<Review>(`/reviews/${id}/`);
  },

  createReview: async (data: ReviewCreateData): Promise<ApiResponse<Review>> => {
    const formData = new FormData();
    
    // Add basic review data
    formData.append('product', data.product);
    formData.append('rating', data.rating.toString());
    formData.append('title', data.title);
    formData.append('comment', data.comment);
    
    if (data.pros) formData.append('pros', data.pros);
    if (data.cons) formData.append('cons', data.cons);
    
    // Add images if provided
    if (data.images && data.images.length > 0) {
      data.images.forEach((image, index) => {
        formData.append(`images[${index}]image`, image);
        formData.append(`images[${index}]sort_order`, index.toString());
      });
    }

    return apiClient.post<Review>('/reviews/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  updateReview: async (id: string, data: ReviewUpdateData): Promise<ApiResponse<Review>> => {
    const formData = new FormData();
    
    if (data.rating !== undefined) formData.append('rating', data.rating.toString());
    if (data.title !== undefined) formData.append('title', data.title);
    if (data.comment !== undefined) formData.append('comment', data.comment);
    if (data.pros !== undefined) formData.append('pros', data.pros);
    if (data.cons !== undefined) formData.append('cons', data.cons);
    
    // Add images if provided
    if (data.images && data.images.length > 0) {
      data.images.forEach((image, index) => {
        formData.append(`images[${index}]image`, image);
        formData.append(`images[${index}]sort_order`, index.toString());
      });
    }

    return apiClient.patch<Review>(`/reviews/${id}/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  deleteReview: async (id: string): Promise<ApiResponse<void>> => {
    return apiClient.delete<void>(`/reviews/${id}/`);
  },

  // Product-specific reviews
  getProductReviews: async (productId: string, filters?: {
    rating?: number;
    verified_only?: boolean;
    ordering?: string;
  }): Promise<ApiResponse<PaginatedResponse<Review>>> => {
    const queryParams = new URLSearchParams();
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get<PaginatedResponse<Review>>(`/products/${productId}/reviews/?${queryParams.toString()}`);
  },

  getProductReviewSummary: (productId: string): Promise<ApiResponse<ProductReviewSummary>> => {
    return apiClient.get(`/products/${productId}/reviews/summary/`);
  },

  // Review helpfulness voting
  voteReviewHelpfulness: (reviewId: string, vote: 'helpful' | 'not_helpful'): Promise<ApiResponse<ReviewHelpfulnessVote>> => {
    return apiClient.post(`/reviews/${reviewId}/vote_helpful/`, { vote });
  },

  // Review reporting
  reportReview: (reviewId: string, data: {
    reason: 'spam' | 'inappropriate' | 'fake' | 'offensive' | 'irrelevant' | 'other';
    description?: string;
  }): Promise<ApiResponse<ReviewReport>> => {
    return apiClient.post(`/reviews/${reviewId}/report/`, data);
  },

  // Review moderation (admin only)
  moderateReview: (reviewId: string, data: {
    action: 'approve' | 'reject' | 'flag';
    notes?: string;
  }): Promise<ApiResponse<Review>> => {
    return apiClient.post(`/reviews/${reviewId}/moderate/`, data);
  },

  bulkModerateReviews: (data: {
    review_ids: string[];
    action: 'approve' | 'reject' | 'flag';
    notes?: string;
  }): Promise<ApiResponse<{ message: string; updated_count: number }>> => {
    return apiClient.post('/reviews/bulk_moderate/', data);
  },

  // Analytics
  getReviewAnalytics: (params?: {
    product?: string;
    user?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<ApiResponse<ReviewAnalytics>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/reviews/analytics/?${queryParams.toString()}`);
  },

  // Moderation dashboard (admin only)
  getModerationDashboard: (): Promise<ApiResponse<{
    stats: ModerationStats;
    pending_reviews: { results: Review[]; count: number };
    flagged_reviews: { results: Review[]; count: number };
    reported_reviews: { results: ReviewReport[]; count: number };
  }>> => {
    return apiClient.get('/reviews/moderation/dashboard/');
  },

  // Review reports management (admin only)
  getReviewReports: (params?: {
    status?: string;
    reason?: string;
  }): Promise<ApiResponse<PaginatedResponse<ReviewReport>>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/review-reports/?${queryParams.toString()}`);
  },

  resolveReviewReport: (reportId: string, data: {
    action: 'resolve' | 'dismiss';
    notes?: string;
  }): Promise<ApiResponse<ReviewReport>> => {
    return apiClient.post(`/review-reports/${reportId}/resolve/`, data);
  },
};