import React, { useState, useEffect } from 'react';
import { useSelector } from 'react-redux';
import { RootState, useAppDispatch } from '@/store';
import { OrderItem, ReturnRequest } from '@/types';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';
import { apiClient } from '@/utils/api';
import { API_ENDPOINTS } from '@/constants';

interface ReplacementRequestFormProps {
  returnRequest: ReturnRequest;
  onClose: () => void;
}

interface Product {
  id: string;
  name: string;
  price: number;
}

export const ReplacementRequestForm: React.FC<ReplacementRequestFormProps> = ({ returnRequest, onClose }) => {
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [eligibleProducts, setEligibleProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>('');
  const [quantity, setQuantity] = useState(1);
  const [notes, setNotes] = useState('');

  useEffect(() => {
    // In a real implementation, we would fetch eligible products for replacement
    // For now, we'll use mock data
    const mockProducts: Product[] = [
      { id: '1', name: 'Similar Product 1', price: 99.99 },
      { id: '2', name: 'Similar Product 2', price: 89.99 },
      { id: '3', name: 'Similar Product 3', price: 109.99 },
    ];
    
    setEligibleProducts(mockProducts);
    if (mockProducts.length > 0) {
      setSelectedProductId(mockProducts[0].id);
    }
  }, [returnRequest.id]);

  const maxQuantity = returnRequest.quantity;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!selectedProductId) {
      setError('Please select a replacement product');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, we would dispatch an action to create a replacement request
      // For now, we'll just simulate a successful request
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create replacement request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Original Product
        </label>
        <div className="text-gray-900">{returnRequest.product_name}</div>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Replacement Product
        </label>
        <select
          value={selectedProductId}
          onChange={(e) => setSelectedProductId(e.target.value)}
          className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
        >
          <option value="">Select a replacement product</option>
          {eligibleProducts.map((product) => (
            <option key={product.id} value={product.id}>
              {product.name} - ${product.price.toFixed(2)}
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Quantity
        </label>
        <select
          value={quantity}
          onChange={(e) => setQuantity(Number(e.target.value))}
          className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
        >
          {Array.from({ length: maxQuantity }, (_, i) => i + 1).map((num) => (
            <option key={num} value={num}>
              {num}
            </option>
          ))}
        </select>
      </div>
      
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Additional Notes
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={3}
          className="block w-full border border-gray-300 rounded-md shadow-sm p-2"
          placeholder="Any specific requirements for the replacement"
        />
      </div>
      
      {error && (
        <div className="p-3 bg-red-50 text-red-700 rounded-md">
          {error}
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
          disabled={loading || !selectedProductId}
        >
          {loading ? <Loading size="sm" /> : 'Request Replacement'}
        </Button>
      </div>
    </form>
  );
};