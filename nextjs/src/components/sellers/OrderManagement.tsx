import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import Link from 'next/link';

// This is a placeholder component as the actual order management functionality
// would be implemented in a separate task. This component provides the UI structure.

const OrderManagement: React.FC = () => {
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [filter, setFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Mock data for demonstration
  useEffect(() => {
    const mockOrders = [
      {
        id: '1',
        order_number: 'ORD-12345',
        customer_name: 'Rahul Sharma',
        total_amount: 2499,
        items_count: 2,
        status: 'DELIVERED',
        payment_status: 'COMPLETED',
        created_at: '2023-06-15T10:30:00Z',
      },
      {
        id: '2',
        order_number: 'ORD-12346',
        customer_name: 'Priya Patel',
        total_amount: 1299,
        items_count: 1,
        status: 'PROCESSING',
        payment_status: 'COMPLETED',
        created_at: '2023-06-16T14:20:00Z',
      },
      {
        id: '3',
        order_number: 'ORD-12347',
        customer_name: 'Amit Kumar',
        total_amount: 3499,
        items_count: 3,
        status: 'SHIPPED',
        payment_status: 'COMPLETED',
        created_at: '2023-06-14T09:15:00Z',
      },
      {
        id: '4',
        order_number: 'ORD-12348',
        customer_name: 'Sneha Gupta',
        total_amount: 799,
        items_count: 1,
        status: 'PENDING',
        payment_status: 'PENDING',
        created_at: '2023-06-17T11:45:00Z',
      },
      {
        id: '5',
        order_number: 'ORD-12349',
        customer_name: 'Vikram Singh',
        total_amount: 4999,
        items_count: 2,
        status: 'CANCELLED',
        payment_status: 'REFUNDED',
        created_at: '2023-06-13T16:30:00Z',
      },
    ];

    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setOrders(mockOrders);
      setLoading(false);
    }, 500);
  }, []);

  // Filter orders based on status and search query
  const filteredOrders = orders.filter((order) => {
    const matchesFilter = filter === 'all' || order.status === filter;
    const matchesSearch = order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         order.customer_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'DELIVERED':
        return 'bg-green-100 text-green-800';
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-800';
      case 'SHIPPED':
        return 'bg-blue-100 text-blue-800';
      case 'PENDING':
        return 'bg-gray-100 text-gray-800';
      case 'CANCELLED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Order Management</h2>
      
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 space-y-4 md:space-y-0">
          <div className="flex items-center space-x-2 overflow-x-auto pb-2 md:pb-0">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'all' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
              }`}
            >
              All Orders
            </button>
            <button
              onClick={() => setFilter('PENDING')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'PENDING' ? 'bg-gray-100 text-gray-800 border-2 border-gray-300' : 'bg-gray-100 text-gray-800'
              }`}
            >
              Pending
            </button>
            <button
              onClick={() => setFilter('PROCESSING')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'PROCESSING' ? 'bg-yellow-100 text-yellow-800 border-2 border-yellow-300' : 'bg-gray-100 text-gray-800'
              }`}
            >
              Processing
            </button>
            <button
              onClick={() => setFilter('SHIPPED')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'SHIPPED' ? 'bg-blue-100 text-blue-800 border-2 border-blue-300' : 'bg-gray-100 text-gray-800'
              }`}
            >
              Shipped
            </button>
            <button
              onClick={() => setFilter('DELIVERED')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'DELIVERED' ? 'bg-green-100 text-green-800 border-2 border-green-300' : 'bg-gray-100 text-gray-800'
              }`}
            >
              Delivered
            </button>
            <button
              onClick={() => setFilter('CANCELLED')}
              className={`px-3 py-1 rounded-md whitespace-nowrap ${
                filter === 'CANCELLED' ? 'bg-red-100 text-red-800 border-2 border-red-300' : 'bg-gray-100 text-gray-800'
              }`}
            >
              Cancelled
            </button>
          </div>
          
          <div className="relative">
            <input
              type="text"
              placeholder="Search orders..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full md:w-64 border border-gray-300 rounded-md pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="absolute left-3 top-2.5 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No orders found.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Order
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredOrders.map((order) => (
                  <tr key={order.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{order.order_number}</div>
                      <div className="text-sm text-gray-500">{order.items_count} items</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{order.customer_name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">₹{order.total_amount.toLocaleString()}</div>
                      <div className="text-xs text-gray-500">{order.payment_status}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(order.status)}`}>
                        {order.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link href={order.id ? `/seller/orders/${order.id}` : '/seller/orders'}>
                        <a className="text-blue-600 hover:text-blue-900">View Details</a>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default OrderManagement;