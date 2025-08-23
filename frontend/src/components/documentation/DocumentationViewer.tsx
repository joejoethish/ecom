'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Eye, 
  Heart, 
  Bookmark, 
  Share2, 
  MessageSquare, 
  Star, 
  Clock, 
  User, 
  Tag, 
  Edit,
  History,
  Download,
  Printer,
  Flag
} from 'lucide-react';

interface DocumentationData {
  id: string;
  title: string;
  content: string;
  excerpt: string;
  category: {
    id: string;
    name: string;
    slug: string;
  };
  author: {
    id: string;
    username: string;
    first_name: string;
    last_name: string;
  };
  tags: Array<{
    id: string;
    name: string;
    slug: string;
    color: string;
  }>;
  status: string;
  visibility: string;
  version: string;
  view_count: number;
  like_count: number;
  average_rating: number;
  total_feedback: number;
  is_bookmarked: boolean;
  published_at: string;
  created_at: string;
  updated_at: string;
  comments: Comment[];
  translations: Translation[];
}

interface Comment {
  id: string;
  author: {
    username: string;
    first_name: string;
    last_name: string;
  };
  content: string;
  created_at: string;
  replies: Comment[];
}

interface Translation {
  id: string;
  language: string;
  title: string;
  is_approved: boolean;
}

interface DocumentationViewerProps {
  documentId: string;
  onEdit?: () => void;
}

