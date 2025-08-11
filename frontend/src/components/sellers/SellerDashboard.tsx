import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { fetchSellerProfile, fetchSellerAnalytics } from '../../store/slices/sellerSlice';
import Link from 'next/link';

const SellerDashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { profile, analytics, loading } = useSelector((state: RootState) => state.seller);

  useEffect(() => {
    dispatch(fetchSellerProfile());
    dispatch(fetchSellerAnalytics());
  }, [dispatch]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-semibold mb-4">Seller Profile Not Found</h2>
        <p className="mb-6">You need to register as a seller to access the dashboard.</p>
        <Link href="/seller/register">
          <a className="bg-blue-600 text-white py-2 px-6 rounded-md hover:bg-blue-700">
            Register as Seller
          </a>
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h2 className="text-2xl font-semibold mb-2">Welcome, {profile.business_name}!</h2>
        <p className="text-gray-600">
          {profile.verification_status === 'VERIFIED' ? (
            <span className="text-green-600 font-medium">Your seller account is verified.</span>
          ) : profile.verification_status === 'PENDING' ? (
            <span className="text-yellow-600 font-medium">Your seller account is pending verification.</span>
          ) : (
            <span className="text-red-600 font-medium">Your seller account verification has issues.</span>
          )}
        </p>
      </div>

      {/* Analytics Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium mb-2">Total Sales</h3>
          <div className="flex items-baseline">
            <span className="text-3xl font-semibold">
              ₹{analytics?.total_sales.toLocaleString() || '0'}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium mb-2">Total Orders</h3>
          <div className="flex items-baseline">
            <span className="text-3xl font-semibold">
              {analytics?.total_orders || '0'}
            </span>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-gray-500 text-sm font-medium mb-2">Total Products</h3>
          <div className="flex items-baseline">
            <span className="text-3xl font-semibold">
              {analytics?.total_products || '0'}
            </span>
          </div>
        </div>
      </div>

      {/* Sales Chart */}
      <div className="bg-white rounded-lg shadow p-6 mb-8">
        <h3 className="text-lg font-medium mb-4">Sales Overview</h3>
        <div className="h-64 flex items-center justify-center">
          {analytics?.sales_by_period ? (
            <div className="w-full h-full">
              {/* This is where we would render a chart using a library like Chart.js or Recharts */}
              <div className="flex h-full items-end justify-between">
                {analytics.sales_by_period.map((item, index) => (
                  <div key={index} className="flex flex-col items-center">
                    <div 
                      className="bg-blue-500 w-12" 
                      style={{ 
                        height: `${(item.amount / Math.max(...analytics.sales_by_period.map(i => i.amount))) * 100}%`,
                        minHeight: '10px'
                      }}
                    ></div>
                    <span className="text-xs mt-2">{item.period}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-500">No sales data available</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium">Recent Orders</h3>
          </div>
          <div className="divide-y">
            {analytics?.recent_orders && analytics.recent_orders.length > 0 ? (
              analytics.recent_orders.map((order) => (
                <div key={order.id} className="px-6 py-4">
                  <div className="flex justify-between">
                    <span className="font-medium">{order.order_number}</span>
                    <span className="text-gray-600">₹{order.total_amount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </span>
                    <span className={`text-sm ${
                      order.status === 'DELIVERED' ? 'text-green-600' : 
                      order.status === 'CANCELLED' ? 'text-red-600' : 'text-yellow-600'
                    }`}>
                      {order.status}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-4 text-center text-gray-500">
                No recent orders
              </div>
            )}
          </div>
          <div className="px-6 py-3 bg-gray-50">
            <Link href="/seller/orders">
              <a className="text-sm text-blue-600 hover:text-blue-800">
                View all orders
              </a>
            </Link>
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h3 className="text-lg font-medium">Top Products</h3>
          </div>
          <div className="divide-y">
            {analytics?.top_products && analytics.top_products.length > 0 ? (
              analytics.top_products.map((product) => (
                <div key={product.id} className="px-6 py-4">
                  <div className="flex justify-between">
                    <span className="font-medium">{product.name}</span>
                    <span className="text-gray-600">₹{product.sales.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between mt-1">
                    <span className="text-sm text-gray-500">
                      {product.quantity} units sold
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="px-6 py-4 text-center text-gray-500">
                No product data available
              </div>
            )}
          </div>
          <div className="px-6 py-3 bg-gray-50">
            <Link href="/seller/products">
              <a className="text-sm text-blue-600 hover:text-blue-800">
                View all products
              </a>
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <h3 className="text-lg font-medium mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <Link href="/seller/products/add">
            <a className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <h4 className="font-medium">Add Product</h4>
              <p className="text-sm text-gray-500 mt-1">List a new product for sale</p>
            </a>
          </Link>
          
          <Link href="/seller/kyc">
            <a className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <h4 className="font-medium">KYC Verification</h4>
              <p className="text-sm text-gray-500 mt-1">Complete your verification</p>
            </a>
          </Link>
          
          <Link href="/seller/bank-accounts">
            <a className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <h4 className="font-medium">Bank Accounts</h4>
              <p className="text-sm text-gray-500 mt-1">Manage your payment methods</p>
            </a>
          </Link>
          
          <Link href="/seller/profile">
            <a className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <h4 className="font-medium">Edit Profile</h4>
              <p className="text-sm text-gray-500 mt-1">Update your business details</p>
            </a>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default SellerDashboard;