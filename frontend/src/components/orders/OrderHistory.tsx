import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import { useAppDispatch } from '@/store';
import Link from 'next/link';
import { fetchOrders } from '@/store/slices/orderSlice';
import { RootState } from '@/store';
import { Order } from '@/types';
import { ROUTES, ORDER_STATUS } from '@/constants';
import { formatDate, formatCurrency } from '@/utils/formatters';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';

export const OrderHistory: React.FC = () => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { orders, loading, error, pagination } = useSelector((state: RootState) => state.orders);
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    dispatch(fetchOrders(currentPage) as any);
  }, [dispatch, currentPage]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case ORDER_STATUS.PENDING:
        return 'bg-yellow-100 text-yellow-800';
      case ORDER_STATUS.CONFIRMED:
        return 'bg-blue-100 text-blue-800';
      case ORDER_STATUS.PROCESSING:
        return 'bg-purple-100 text-purple-800';
      case ORDER_STATUS.SHIPPED:
        return 'bg-indigo-100 text-indigo-800';
      case ORDER_STATUS.DELIVERED:
        return 'bg-green-100 text-green-800';
      case ORDER_STATUS.CANCELLED:
        return 'bg-red-100 text-red-800';
      case ORDER_STATUS.RETURNED:
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const viewOrderDetails = (orderId: string) => {
    router.push(`/profile/orders/${orderId}`);
  };

  if (loading && orders.length === 0) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-md">
        <p>Error loading orders: {error}</p>
        <Button onClick={() => dispatch(fetchOrders(currentPage) as any)}>
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Order History</h1>
      
      {orders.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">You haven't placed any orders yet.</p>
          <Link href={ROUTES.PRODUCTS}>
            <Button>Start Shopping</Button>
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {orders.map((order: Order) => (
              <Card key={order.id} className="overflow-hidden">
                <div className="p-4 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
                  <div>
                    <span className="font-medium">Order #{order.order_number}</span>
                    <span className="text-sm text-gray-500 ml-4">
                      {formatDate(order.created_at)}
                    </span>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(order.status)}`}>
                    {order.status}
                  </span>
                </div>
                
                <div className="p-4">
                  <div className="flex justify-between items-center mb-4">
                    <div>
                      <p className="text-sm text-gray-500">Total Amount</p>
                      <p className="font-medium">{formatCurrency(order.total_amount)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Payment Status</p>
                      <p className="font-medium">{order.payment_status}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500">Items</p>
                      <p className="font-medium">{order.items?.length || 0} items</p>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={() => viewOrderDetails(order.id)}
                    className="w-full"
                  >
                    View Order Details
                  </Button>
                </div>
              </Card>
            ))}
          </div>
          
          {pagination && pagination.total_pages > 1 && (
            <div className="flex justify-center mt-6">
              <nav className="flex items-center space-x-2">
                <Button
                  disabled={currentPage === 1}
                  onClick={() => handlePageChange(currentPage - 1)}
                  className="px-3 py-1"
                >
                  Previous
                </Button>
                
                {Array.from({ length: pagination.total_pages }, (_, i) => i + 1).map((page) => (
                  <Button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-3 py-1 ${
                      currentPage === page ? 'bg-blue-600 text-white' : 'bg-gray-200'
                    }`}
                  >
                    {page}
                  </Button>
                ))}
                
                <Button
                  disabled={currentPage === pagination.total_pages}
                  onClick={() => handlePageChange(currentPage + 1)}
                  className="px-3 py-1"
                >
                  Next
                </Button>
              </nav>
            </div>
          )}
        </>
      )}
    </div>
  );
};