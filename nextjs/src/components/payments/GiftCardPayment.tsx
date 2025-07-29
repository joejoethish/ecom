import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { validateGiftCard, clearGiftCard } from '@/store/slices/paymentSlice';

interface GiftCardPaymentProps {
  amount: number;
  onProceed: (giftCardCode: string) => void;
}

const GiftCardPayment: React.FC<GiftCardPaymentProps> = ({ amount, onProceed }) => {
  const dispatch = useAppDispatch();
  const { giftCard, loading, error } = useSelector((state: RootState) => state.payments);
  const [giftCardCode, setGiftCardCode] = useState('');

  const handleValidate = () => {
    if (giftCardCode.trim()) {
      dispatch(validateGiftCard(giftCardCode.trim()));
    }
  };

  const handleProceed = () => {
    if (giftCard && giftCard.current_balance >= amount) {
      onProceed(giftCard.code);
    }
  };

  const handleClear = () => {
    dispatch(clearGiftCard());
    setGiftCardCode('');
  };

  const hasSufficientBalance = giftCard && giftCard.current_balance >= amount;

  return (
    <div className="gift-card-payment p-4 border rounded-lg">
      <h4 className="text-lg font-medium mb-4">Gift Card Payment</h4>

      {!giftCard ? (
        <div>
          <div className="mb-4">
            <label htmlFor="gift-card-code" className="block text-sm font-medium text-gray-700 mb-1">
              Enter Gift Card Code
            </label>
            <div className="flex">
              <input
                id="gift-card-code"
                type="text"
                value={giftCardCode}
                onChange={(e) => setGiftCardCode(e.target.value)}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                className="flex-grow form-input rounded-l-md border-gray-300 focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                disabled={loading}
              />
              <button
                onClick={handleValidate}
                disabled={!giftCardCode.trim() || loading}
                className={`px-4 py-2 rounded-r-md ${
                  !giftCardCode.trim() || loading
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {loading ? 'Validating...' : 'Validate'}
              </button>
            </div>
            {error && (
              <p className="mt-2 text-sm text-red-600">{error}</p>
            )}
          </div>
        </div>
      ) : (
        <div>
          <div className="mb-4 p-3 bg-green-50 rounded-md">
            <div className="flex justify-between items-center">
              <span className="text-green-700">Valid Gift Card</span>
              <button
                onClick={handleClear}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Change
              </button>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">Card Number</div>
              <div className="font-medium">{giftCard.code}</div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">Available Balance</div>
              <div className="font-bold">
                {giftCard.currency.symbol}{giftCard.current_balance.toFixed(2)} {giftCard.currency.code}
              </div>
            </div>
            <div className="mt-2">
              <div className="text-sm text-gray-500">Expires On</div>
              <div>{new Date(giftCard.expiry_date).toLocaleDateString()}</div>
            </div>
          </div>

          <div className="mb-4 p-3 bg-gray-50 rounded-md">
            <div className="flex justify-between">
              <span>Payment Amount:</span>
              <span className="font-medium">{giftCard.currency.symbol}{amount.toFixed(2)}</span>
            </div>
            <div className="flex justify-between mt-2">
              <span>Balance After Payment:</span>
              <span className={`font-medium ${hasSufficientBalance ? 'text-green-600' : 'text-red-600'}`}>
                {giftCard.currency.symbol}{Math.max(0, giftCard.current_balance - amount).toFixed(2)}
              </span>
            </div>
          </div>

          {!hasSufficientBalance && (
            <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-md">
              <p>Insufficient gift card balance. Please use another gift card or choose another payment method.</p>
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
            {hasSufficientBalance ? 'Pay with Gift Card' : 'Insufficient Balance'}
          </button>
        </div>
      )}
    </div>
  );
};

export default GiftCardPayment;