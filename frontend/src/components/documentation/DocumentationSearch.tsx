'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Filter, 
  Grid, 
  List, 
  Tag, 
  Eye, 
  Heart, 
  Star,
  BookOpen,
  X,
  ChevronDown
} from 'lucide-react';
import { debounce } from 'lodash';

interface SearchFilters {
  query: string;
  category: string;
  tags: string[];
  author: string;
  status: string;
  visibility: string;
  dateRange: {
    start: string;
    end: string;
  };
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

interface SearchResult {
  id: string;
  title: string;
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
  view_count: number;
  like_count: number;
  average_rating: number;
  created_at: string;
  updated_at: string;
}

interface Category {
  id: string;
  name: string;
  slug: string;
}

interface Tag {
  id: string;
  name: string;
  slug: string;
}

interface DocumentationSearchProps {
  initialQuery?: string;
  onResultClick?: (result: SearchResult) => void;
}

const DocumentationSearch: React.FC<DocumentationSearchProps> = ({
  initialQuery = '',
  onResultClick
}) => {
  const [filters, setFilters] = useState<SearchFilters>({
    query: initialQuery,
    category: '',
    tags: [],
    author: '',
    status: '',
    visibility: '',
    dateRange: {
      start: '',
      end: ''
    },
    sortBy: 'updated_at',
    sortOrder: 'desc'
  });

  const [results, setResults] = useState<SearchResult[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalResults, setTotalResults] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('list');
  const [showFilters, setShowFilters] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  const pageSize = 20;

  useEffect(() => {
    fetchInitialData();
  }, []);

  const searchDocuments = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      
      if (filters.query) params.append('search', filters.query);
      if (filters.category) params.append('category', filters.category);
      if (filters.tags.length > 0) params.append('tags', filters.tags.join(','));
      if (filters.author) params.append('author', filters.author);
      if (filters.status) params.append('status', filters.status);
      if (filters.visibility) params.append('visibility', filters.visibility);
      if (filters.dateRange.start) params.append('created_after', filters.dateRange.start);
      if (filters.dateRange.end) params.append('created_before', filters.dateRange.end);
      
      const ordering = filters.sortOrder === 'desc' ? `-${filters.sortBy}` : filters.sortBy;
      params.append('ordering', ordering);
      params.append('page', currentPage.toString());
      params.append('page_size', pageSize.toString());

      const response = await fetch(`/api/documentation/documents/?${params}`);
      const data = await response.json();
      
      setResults(data.results || []);
      setTotalResults(data.count || 0);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = useCallback(() => {
    const timeoutId = setTimeout(() => {
      searchDocuments();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [searchDocuments]);

  useEffect(() => {
    if (filters.query || Object.values(filters).some(v => 
      Array.isArray(v) ? v.length > 0 : v !== '' && v !== 'updated_at' && v !== 'desc'
    )) {
      debouncedSearch();
    }
  }, [filters, currentPage, debouncedSearch]);

  const fetchInitialData = async () => {
    try {
      const [categoriesRes, tagsRes] = await Promise.all([
        fetch('/api/documentation/categories/'),
        fetch('/api/documentation/tags/')
      ]);

      const [categoriesData, tagsData] = await Promise.all([
        categoriesRes.json(),
        tagsRes.json()
      ]);

      setCategories(categoriesData.results || []);
      setTags(tagsData.results || []);
    } catch (error) {
      console.error('Error fetching initial data:', error);
    }
  };

  const searchDocuments = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      
      if (filters.query) params.append('search', filters.query);
      if (filters.category) params.append('category', filters.category);
      if (filters.tags.length > 0) params.append('tags', filters.tags.join(','));
      if (filters.author) params.append('author', filters.author);
      if (filters.status) params.append('status', filters.status);
      if (filters.visibility) params.append('visibility', filters.visibility);
      if (filters.dateRange.start) params.append('created_after', filters.dateRange.start);
      if (filters.dateRange.end) params.append('created_before', filters.dateRange.end);
      
      const ordering = filters.sortOrder === 'desc' ? `-${filters.sortBy}` : filters.sortBy;
      params.append('ordering', ordering);
      params.append('page', currentPage.toString());
      params.append('page_size', pageSize.toString());

      const response = await fetch(`/api/documentation/documents/?${params}`);
      const data = await response.json();
      
      setResults(data.results || []);
      setTotalResults(data.count || 0);
    } catch (error) {
      console.error('Error searching documents:', error);
    } finally {
      setLoading(false);
    }
  };

  const debouncedSearch = useCallback(
    debounce(searchDocuments, 300),
    [filters, currentPage]
  );

  const fetchSearchSuggestions = async (query: string) => {
    if (!query || query.length < 2) {
      setSearchSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`/api/documentation/search/suggestions/?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      setSearchSuggestions(data.suggestions || []);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  };

  const debouncedSuggestions = useCallback((query: string) => {
    const timeoutId = setTimeout(() => {
      fetchSearchSuggestions(query);
    }, 200);
    return () => clearTimeout(timeoutId);
  }, []);

  const handleQueryChange = (query: string) => {
    setFilters(prev => ({ ...prev, query }));
    debouncedSuggestions(query);
    setShowSuggestions(true);
  };

  const handleFilterChange = (key: keyof SearchFilters, value: string | string[]) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1);
  };



  const removeTag = (tagId: string) => {
    handleFilterChange('tags', filters.tags.filter(id => id !== tagId));
  };

  const clearFilters = () => {
    setFilters({
      query: '',
      category: '',
      tags: [],
      author: '',
      status: '',
      visibility: '',
      dateRange: { start: '', end: '' },
      sortBy: 'updated_at',
      sortOrder: 'desc'
    });
    setCurrentPage(1);
  };

  const getSelectedTagNames = () => {
    return filters.tags.map(tagId => {
      const tag = tags.find(t => t.id === tagId);
      return tag ? tag.name : tagId;
    });
  };

  const ResultCard: React.FC<{ result: SearchResult; mode: 'grid' | 'list' }> = ({ result, mode }) => {
    const cardClass = mode === 'grid' 
      ? 'bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow cursor-pointer'
      : 'bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer flex items-start space-x-4';

    return (
      <div 
        className={cardClass}
        onClick={() => onResultClick?.(result)}
      >
        {mode === 'grid' ? (
          <div>
            <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{result.title}</h3>
            <p className="text-gray-600 text-sm mb-3 line-clamp-3">{result.excerpt}</p>
            
            <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
              <span>{result.category.name}</span>
              <span>{new Date(result.updated_at).toLocaleDateString()}</span>
            </div>

            {result.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-3">
                {result.tags.slice(0, 3).map(tag => (
                  <span
                    key={tag.id}
                    className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                    style={{ backgroundColor: tag.color + '20', color: tag.color }}
                  >
                    {tag.name}
                  </span>
                ))}
                {result.tags.length > 3 && (
                  <span className="text-xs text-gray-500">+{result.tags.length - 3} more</span>
                )}
              </div>
            )}

            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3 text-xs text-gray-500">
                <div className="flex items-center">
                  <Eye className="w-3 h-3 mr-1" />
                  {result.view_count}
                </div>
                <div className="flex items-center">
                  <Heart className="w-3 h-3 mr-1" />
                  {result.like_count}
                </div>
                <div className="flex items-center">
                  <Star className="w-3 h-3 mr-1 text-yellow-500" />
                  {result.average_rating.toFixed(1)}
                </div>
              </div>
              <span className="text-xs text-gray-500">
                by {result.author.first_name} {result.author.last_name}
              </span>
            </div>
          </div>
        ) : (
          <>
            <div className="flex-1">
              <h3 className="font-semibold text-gray-900 mb-1">{result.title}</h3>
              <p className="text-gray-600 text-sm mb-2 line-clamp-2">{result.excerpt}</p>
              
              <div className="flex items-center space-x-4 text-xs text-gray-500 mb-2">
                <span>{result.category.name}</span>
                <span>by {result.author.first_name} {result.author.last_name}</span>
                <span>{new Date(result.updated_at).toLocaleDateString()}</span>
              </div>

              {result.tags.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {result.tags.slice(0, 5).map(tag => (
                    <span
                      key={tag.id}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium"
                      style={{ backgroundColor: tag.color + '20', color: tag.color }}
                    >
                      {tag.name}
                    </span>
                  ))}
                </div>
              )}
            </div>

            <div className="flex flex-col items-end space-y-2 text-xs text-gray-500">
              <div className="flex items-center space-x-3">
                <div className="flex items-center">
                  <Eye className="w-3 h-3 mr-1" />
                  {result.view_count}
                </div>
                <div className="flex items-center">
                  <Heart className="w-3 h-3 mr-1" />
                  {result.like_count}
                </div>
                <div className="flex items-center">
                  <Star className="w-3 h-3 mr-1 text-yellow-500" />
                  {result.average_rating.toFixed(1)}
                </div>
              </div>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                result.status === 'published' ? 'bg-green-100 text-green-800' :
                result.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {result.status}
              </span>
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search documentation..."
              value={filters.query}
              onChange={(e) => handleQueryChange(e.target.value)}
              onFocus={() => setShowSuggestions(true)}
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            
            {/* Search Suggestions */}
            {showSuggestions && searchSuggestions.length > 0 && (
              <div className="absolute top-full left-0 right-0 bg-white border border-gray-200 rounded-lg shadow-lg mt-1 z-10">
                {searchSuggestions.map((suggestion, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      handleQueryChange(suggestion);
                      setShowSuggestions(false);
                    }}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg"
                  >
                    <Search className="w-4 h-4 inline mr-2 text-gray-400" />
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
          
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`px-4 py-3 border rounded-lg flex items-center ${
              showFilters ? 'bg-blue-50 border-blue-200 text-blue-600' : 'bg-white border-gray-300 text-gray-600'
            } hover:bg-gray-50`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
            <ChevronDown className={`w-4 h-4 ml-2 transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
        </div>

        {/* Active Filters */}
        {(filters.category || filters.tags.length > 0 || filters.author || filters.status) && (
          <div className="flex flex-wrap gap-2 mb-4">
            {filters.category && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-blue-100 text-blue-800">
                Category: {categories.find(c => c.id === filters.category)?.name}
                <button
                  onClick={() => handleFilterChange('category', '')}
                  className="ml-2 text-blue-600 hover:text-blue-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            
            {getSelectedTagNames().map((tagName, index) => (
              <span key={index} className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-green-100 text-green-800">
                Tag: {tagName}
                <button
                  onClick={() => removeTag(filters.tags[index])}
                  className="ml-2 text-green-600 hover:text-green-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ))}
            
            {filters.status && (
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-800">
                Status: {filters.status}
                <button
                  onClick={() => handleFilterChange('status', '')}
                  className="ml-2 text-purple-600 hover:text-purple-800"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            )}
            
            <button
              onClick={clearFilters}
              className="text-sm text-gray-600 hover:text-gray-800 underline"
            >
              Clear all filters
            </button>
          </div>
        )}

        {/* Filters Panel */}
        {showFilters && (
          <div className="border-t border-gray-200 pt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={filters.category}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All categories</option>
                {categories.map(category => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All statuses</option>
                <option value="draft">Draft</option>
                <option value="review">Under Review</option>
                <option value="approved">Approved</option>
                <option value="published">Published</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sort by</label>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="updated_at">Last updated</option>
                <option value="created_at">Created date</option>
                <option value="title">Title</option>
                <option value="view_count">Views</option>
                <option value="like_count">Likes</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Order</label>
              <select
                value={filters.sortOrder}
                onChange={(e) => handleFilterChange('sortOrder', e.target.value as 'asc' | 'desc')}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Descending</option>
                <option value="asc">Ascending</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Results Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h2 className="text-lg font-semibold text-gray-900">
            {loading ? 'Searching...' : `${totalResults} results`}
          </h2>
          {filters.query && (
            <span className="text-gray-600">for &quot;{filters.query}&quot;</span>
          )}
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded ${viewMode === 'list' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
          >
            <List className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded ${viewMode === 'grid' ? 'bg-blue-100 text-blue-600' : 'text-gray-600'}`}
          >
            <Grid className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : results.length > 0 ? (
        <div className={
          viewMode === 'grid' 
            ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'
            : 'space-y-4'
        }>
          {results.map(result => (
            <ResultCard key={result.id} result={result} mode={viewMode} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <BookOpen className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No results found</h3>
          <p className="text-gray-600">Try adjusting your search terms or filters</p>
        </div>
      )}

      {/* Pagination */}
      {totalResults > pageSize && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {currentPage} of {Math.ceil(totalResults / pageSize)}
          </span>
          
          <button
            onClick={() => setCurrentPage(prev => prev + 1)}
            disabled={currentPage >= Math.ceil(totalResults / pageSize)}
            className="px-3 py-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default DocumentationSearch;