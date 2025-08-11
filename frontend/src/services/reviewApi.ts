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
    formData.append(&apos;product&apos;, data.product);
    formData.append(&apos;rating&apos;, data.rating.toString());
    formData.append(&apos;title&apos;, data.title);
    formData.append(&apos;comment&apos;, data.comment);
    
    if (data.pros) formData.append(&apos;pros&apos;, data.pros);
    if (data.cons) formData.append(&apos;cons&apos;, data.cons);
    
    // Add images if provided
    if (data.images && data.images.length > 0) {
      data.images.forEach((image, index) => {
        formData.append(`images[${index}]image`, image);
        formData.append(`images[${index}]sort_order`, index.toString());
      });
    }

    return apiClient.post<Review>(&apos;/reviews/&apos;, formData, {
      headers: {
        &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
      },
    });
  },

  updateReview: async (id: string, data: ReviewUpdateData): Promise<ApiResponse<Review>> => {
    const formData = new FormData();
    
    if (data.rating !== undefined) formData.append(&apos;rating&apos;, data.rating.toString());
    if (data.title !== undefined) formData.append(&apos;title&apos;, data.title);
    if (data.comment !== undefined) formData.append(&apos;comment&apos;, data.comment);
    if (data.pros !== undefined) formData.append(&apos;pros&apos;, data.pros);
    if (data.cons !== undefined) formData.append(&apos;cons&apos;, data.cons);
    
    // Add images if provided
    if (data.images && data.images.length > 0) {
      data.images.forEach((image, index) => {
        formData.append(`images[${index}]image`, image);
        formData.append(`images[${index}]sort_order`, index.toString());
      });
    }

    return apiClient.patch<Review>(`/reviews/${id}/`, formData, {
      headers: {
        &apos;Content-Type&apos;: &apos;multipart/form-data&apos;,
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
  voteReviewHelpfulness: (reviewId: string, vote: &apos;helpful&apos; | &apos;not_helpful&apos;): Promise<ApiResponse<ReviewHelpfulnessVote>> => {
    return apiClient.post(`/reviews/${reviewId}/vote_helpful/`, { vote });
  },

  // Review reporting
  reportReview: (reviewId: string, data: {
    reason: &apos;spam&apos; | &apos;inappropriate&apos; | &apos;fake&apos; | &apos;offensive&apos; | &apos;irrelevant&apos; | &apos;other&apos;;
    description?: string;
  }): Promise<ApiResponse<ReviewReport>> => {
    return apiClient.post(`/reviews/${reviewId}/report/`, data);
  },

  // Review moderation (admin only)
  moderateReview: (reviewId: string, data: {
    action: &apos;approve&apos; | &apos;reject&apos; | &apos;flag&apos;;
    notes?: string;
  }): Promise<ApiResponse<Review>> => {
    return apiClient.post(`/reviews/${reviewId}/moderate/`, data);
  },

  bulkModerateReviews: (data: {
    review_ids: string[];
    action: &apos;approve&apos; | &apos;reject&apos; | &apos;flag&apos;;
    notes?: string;
  }): Promise<ApiResponse<{ message: string; updated_count: number }>> => {
    return apiClient.post(&apos;/reviews/bulk_moderate/&apos;, data);
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
    return apiClient.get(&apos;/reviews/moderation/dashboard/&apos;);
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
    action: &apos;resolve&apos; | &apos;dismiss&apos;;
    notes?: string;
  }): Promise<ApiResponse<ReviewReport>> => {
    return apiClient.post(`/review-reports/${reportId}/resolve/`, data);
  },
};