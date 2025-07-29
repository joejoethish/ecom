import React, { useState } from 'react';
import {
    ThumbsUp,
    ThumbsDown,
    Flag,
    MoreVertical,
    Edit,
    Trash2,
    CheckCircle,
    AlertTriangle
} from 'lucide-react';
import StarRating from '../ui/StarRating';
import { Review } from '../../types';
// Simple date formatting utility
const formatDistanceToNow = (date: Date): string => {
  const now = new Date();
  const diffInMs = now.getTime() - date.getTime();
  const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
  const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));
  
  if (diffInMinutes < 1) return 'just now';
  if (diffInMinutes < 60) return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
  if (diffInHours < 24) return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
  if (diffInDays < 30) return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
  
  return date.toLocaleDateString();
};

interface ReviewCardProps {
    review: Review;
    onVoteHelpful?: (reviewId: string, vote: 'helpful' | 'not_helpful') => Promise<void>;
    onReport?: (reviewId: string) => void;
    onEdit?: (review: Review) => void;
    onDelete?: (reviewId: string) => Promise<void>;
    onModerate?: (reviewId: string, action: 'approve' | 'reject' | 'flag') => Promise<void>;
    currentUserId?: string;
    showModerationActions?: boolean;
    loading?: boolean;
}

const ReviewCard: React.FC<ReviewCardProps> = ({
    review,
    onVoteHelpful,
    onReport,
    onEdit,
    onDelete,
    onModerate,
    currentUserId,
    showModerationActions = false,
    loading = false,
}) => {
    const [showDropdown, setShowDropdown] = useState(false);
    const [votingLoading, setVotingLoading] = useState(false);
    const [moderationLoading, setModerationLoading] = useState(false);

    const isOwnReview = currentUserId === review.user.id;
    const canEdit = isOwnReview && review.status === 'pending';

    const handleVote = async (vote: 'helpful' | 'not_helpful') => {
        if (!onVoteHelpful || votingLoading) return;

        setVotingLoading(true);
        try {
            await onVoteHelpful(review.id, vote);
        } catch (error) {
            console.error('Error voting on review:', error);
        } finally {
            setVotingLoading(false);
        }
    };

    const handleModerate = async (action: 'approve' | 'reject' | 'flag') => {
        if (!onModerate || moderationLoading) return;

        setModerationLoading(true);
        try {
            await onModerate(review.id, action);
        } catch (error) {
            console.error('Error moderating review:', error);
        } finally {
            setModerationLoading(false);
        }
    };

    const getStatusBadge = () => {
        switch (review.status) {
            case 'pending':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded-full">
                        <AlertTriangle className="w-3 h-3" />
                        Pending Review
                    </span>
                );
            case 'approved':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                        <CheckCircle className="w-3 h-3" />
                        Approved
                    </span>
                );
            case 'rejected':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-red-100 text-red-800 rounded-full">
                        <AlertTriangle className="w-3 h-3" />
                        Rejected
                    </span>
                );
            case 'flagged':
                return (
                    <span className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-orange-100 text-orange-800 rounded-full">
                        <Flag className="w-3 h-3" />
                        Flagged
                    </span>
                );
            default:
                return null;
        }
    };

    return (
        <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                        {review.user.avatar_url ? (
                            <img
                                src={review.user.avatar_url}
                                alt={review.user.full_name}
                                className="w-10 h-10 rounded-full object-cover"
                            />
                        ) : (
                            <span className="text-sm font-medium text-gray-600">
                                {review.user.full_name.charAt(0).toUpperCase()}
                            </span>
                        )}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h4 className="font-medium text-gray-900">{review.user.full_name}</h4>
                            {review.is_verified_purchase && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs bg-green-100 text-green-800 rounded-full">
                                    <CheckCircle className="w-3 h-3" />
                                    Verified Purchase
                                </span>
                            )}
                        </div>
                        <div className="flex items-center gap-2 mt-1">
                            <StarRating rating={review.rating} size="sm" />
                            <span className="text-sm text-gray-500">
                                {formatDistanceToNow(new Date(review.created_at))}
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    {getStatusBadge()}

                    {/* Actions Dropdown */}
                    <div className="relative">
                        <button
                            onClick={() => setShowDropdown(!showDropdown)}
                            className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                        >
                            <MoreVertical className="w-4 h-4 text-gray-500" />
                        </button>

                        {showDropdown && (
                            <div className="absolute right-0 top-8 bg-white border border-gray-200 rounded-md shadow-lg z-10 min-w-[120px]">
                                {canEdit && onEdit && (
                                    <button
                                        onClick={() => {
                                            onEdit(review);
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                                    >
                                        <Edit className="w-4 h-4" />
                                        Edit
                                    </button>
                                )}

                                {isOwnReview && onDelete && (
                                    <button
                                        onClick={() => {
                                            onDelete(review.id);
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2 text-red-600"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                        Delete
                                    </button>
                                )}

                                {!isOwnReview && onReport && (
                                    <button
                                        onClick={() => {
                                            onReport(review.id);
                                            setShowDropdown(false);
                                        }}
                                        className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 flex items-center gap-2"
                                    >
                                        <Flag className="w-4 h-4" />
                                        Report
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Review Content */}
            <div className="mb-4">
                <h5 className="font-medium text-gray-900 mb-2">{review.title}</h5>
                <p className="text-gray-700 leading-relaxed">{review.comment}</p>

                {/* Pros and Cons */}
                {(review.pros || review.cons) && (
                    <div className="mt-3 space-y-2">
                        {review.pros && (
                            <div>
                                <span className="text-sm font-medium text-green-700">Pros: </span>
                                <span className="text-sm text-gray-700">{review.pros}</span>
                            </div>
                        )}
                        {review.cons && (
                            <div>
                                <span className="text-sm font-medium text-red-700">Cons: </span>
                                <span className="text-sm text-gray-700">{review.cons}</span>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Review Images */}
            {review.images && review.images.length > 0 && (
                <div className="mb-4">
                    <div className="grid grid-cols-3 gap-2">
                        {review.images.slice(0, 3).map((image, index) => (
                            <img
                                key={image.id}
                                src={image.image}
                                alt={image.caption || `Review image ${index + 1}`}
                                className="w-full h-20 object-cover rounded-md border cursor-pointer hover:opacity-80 transition-opacity"
                                onClick={() => {
                                    // TODO: Implement image modal/lightbox
                                }}
                            />
                        ))}
                        {review.images.length > 3 && (
                            <div className="w-full h-20 bg-gray-100 rounded-md border flex items-center justify-center text-sm text-gray-600">
                                +{review.images.length - 3} more
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* Footer */}
            <div className="flex items-center justify-between pt-3 border-t border-gray-100">
                {/* Helpfulness Voting */}
                {!isOwnReview && onVoteHelpful && (
                    <div className="flex items-center gap-4">
                        <span className="text-sm text-gray-600">Was this helpful?</span>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => handleVote('helpful')}
                                disabled={votingLoading}
                                className={`flex items-center gap-1 px-2 py-1 text-sm rounded-md transition-colors ${review.user_vote === 'helpful'
                                        ? 'bg-green-100 text-green-700'
                                        : 'hover:bg-gray-100 text-gray-600'
                                    } disabled:opacity-50`}
                            >
                                <ThumbsUp className="w-4 h-4" />
                                <span>{review.helpful_count}</span>
                            </button>

                            <button
                                onClick={() => handleVote('not_helpful')}
                                disabled={votingLoading}
                                className={`flex items-center gap-1 px-2 py-1 text-sm rounded-md transition-colors ${review.user_vote === 'not_helpful'
                                        ? 'bg-red-100 text-red-700'
                                        : 'hover:bg-gray-100 text-gray-600'
                                    } disabled:opacity-50`}
                            >
                                <ThumbsDown className="w-4 h-4" />
                                <span>{review.not_helpful_count}</span>
                            </button>
                        </div>
                    </div>
                )}

                {/* Moderation Actions */}
                {showModerationActions && review.can_moderate && onModerate && (
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => handleModerate('approve')}
                            disabled={moderationLoading}
                            className="px-3 py-1 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200 disabled:opacity-50 transition-colors"
                        >
                            Approve
                        </button>
                        <button
                            onClick={() => handleModerate('reject')}
                            disabled={moderationLoading}
                            className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded-md hover:bg-red-200 disabled:opacity-50 transition-colors"
                        >
                            Reject
                        </button>
                        <button
                            onClick={() => handleModerate('flag')}
                            disabled={moderationLoading}
                            className="px-3 py-1 text-sm bg-orange-100 text-orange-700 rounded-md hover:bg-orange-200 disabled:opacity-50 transition-colors"
                        >
                            Flag
                        </button>
                    </div>
                )}

                {/* Helpfulness Score */}
                {review.helpfulness_score > 0 && (
                    <div className="text-sm text-gray-500">
                        {review.helpfulness_score}% found this helpful
                    </div>
                )}
            </div>

            {/* Click outside to close dropdown */}
            {showDropdown && (
                <div
                    className="fixed inset-0 z-5"
                    onClick={() => setShowDropdown(false)}
                />
            )}
        </div>
    );
};

export default ReviewCard;