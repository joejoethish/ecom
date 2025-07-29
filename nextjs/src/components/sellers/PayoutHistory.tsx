import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { AppDispatch, RootState } from '../../store';
import { fetchPayoutHistory } from '../../store/slices/sellerSlice';

const PayoutHistory: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { payouts, loading, error } = useSelector((state: RootState) => state.seller);

  useEffect(() => {
    dispatch(fetchPayoutHistory());
  }, [dispatch]);

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      case 'PROCESSING':
        return 'bg-yellow-100 text-yellow-800';
      case 'PENDING':
        return 'bg-gray-100 text-gray-800';
      case 'FAILED':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-semibold mb-6">Payout History</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="bg-white shadow-md rounded-lg p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-medium">Your Payouts</h3>
        </div>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
          </div>
        ) : payouts.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500">No payout history available.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Transaction ID
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Fee
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {payouts.map((payout) => (
                  <tr key={payout.id}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{payout.transaction_id}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">₹{payout.amount.toLocaleString()}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">₹{payout.transaction_fee.toLocaleString()}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusClass(payout.status)}`}>
                        {payout.status_display}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(payout.payout_date).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      <div className="bg-white shadow-md rounded-lg p-6 mt-8">
        <h3 className="text-lg font-medium mb-4">Payout Information</h3>
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row md:justify-between md:items-center p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium">Payout Schedule</h4>
              <p className="text-sm text-gray-600">Payouts are processed every 7 days</p>
            </div>
            <div className="mt-2 md:mt-0">
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">Weekly</span>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row md:justify-between md:items-center p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium">Transaction Fee</h4>
              <p className="text-sm text-gray-600">Fee charged on each payout</p>
            </div>
            <div className="mt-2 md:mt-0">
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">2%</span>
            </div>
          </div>
          
          <div className="flex flex-col md:flex-row md:justify-between md:items-center p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium">Minimum Payout Amount</h4>
              <p className="text-sm text-gray-600">Minimum balance required for payout</p>
            </div>
            <div className="mt-2 md:mt-0">
              <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">₹1,000</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PayoutHistory;