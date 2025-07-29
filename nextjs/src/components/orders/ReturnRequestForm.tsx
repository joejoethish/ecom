import React, { useState } from 'react';
import { useSelector } from 'react-redux';
import { createReturnRequest } from '@/store/slices/orderSlice';
import { RootState, useAppDispatch } from '@/store';
import { OrderItem, RETURN_REASON_OPTIONS } from '@/types';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';

interface ReturnRequestFormProps {
  orderItem: OrderItem;
  onClose: () => void;
}

export const ReturnRequestForm: React.FC<ReturnRequestFormProps> = ({ orderItem, onClose }) => {
  const dispatch = useAppDispatch();
  const { returnRequestLoading, returnRequestError } = useSelector((state: RootState) => state.orders);
  
  const [quantity, setQuantity] = useState(1);
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const maxReturnQuantity = orderItem.quantity - (orderItem.returned_quantity || 0);

  const validateForm = () => {
    const newErrors: Record<string, string> = {};
    
    if (quantity <= 0 || quantity > maxReturnQuantity) {
      newErrors.quantity = `Quantity must be between 1 and ${maxReturnQuantity}`;
    }
    
    if (!reason) {
      newErrors.reason = 'Please select a reason for return';
    }
    
    if (!description.trim()) {
      newErrors.description = 'Please provide a description';
    } else if (description.trim().length < 10) {
      newErrors.description = 'Description must be at least 10 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    dispatch(createReturnRequest({
      order_item_id: orderItem.id,
      quantity,
      reason,
      description
    }) as any).then((result: any) => {
      if (!result.error) {
        onClose();
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Product
        </label>
        <div className="text-gray-900">{orderItem.product.name}</div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Quantity to Return
        </label>
        <select
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          className={`block w-full border ${errors.quantity ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm p-2`}
        >
          {Array.from({ length: maxReturnQuantity }, (_, i) => i + 1).map((num) => (
            <option key={num} value={num}>
              {num}
            </option>
          ))}
        </select>
        {errors.quantity && (
          <p className="mt-1 text-sm text-red-600">{errors.quantity}</p>
        )}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Reason for Return
        </label>
        <select
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          className={`block w-full border ${errors.reason ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm p-2`}
        >
          <option value="">Select a reason</option>
          {RETURN_REASON_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.reason && (
          <p className="mt-1 text-sm text-red-600">{errors.reason}</p>
        )}
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className={`block w-full border ${errors.description ? 'border-red-500' : 'border-gray-300'} rounded-md shadow-sm p-2`}
          placeholder="Please provide details about the return reason"
        />
        {errors.description && (
          <p className="mt-1 text-sm text-red-600">{errors.description}</p>
        )}
      </div>
      
      {returnRequestError && (
        <div className="p-3 bg-red-50 text-red-700 rounded-md">
          {returnRequestError}
        </div>
      )}
      
      <div className="flex justify-end space-x-3 pt-2">
        <Button
          type="button"
          onClick={onClose}
          className="bg-gray-200 hover:bg-gray-300 text-gray-800"
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={returnRequestLoading}
        >
          {returnRequestLoading ? <Loading size="sm" /> : 'Submit Return Request'}
        </Button>
      </div>
    </form>
  );
};