const DocumentationViewer: React.FC<DocumentationViewerProps> = ({
  documentId,
  onEdit
}) => {
  const [document, setDocument] = useState<DocumentationData | null>(null);
  const [loading, setLoading] = useState(true);
  const [showComments, setShowComments] = useState(false);
  const [showToc] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [rating, setRating] = useState(0);
  const [feedback, setFeedback] = useState('');
  const [isLiked, setIsLiked] = useState(false);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [tocItems, setTocItems] = useState<Array<{ id: string; text: string; level: number }>>([]);
  const [activeSection, setActiveSection] = useState('');

  const fetchDocument = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/documentation/documents/${documentId}/`);
      const data = await response.json();
      setDocument(data);
      setIsBookmarked(data.is_bookmarked);
    } catch (error) {
      console.error('Error fetching document:', error);
    } finally {
      setLoading(false);
    }
  }, [documentId]);

  const generateToc = useCallback(() => {
    if (!document) return;

    const parser = new DOMParser();
    const doc = parser.parseFromString(document.content, 'text/html');
    const headings = doc.querySelectorAll('h1, h2, h3, h4, h5, h6');
    
    const items = Array.from(headings).map((heading, index) => {
      const id = `heading-${index}`;
      heading.id = id;
      return {
        id,
        text: heading.textContent || '',
        level: parseInt(heading.tagName.charAt(1))
      };
    });

    setTocItems(items);
  }, [document]);

  const updateActiveSection = useCallback(() => {
    if (typeof window === 'undefined' || !window.document) return;
    
    const headings = window.document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let current = '';

    headings.forEach((heading) => {
      const rect = heading.getBoundingClientRect();
      if (rect.top <= 100) {
        current = heading.id;
      }
    });

    setActiveSection(current);
  }, []);

  const trackView = useCallback(async () => {
    try {
      await fetch(`/api/documentation/analytics/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          documentation: documentId,
          event_type: 'view',
          event_data: {
            timestamp: new Date().toISOString(),
            user_agent: navigator.userAgent
          }
        })
      });
    } catch (error) {
      console.error('Error tracking view:', error);
    }
  }, [documentId]);

  useEffect(() => {
    fetchDocument();
  }, [fetchDocument]);

  useEffect(() => {
    if (document) {
      generateToc();
      trackView();
    }
  }, [document, generateToc, trackView]);

  useEffect(() => {
    const handleScroll = () => {
      updateActiveSection();
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [updateActiveSection]);

  const handleLike = async () => {
    try {
      const response = await fetch(`/api/documentation/documents/${documentId}/like/`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setIsLiked(!isLiked);
        if (document) {
          setDocument(prev => prev ? {
            ...prev,
            like_count: isLiked ? prev.like_count - 1 : prev.like_count + 1
          } : null);
        }
      }
    } catch (error) {
      console.error('Error liking document:', error);
    }
  };

  const handleBookmark = async () => {
    try {
      const response = await fetch(`/api/documentation/documents/${documentId}/bookmark/`, {
        method: 'POST'
      });
      
      if (response.ok) {
        setIsBookmarked(!isBookmarked);
      }
    } catch (error) {
      console.error('Error bookmarking document:', error);
    }
  };

  const handleShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: document?.title,
          text: document?.excerpt,
          url: typeof window !== 'undefined' ? window.location.href : ''
        });
      } catch (error) {
        console.error('Error sharing:', error);
      }
    } else {
      // Fallback: copy to clipboard
      if (typeof window !== 'undefined') {
        navigator.clipboard.writeText(window.location.href);
      }
    }
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;

    try {
      const response = await fetch(`/api/documentation/documents/${documentId}/add_comment/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newComment
        })
      });

      if (response.ok) {
        const comment = await response.json();
        setDocument(prev => prev ? {
          ...prev,
          comments: [...prev.comments, comment]
        } : null);
        setNewComment('');
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
    }
  };

  const submitFeedback = async () => {
    if (!rating) return;

    try {
      const response = await fetch(`/api/documentation/documents/${documentId}/submit_feedback/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          rating,
          comment: feedback,
          is_helpful: rating >= 4
        })
      });

      if (response.ok) {
        setRating(0);
        setFeedback('');
        // Refresh document to get updated rating
        fetchDocument();
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    }
  };

  const scrollToSection = (id: string) => {
    const element = window.document?.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Document not found</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex gap-8">
        {/* Table of Contents */}
        {showToc && tocItems.length > 0 && (
          <div className="hidden lg:block w-64 flex-shrink-0">
            <div className="sticky top-8">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="font-semibold text-gray-900 mb-4">Table of Contents</h3>
                <nav className="space-y-1">
                  {tocItems.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => scrollToSection(item.id)}
                      className={`block w-full text-left text-sm py-1 px-2 rounded hover:bg-gray-100 ${
                        activeSection === item.id ? 'bg-blue-50 text-blue-600' : 'text-gray-600'
                      }`}
                      style={{ paddingLeft: `${(item.level - 1) * 12 + 8}px` }}
                    >
                      {item.text}
                    </button>
                  ))}
                </nav>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <h1 className="text-3xl font-bold text-gray-900 mb-2">{document.title}</h1>
                <p className="text-gray-600 mb-4">{document.excerpt}</p>
                
                {/* Metadata */}
                <div className="flex items-center space-x-4 text-sm text-gray-500 mb-4">
                  <div className="flex items-center">
                    <User className="w-4 h-4 mr-1" />
                    {document.author.first_name} {document.author.last_name}
                  </div>
                  <div className="flex items-center">
                    <Clock className="w-4 h-4 mr-1" />
                    {new Date(document.updated_at).toLocaleDateString()}
                  </div>
                  <div className="flex items-center">
                    <Eye className="w-4 h-4 mr-1" />
                    {document.view_count} views
                  </div>
                  <div className="flex items-center">
                    <Star className="w-4 h-4 mr-1 text-yellow-500" />
                    {document.average_rating.toFixed(1)} ({document.total_feedback} reviews)
                  </div>
                </div>

                {/* Tags */}
                {document.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mb-4">
                    {document.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                        style={{ backgroundColor: tag.color + '20', color: tag.color }}
                      >
                        <Tag className="w-3 h-3 mr-1" />
                        {tag.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center space-x-2 ml-4">
                <button
                  onClick={handleLike}
                  className={`p-2 rounded-lg border ${
                    isLiked ? 'bg-red-50 border-red-200 text-red-600' : 'bg-white border-gray-200 text-gray-600'
                  } hover:bg-gray-50`}
                >
                  <Heart className={`w-5 h-5 ${isLiked ? 'fill-current' : ''}`} />
                </button>
                <button
                  onClick={handleBookmark}
                  className={`p-2 rounded-lg border ${
                    isBookmarked ? 'bg-blue-50 border-blue-200 text-blue-600' : 'bg-white border-gray-200 text-gray-600'
                  } hover:bg-gray-50`}
                >
                  <Bookmark className={`w-5 h-5 ${isBookmarked ? 'fill-current' : ''}`} />
                </button>
                <button
                  onClick={handleShare}
                  className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
                >
                  <Share2 className="w-5 h-5" />
                </button>
                {onEdit && (
                  <button
                    onClick={onEdit}
                    className="p-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50"
                  >
                    <Edit className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <div 
              className="prose max-w-none"
              dangerouslySetInnerHTML={{ __html: document.content }}
            />
          </div>

          {/* Feedback Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Rate this document</h3>
            <div className="flex items-center space-x-4 mb-4">
              <div className="flex items-center space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRating(star)}
                    className={`p-1 ${
                      star <= rating ? 'text-yellow-500' : 'text-gray-300'
                    } hover:text-yellow-500`}
                  >
                    <Star className="w-6 h-6 fill-current" />
                  </button>
                ))}
              </div>
              <span className="text-sm text-gray-600">
                {rating > 0 && `${rating} star${rating !== 1 ? 's' : ''}`}
              </span>
            </div>
            <textarea
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Share your feedback (optional)..."
              className="w-full h-20 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-4"
            />
            <button
              onClick={submitFeedback}
              disabled={!rating}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              Submit Feedback
            </button>
          </div>

          {/* Comments Section */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">
                Comments ({document.comments.length})
              </h3>
              <button
                onClick={() => setShowComments(!showComments)}
                className="text-blue-600 hover:text-blue-700"
              >
                {showComments ? 'Hide' : 'Show'} Comments
              </button>
            </div>

            {showComments && (
              <div className="space-y-4">
                {/* Add Comment */}
                <div className="border-b border-gray-200 pb-4">
                  <textarea
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="w-full h-20 p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent mb-2"
                  />
                  <button
                    onClick={submitComment}
                    disabled={!newComment.trim()}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    <MessageSquare className="w-4 h-4 inline mr-2" />
                    Add Comment
                  </button>
                </div>

                {/* Comments List */}
                <div className="space-y-4">
                  {document.comments.map((comment) => (
                    <div key={comment.id} className="border-l-2 border-gray-200 pl-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-medium text-gray-900">
                          {comment.author.first_name} {comment.author.last_name}
                        </span>
                        <span className="text-sm text-gray-500">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-gray-700">{comment.content}</p>
                      
                      {/* Replies */}
                      {comment.replies.length > 0 && (
                        <div className="mt-3 ml-4 space-y-2">
                          {comment.replies.map((reply) => (
                            <div key={reply.id} className="border-l-2 border-gray-100 pl-3">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="font-medium text-gray-900 text-sm">
                                  {reply.author.first_name} {reply.author.last_name}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {new Date(reply.created_at).toLocaleDateString()}
                                </span>
                              </div>
                              <p className="text-gray-700 text-sm">{reply.content}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="hidden xl:block w-80 flex-shrink-0">
          <div className="sticky top-8 space-y-6">
            {/* Document Info */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Document Info</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Category:</span>
                  <span className="text-gray-900">{document.category.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Version:</span>
                  <span className="text-gray-900">{document.version}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Status:</span>
                  <span className="text-gray-900 capitalize">{document.status}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Created:</span>
                  <span className="text-gray-900">
                    {new Date(document.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>

            {/* Translations */}
            {document.translations.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="font-semibold text-gray-900 mb-3">Available Translations</h3>
                <div className="space-y-2">
                  {document.translations.map((translation) => (
                    <button
                      key={translation.id}
                      className="block w-full text-left p-2 rounded hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-900">
                          {translation.language.toUpperCase()}
                        </span>
                        {translation.is_approved && (
                          <span className="text-xs text-green-600">Approved</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="font-semibold text-gray-900 mb-3">Quick Actions</h3>
              <div className="space-y-2">
                <button className="w-full flex items-center p-2 text-left text-sm text-gray-600 hover:bg-gray-50 rounded">
                  <Download className="w-4 h-4 mr-2" />
                  Download PDF
                </button>
                <button className="w-full flex items-center p-2 text-left text-sm text-gray-600 hover:bg-gray-50 rounded">
                  <Printer className="w-4 h-4 mr-2" />
                  Print
                </button>
                <button className="w-full flex items-center p-2 text-left text-sm text-gray-600 hover:bg-gray-50 rounded">
                  <History className="w-4 h-4 mr-2" />
                  View History
                </button>
                <button className="w-full flex items-center p-2 text-left text-sm text-gray-600 hover:bg-gray-50 rounded">
                  <Flag className="w-4 h-4 mr-2" />
                  Report Issue
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DocumentationViewer;