'use client';

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Badge } from '@/components/ui/Badge';
import { Card } from '@/components/ui/card';
import LoadingSpinner from '@/components/ui/LoadingSpinner';
import { ErrorBoundary, ErrorDisplay, EmptyState } from '@/components/ui/ErrorBoundary';
import { SkeletonTable } from '@/components/ui/SkeletonLoader';
import { 
  Search, 
  Download, 
  Calendar, 
  Filter, 
  Eye,
  ArrowUpDown,
  Package,
  User,
  Clock,
  FileText,
  RefreshCw
} from 'lucide-react';
import { 
  inventoryManagementApi, 
  type InventoryTransaction, 
  type TransactionFilters 
} from '@/services/inventoryManagementApi';
import { handleApiResponse, showErrorToast, showSuccessToast, debounce } from '@/utils/errorHandling';

interface TransactionHistoryProps {
  className?: string;
}

export default function TransactionHistory({ className = '' }: TransactionHistoryProps) {
  const [transactions, setTransactions] = useState<InventoryTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);
  const [selectedTransaction, setSelectedTransaction] = useState<InventoryTransaction | null>(null);
  const [showTransactionDetails, setShowTransactionDetails] = useState(false);
  const [pagination, setPagination] = useState({
    count: 0,
    next: null as string | null,
    previous: null as string | null,
    page_size: 20,
    total_pages: 0,
    current_page: 1
  });

  const [filters, setFilters] = useState<TransactionFilters>({
    date_from: '',
    date_to: '',
    product: '',
    warehouse: '',
    transaction_type: undefined,
    user: '',
    page: 1,
    page_size: 20,
    ordering: '-created_at'
  });

  const [warehouses, setWarehouses] = useState<Array<{ id: string; name: string; code: string }>>([]);

  useEffect(() => {
    fetchTransactions();
    fetchWarehouses();
  }, [filters]);

  const fetchTransactions = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await inventoryManagementApi.getTransactions(filters);
      const result = handleApiResponse(response, {
        showErrorToast: false
      });

      if (result.success && result.data) {
        setTransactions(result.data.results);
        setPagination(result.data.pagination);
      } else if (result.error) {
        setError(result.error.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to load transactions';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const response = await inventoryManagementApi.getWarehouses();
      if (response.success && response.data) {
        setWarehouses(response.data.map((w: any) => ({ 
          id: w.id, 
          name: w.name, 
          code: w.code 
        })));
      }
    } catch (error) {
      console.error('Failed to fetch warehouses:', error);
    }
  };

  const handleExportTransactions = async () => {
    try {
      setExporting(true);
      setExportError(null);
      
      const blob = await inventoryManagementApi.exportTransactions(filters);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `inventory-transactions-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      showSuccessToast('Transactions exported successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to export transactions';
      setExportError(errorMessage);
      showErrorToast(
        { type: 'unknown', message: errorMessage },
        'Failed to export transactions. Please try again.'
      );
    } finally {
      setExporting(false);
    }
  };

  const handleViewTransactionDetails = (transaction: InventoryTransaction) => {
    setSelectedTransaction(transaction);
    setShowTransactionDetails(true);
  };

  const handlePageChange = (page: number) => {
    setFilters({ ...filters, page });
  };

  const handleFilterChange = (key: keyof TransactionFilters, value: any) => {
    setFilters({ ...filters, [key]: value, page: 1 });
  };

  const clearFilters = () => {
    setFilters({
      date_from: '',
      date_to: '',
      product: '',
      warehouse: '',
      transaction_type: undefined,
      user: '',
      page: 1,
      page_size: 20,
      ordering: '-created_at'
    });
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case 'sale': return 'bg-red-100 text-red-800';
      case 'purchase': return 'bg-green-100 text-green-800';
      case 'adjustment': return 'bg-blue-100 text-blue-800';
      case 'transfer': return 'bg-purple-100 text-purple-800';
      case 'return': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getTransactionTypeIcon = (type: string) => {
    switch (type) {
      case 'sale': return '↓';
      case 'purchase': return '↑';
      case 'adjustment': return '±';
      case 'transfer': return '⇄';
      case 'return': return '↩';
      default: return '•';
    }
  };

  const formatQuantityChange = (change: number) => {
    if (change > 0) {
      return <span className="text-green-600 font-medium">+{change}</span>;
    } else if (change < 0) {
      return <span className="text-red-600 font-medium">{change}</span>;
    }
    return <span className="text-gray-600 font-medium">0</span>;
  };

  return (
    <ErrorBoundary>
      <div className={`space-y-6 ${className}`}>
        {/* Header */}
        <div className="flex flex-col gap-4 sm:items-center sm:justify-between sm:flex-row">
          <div>
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900">Transaction History</h2>
            <p className="text-sm sm:text-base text-gray-600">Track all inventory movements and changes</p>
          </div>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <Button
              variant="outline"
              onClick={fetchTransactions}
              disabled={loading}
              className="flex items-center justify-center gap-2 min-h-[44px]"
              aria-label="Refresh transaction history"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} aria-hidden="true" />
              <span className="hidden sm:inline">Refresh</span>
            </Button>
            <Button 
              onClick={handleExportTransactions}
              disabled={exporting || loading}
              className="flex items-center justify-center gap-2 min-h-[44px]"
              aria-label="Export transactions to CSV"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">{exporting ? 'Exporting...' : 'Export CSV'}</span>
              <span className="sm:hidden">{exporting ? 'Export...' : 'Export'}</span>
            </Button>
          </div>
        </div>

        {exportError && (
          <ErrorDisplay 
            error={exportError} 
            onRetry={handleExportTransactions}
          />
        )}

      {/* Filters */}
      <Card className="p-4 sm:p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label htmlFor="date-from" className="block text-sm font-medium text-gray-700 mb-2">
              Date From
            </label>
            <Input
              id="date-from"
              type="date"
              value={filters.date_from || ''}
              onChange={(e) => handleFilterChange('date_from', e.target.value)}
              className="min-h-[44px]"
              aria-label="Filter transactions from date"
            />
          </div>
          <div>
            <label htmlFor="date-to" className="block text-sm font-medium text-gray-700 mb-2">
              Date To
            </label>
            <Input
              id="date-to"
              type="date"
              value={filters.date_to || ''}
              onChange={(e) => handleFilterChange('date_to', e.target.value)}
              className="min-h-[44px]"
              aria-label="Filter transactions to date"
            />
          </div>
          <div>
            <label htmlFor="warehouse-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Warehouse
            </label>
            <Select
              id="warehouse-filter"
              value={filters.warehouse || ''}
              onChange={(e) => handleFilterChange('warehouse', e.target.value)}
              className="min-h-[44px]"
              aria-label="Filter by warehouse"
            >
              <option value="">All Warehouses</option>
              {warehouses.map((warehouse) => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.name} ({warehouse.code})
                </option>
              ))}
            </Select>
          </div>
          <div>
            <label htmlFor="transaction-type-filter" className="block text-sm font-medium text-gray-700 mb-2">
              Transaction Type
            </label>
            <Select
              id="transaction-type-filter"
              value={filters.transaction_type || ''}
              onChange={(e) => handleFilterChange('transaction_type', e.target.value)}
              className="min-h-[44px]"
              aria-label="Filter by transaction type"
            >
              <option value="">All Types</option>
              <option value="sale">Sale</option>
              <option value="purchase">Purchase</option>
              <option value="adjustment">Adjustment</option>
              <option value="transfer">Transfer</option>
              <option value="return">Return</option>
            </Select>
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4 pointer-events-none" aria-hidden="true" />
              <Input
                placeholder="Search by product name, SKU, or user..."
                value={filters.product || ''}
                onChange={(e) => handleFilterChange('product', e.target.value)}
                className="pl-10 min-h-[44px]"
                aria-label="Search transactions"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              onClick={clearFilters}
              className="min-h-[44px] flex items-center gap-2"
              aria-label="Clear all filters"
            >
              <Filter className="h-4 w-4" aria-hidden="true" />
              <span className="hidden sm:inline">Clear Filters</span>
              <span className="sm:hidden">Clear</span>
            </Button>
          </div>
        </div>
      </Card>

        {/* Transactions Table */}
        <Card>
          <div className="overflow-x-auto">
            {loading ? (
              <SkeletonTable rows={10} columns={7} className="p-6" />
            ) : error ? (
              <ErrorDisplay 
                error={error} 
                onRetry={fetchTransactions}
                className="m-6"
              />
            ) : transactions.length === 0 ? (
              <EmptyState
                icon={FileText}
                title="No transactions found"
                description="No inventory transactions match your current filters."
                className="py-12"
              />
            ) : (
            <>
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4" />
                        Date & Time
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center gap-2">
                        <Package className="h-4 w-4" />
                        Product
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center gap-2">
                        <ArrowUpDown className="h-4 w-4" />
                        Quantity Change
                      </div>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Stock Levels
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <div className="flex items-center gap-2">
                        <User className="h-4 w-4" />
                        User
                      </div>
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transactions.map((transaction) => (
                    <tr key={transaction.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {new Date(transaction.created_at).toLocaleDateString()}
                        </div>
                        <div className="text-sm text-gray-500">
                          {new Date(transaction.created_at).toLocaleTimeString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-medium text-gray-900">
                          {transaction.inventory_item.product_variant.product.name}
                        </div>
                        <div className="text-sm text-gray-500">
                          SKU: {transaction.inventory_item.product_variant.sku}
                        </div>
                        <div className="text-xs text-blue-600">
                          {transaction.inventory_item.warehouse.name}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge className={getTransactionTypeColor(transaction.transaction_type)}>
                          <span className="mr-1">{getTransactionTypeIcon(transaction.transaction_type)}</span>
                          {transaction.transaction_type.charAt(0).toUpperCase() + transaction.transaction_type.slice(1)}
                        </Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm">
                          {formatQuantityChange(transaction.quantity_change)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          <div>Before: <span className="font-medium">{transaction.previous_quantity}</span></div>
                          <div>After: <span className="font-medium">{transaction.new_quantity}</span></div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{transaction.user.username}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewTransactionDetails(transaction)}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              {pagination.total_pages > 1 && (
                <div className="px-6 py-4 border-t border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-700">
                      Showing {((pagination.current_page - 1) * pagination.page_size) + 1} to{' '}
                      {Math.min(pagination.current_page * pagination.page_size, pagination.count)} of{' '}
                      {pagination.count} results
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(pagination.current_page - 1)}
                        disabled={!pagination.previous}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePageChange(pagination.current_page + 1)}
                        disabled={!pagination.next}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                </div>
              )}
              </>
            )}
          </div>
        </Card>

      {/* Transaction Details Modal */}
      {showTransactionDetails && selectedTransaction && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Transaction Details</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowTransactionDetails(false)}
                >
                  ×
                </Button>
              </div>

              <div className="space-y-6">
                {/* Transaction Info */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Transaction ID
                    </label>
                    <p className="text-sm text-gray-900 font-mono">{selectedTransaction.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Date & Time
                    </label>
                    <p className="text-sm text-gray-900">
                      {new Date(selectedTransaction.created_at).toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Product Info */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Product Information
                  </label>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {selectedTransaction.inventory_item.product_variant.product.name}
                        </p>
                        <p className="text-sm text-gray-500">
                          SKU: {selectedTransaction.inventory_item.product_variant.sku}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-700">
                          Warehouse: {selectedTransaction.inventory_item.warehouse.name}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Transaction Details */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Transaction Type
                    </label>
                    <Badge className={getTransactionTypeColor(selectedTransaction.transaction_type)}>
                      <span className="mr-1">{getTransactionTypeIcon(selectedTransaction.transaction_type)}</span>
                      {selectedTransaction.transaction_type.charAt(0).toUpperCase() + selectedTransaction.transaction_type.slice(1)}
                    </Badge>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Quantity Change
                    </label>
                    <p className="text-sm">
                      {formatQuantityChange(selectedTransaction.quantity_change)}
                    </p>
                  </div>
                </div>

                {/* Stock Levels */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Previous Quantity
                    </label>
                    <p className="text-sm text-gray-900 font-medium">
                      {selectedTransaction.previous_quantity}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      New Quantity
                    </label>
                    <p className="text-sm text-gray-900 font-medium">
                      {selectedTransaction.new_quantity}
                    </p>
                  </div>
                </div>

                {/* User and Reason */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Performed By
                  </label>
                  <p className="text-sm text-gray-900">{selectedTransaction.user.username}</p>
                </div>

                {selectedTransaction.reason && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reason
                    </label>
                    <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-lg">
                      {selectedTransaction.reason}
                    </p>
                  </div>
                )}

                {selectedTransaction.reference_id && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Reference ID
                    </label>
                    <p className="text-sm text-gray-900 font-mono">
                      {selectedTransaction.reference_id}
                    </p>
                  </div>
                )}
              </div>

              <div className="flex justify-end mt-6">
                <Button onClick={() => setShowTransactionDetails(false)}>
                  Close
                </Button>
              </div>
            </div>
          </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}