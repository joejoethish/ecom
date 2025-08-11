import React, { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { getWalletDetails } from '@/store/slices/paymentSlice';

interface WalletPaymentProps {
  amount: number;
  onProceed: () => void;
}

const WalletPayment: React.FC<WalletPaymentProps> = ({ amount, onProceed }) => {
  const dispatch = useAppDispatch();
  const { wallet, loading, error } = useSelector((state: RootState) => state.payments);

  useEffect(() => {
    dispatch(getWalletDetails());
  }, [dispatch]);

  const handleProceed = () => {
    onProceed();
  };

  const hasSufficientBalance = wallet && wallet.balance >= amount;

  if (loading) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-4 py-1">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-lg">
        <p>Error loading wallet: {error}</p>
        <button 
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          onClick={() => dispatch(getWalletDetails())}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!wallet) {
    return (
      <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg">
        <p>You don't have a wallet yet. A wallet will be created for you when you proceed.</p>
        <button 
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          onClick={handleProceed}
        >
          Proceed with Payment
        </button>
      </div>
    );
  }

  return (
    <div className="wallet-payment p-4 border rounded-lg">
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-lg font-medium">Your Wallet</h4>
        <div className="text-right">
          <div className="text-sm text-gray-500">Available Balance</div>
          <div className="text-xl font-bold">
            {wallet.currency.symbol}{wallet.balance.toFixed(2)} {wallet.currency.code}
          </div>
        </div>
      </div>

      <div className="mb-4 p-3 bg-gray-50 rounded-md">
        <div className="flex justify-between">
          <span>Payment Amount:</span>
          <span className="font-medium">{wallet.currency.symbol}{amount.toFixed(2)}</span>
        </div>
        <div className="flex justify-between mt-2">
          <span>Balance After Payment:</span>
          <span className={`font-medium ${hasSufficientBalance ? 'text-green-600' : 'text-red-600'}`}>
            {wallet.currency.symbol}{Math.max(0, wallet.balance - amount).toFixed(2)}
          </span>
        </div>
      </div>

      {!hasSufficientBalance && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
          <p>Insufficient wallet balance. Please add funds or choose another payment method.</p>
        </div>
      )}

      <button 
        className={`w-full py-2 rounded-md transition-colors ${
          hasSufficientBalance 
            ? 'bg-blue-600 text-white hover:bg-blue-700' 
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
        onClick={handleProceed}
        disabled={!hasSufficientBalance}
      >
        {hasSufficientBalance ? 'Pay from Wallet' : 'Insufficient Balance'}
      </button>
    </div>
  );
};

export default WalletPayment;