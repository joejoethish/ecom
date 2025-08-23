'use client';

import { useState, useEffect, useMemo } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Avatar } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { Alert } from '@/components/ui/Alert';
import { User, PaginatedResponse } from '@/types';
import { formatDate } from '@/utils/format';
import { useDebounce } from '@/hooks/useDebounce';

interface UserListViewProps {
  users: PaginatedResponse<User>;
  loading?: boolean;
  error?: string | null;
  onUserSelect?: (user: User) => void;
  onUserEdit?: (user: User) => void;
  onUserDelete?: (user: User) => void;
  onCreateUser?: () => void;
  onRefresh?: () => void;
  onPageChange?: (page: number) => void;
  onSearch?: (query: string) => void;
  onFilterChange?: (filters: UserFilters) => void;
}

interface UserFilters {
  user_type?: string;
  is_verified?: boolean;
  is_email_verified?: boolean;
  is_active?: boolean;
  ordering?: string;
}

export function UserListView({
  users,
  loading = false,
  error = null,
  onUserSelect,
  onUserEdit,
  onUserDelete,
  onCreateUser,
  onRefresh,
  onPageChange,
  onSearch,
  onFilterChange,
}: UserListViewProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<UserFilters>({
    ordering: '-created_at',
  });
  const [selectedUsers, setSelectedUsers] = useState<Set<string>>(new Set());

  const debouncedSearch = useDebounce(searchQuery, 300);

  // Handle search
  useEffect(() => {
    if (onSearch) {
      onSearch(debouncedSearch);
    }
  }, [debouncedSearch, onSearch]);

  // Handle filter changes
  useEffect(() => {
    if (onFilterChange) {
      onFilterChange(filters);
    }
  }, [filters, onFilterChange]);

  const handleFilterChange = (key: keyof UserFilters, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value === '' ? undefined : value,
    }));
  };

  const handleSelectUser = (userId: string) => {
    setSelectedUsers(prev => {
      const newSet = new Set(prev);
      if (newSet.has(userId)) {
        newSet.delete(userId);
      } else {
        newSet.add(userId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedUsers.size === users.results.length) {
      setSelectedUsers(new Set());
    } else {
      setSelectedUsers(new Set(users.results.map(user => user.id)));
    }
  };

  const getUserTypeColor = (userType: string) => {
    switch (userType) {
      case 'admin':
        return 'bg-red-100 text-red-800';
      case 'seller':
        return 'bg-blue-100 text-blue-800';
      case 'customer':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (isVerified: boolean) => {
    return isVerified
      ? 'bg-green-100 text-green-800'
      : 'bg-yellow-100 text-yellow-800';
  };

  // Pagination component
  const Pagination = () => {
    const { pagination } = users;
    const totalPages = pagination.total_pages;
    const currentPage = pagination.current_page;

    if (totalPages <= 1) return null;

    const pages = [];
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

    if (endPage - startPage + 1 < maxVisiblePages) {
      startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }

    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }

    return (
      <div className="flex items-center justify-between px-6 py-3 border-t border-gray-200">
        <div className="flex items-center text-sm text-gray-500">
          Showing {((currentPage - 1) * pagination.page_size) + 1} to{' '}
          {Math.min(currentPage * pagination.page_size, pagination.count)} of{' '}
          {pagination.count} results
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(currentPage - 1)}
            disabled={!pagination.previous || loading}
          >
            Previous
          </Button>
          
          {pages.map(page => (
            <Button
              key={page}
              variant={page === currentPage ? 'primary' : 'outline'}
              size="sm"
              onClick={() => onPageChange?.(page)}
              disabled={loading}
            >
              {page}
            </Button>
          ))}
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onPageChange?.(currentPage + 1)}
            disabled={!pagination.next || loading}
          >
            Next
          </Button>
        </div>
      </div>
    );
  };

  if (error) {
    return (
      <Alert variant="destructive" className="m-6">
        <div className="flex items-center justify-between">
          <span>{error}</span>
          {onRefresh && (
            <Button variant="outline" size="sm" onClick={onRefresh}>
              Retry
            </Button>
          )}
        </div>
      </Alert>
    );
  }

  return (
    <Card className="w-full">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">User Management</h2>
            <p className="text-sm text-gray-600 mt-1">
              Manage user accounts and permissions
            </p>
          </div>
          <div className="flex space-x-3">
            {onRefresh && (
              <Button
                variant="outline"
                onClick={onRefresh}
                loading={loading}
              >
                Refresh
              </Button>
            )}
            {onCreateUser && (
              <Button
                variant="primary"
                onClick={onCreateUser}
              >
                Create User
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Input
            placeholder="Search users..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full"
          />
          
          <Select
            value={filters.user_type || ''}
            onChange={(value) => handleFilterChange('user_type', value)}
          >
            <option value="">All User Types</option>
            <option value="customer">Customer</option>
            <option value="seller">Seller</option>
            <option value="admin">Admin</option>
          </Select>
          
          <Select
            value={filters.is_verified?.toString() || ''}
            onChange={(value) => handleFilterChange('is_verified', value === 'true')}
          >
            <option value="">All Statuses</option>
            <option value="true">Verified</option>
            <option value="false">Unverified</option>
          </Select>
          
          <Select
            value={filters.ordering || ''}
            onChange={(value) => handleFilterChange('ordering', value)}
          >
            <option value="-created_at">Newest First</option>
            <option value="created_at">Oldest First</option>
            <option value="username">Username A-Z</option>
            <option value="-username">Username Z-A</option>
            <option value="email">Email A-Z</option>
            <option value="-email">Email Z-A</option>
          </Select>
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedUsers.size > 0 && (
        <div className="px-6 py-3 bg-blue-50 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-800">
              {selectedUsers.size} user{selectedUsers.size !== 1 ? 's' : ''} selected
            </span>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm">
                Export Selected
              </Button>
              <Button variant="outline" size="sm" className="text-red-600">
                Bulk Delete
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* User List */}
      <div className="overflow-x-auto">
        {loading && users.results.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={selectedUsers.size === users.results.length && users.results.length > 0}
                    onChange={handleSelectAll}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.results.map((user) => (
                <tr
                  key={user.id}
                  className={`hover:bg-gray-50 ${selectedUsers.has(user.id) ? 'bg-blue-50' : ''}`}
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <input
                      type="checkbox"
                      checked={selectedUsers.has(user.id)}
                      onChange={() => handleSelectUser(user.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <Avatar className="h-10 w-10 mr-3">
                        <div className="h-full w-full bg-gray-300 flex items-center justify-center">
                          <span className="text-gray-500 text-sm font-medium">
                            {user.username.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </Avatar>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {user.username}
                        </div>
                        <div className="text-sm text-gray-500">
                          {user.email}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Badge className={getUserTypeColor(user.user_type)}>
                      {user.user_type.charAt(0).toUpperCase() + user.user_type.slice(1)}
                    </Badge>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex flex-col space-y-1">
                      <Badge className={getStatusColor(user.is_verified)}>
                        {user.is_verified ? 'Active' : 'Inactive'}
                      </Badge>
                      {user.is_email_verified && (
                        <Badge className="bg-green-100 text-green-800 text-xs">
                          Email Verified
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(user.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      {onUserSelect && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onUserSelect(user)}
                        >
                          View
                        </Button>
                      )}
                      {onUserEdit && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onUserEdit(user)}
                        >
                          Edit
                        </Button>
                      )}
                      {onUserDelete && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onUserDelete(user)}
                          className="text-red-600 border-red-300 hover:bg-red-50"
                        >
                          Delete
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Empty State */}
      {!loading && users.results.length === 0 && (
        <div className="text-center py-12">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No users found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchQuery || Object.values(filters).some(v => v !== undefined)
              ? 'Try adjusting your search or filters.'
              : 'Get started by creating a new user.'}
          </p>
          {onCreateUser && (
            <div className="mt-6">
              <Button variant="primary" onClick={onCreateUser}>
                Create User
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Pagination */}
      <Pagination />
    </Card>
  );
}