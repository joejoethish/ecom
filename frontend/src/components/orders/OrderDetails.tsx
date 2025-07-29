import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { useRouter } from 'next/navigation';
import Image from 'next/image';
import { fetchOrderById, cancelOrder } from '@/store/slices/orderSlice';
import { RootState, useAppDispatch } from '@/store';
import { OrderItem } from '@/types';
import { PROFILE_ROUTES, ORDER_STATUS } from '@/constants';
import { formatDate, formatCurrency } from '@/utils/formatters';
import { 
  hasTimeline, 
  hasReturnRequests, 
  hasReplacements, 
  isReturnableItem, 
  hasProductImages,
  hasAddressLine2,
  hasRefundAmount,
  hasReturnTrackingNumber,
  hasTrackingInfo,
  hasShippingDate,
  hasDeliveryDate
} from '@/utils/typeGuards';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/Button';
import { Loading } from '@/components/ui/Loading';
import OrderTrackingComponent from './OrderTracking';
import { ReturnRequestForm } from './ReturnRequestForm';

interface OrderDetailsProps {
  orderId: string;
}

export const OrderDetails: React.FC<OrderDetailsProps> = ({ orderId }) => {
  const dispatch = useAppDispatch();
  const router = useRouter();
  const { currentOrder, loading, error } = useSelector((state: RootState) => state.orders);
  const [showReturnForm, setShowReturnForm] = useState(false);
  const [selectedItem, setSelectedItem] = useState<OrderItem | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const [showCancelDialog, setShowCancelDialog] = useState(false);

  useEffect(() => {
    if (orderId) {
      dispatch(fetchOrderById(orderId));
    }
  }, [dispatch, orderId]);

  const handleCancelOrder = () => {
    if (currentOrder && cancelReason.trim()) {
      dispatch(cancelOrder(currentOrder.id));
      setShowCancelDialog(false);
    }
  };

  const handleReturnRequest = (item: OrderItem) => {
    setSelectedItem(item);
    setShowReturnForm(true);
  };

  const closeReturnForm = () => {
    setShowReturnForm(false);
    setSelectedItem(null);
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

  if (loading && !currentOrder) {
    return <Loading />;
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 text-red-700 rounded-md">
        <p>Error loading order details: {error}</p>
        <Button onClick={() => {
          dispatch(fetchOrderById(orderId));
        }}>
          Try Again
        </Button>
      </div>
    );
  }

  if (!currentOrder) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 mb-4">Order not found.</p>
        <Button onClick={() => router.push(PROFILE_ROUTES.ORDERS)}>
          Back to Orders
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-semibold">Order #{currentOrder.order_number}</h1>
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusBadgeClass(currentOrder.status)}`}>
          {currentOrder.status}
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Order Summary */}
        <Card className="md:col-span-2">
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold">Order Summary</h2>
          </div>
          <div className="p-4 space-y-4">
            <div className="flex justify-between">
              <span className="text-gray-600">Order Date</span>
              <span>{formatDate(currentOrder.created_at)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Payment Method</span>
              <span>{currentOrder.payment_method}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Payment Status</span>
              <span>{currentOrder.payment_status}</span>
            </div>
            {currentOrder.tracking_number ? (
              <div className="flex justify-between">
                <span className="text-gray-600">Tracking Number</span>
                <span>{currentOrder.tracking_number}</span>
              </div>
            ) : null}
            {currentOrder.estimated_delivery_date ? (
              <div className="flex justify-between">
                <span className="text-gray-600">Estimated Delivery</span>
                <span>{formatDate(currentOrder.estimated_delivery_date)}</span>
              </div>
            ) : null}
            {currentOrder.actual_delivery_date ? (
              <div className="flex justify-between">
                <span className="text-gray-600">Delivered On</span>
                <span>{formatDate(currentOrder.actual_delivery_date)}</span>
              </div>
            ) : null}

            <hr className="my-2" />

            <div className="flex justify-between">
              <span className="text-gray-600">Subtotal</span>
              <span>{formatCurrency(currentOrder.total_amount - currentOrder.tax_amount - currentOrder.shipping_amount + currentOrder.discount_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Shipping</span>
              <span>{formatCurrency(currentOrder.shipping_amount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Tax</span>
              <span>{formatCurrency(currentOrder.tax_amount)}</span>
            </div>
            {(currentOrder.discount_amount && currentOrder.discount_amount > 0) ? (
              <div className="flex justify-between">
                <span className="text-gray-600">Discount</span>
                <span>-{formatCurrency(currentOrder.discount_amount)}</span>
              </div>
            ) : null}
            <div className="flex justify-between font-semibold">
              <span>Total</span>
              <span>{formatCurrency(currentOrder.total_amount)}</span>
            </div>

            <div className="flex space-x-4 mt-6">
              {currentOrder.can_cancel === true && (
                <Button
                  onClick={() => setShowCancelDialog(true)}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Cancel Order
                </Button>
              )}
              {currentOrder.has_invoice === true && (
                <Button>
                  Download Invoice
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* Shipping & Billing */}
        <Card>
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold">Shipping & Billing</h2>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <h3 className="font-medium mb-2">Shipping Address</h3>
              <address className="not-italic text-gray-600">
                {currentOrder.shipping_address.first_name} {currentOrder.shipping_address.last_name}<br />
                {currentOrder.shipping_address.address_line_1}<br />
                {hasAddressLine2(currentOrder.shipping_address) && (
                  <>{currentOrder.shipping_address.address_line_2}<br /></>
                )}
                {currentOrder.shipping_address.city}, {currentOrder.shipping_address.state} {currentOrder.shipping_address.postal_code}<br />
                {currentOrder.shipping_address.country}
              </address>
            </div>

            <div>
              <h3 className="font-medium mb-2">Billing Address</h3>
              <address className="not-italic text-gray-600">
                {currentOrder.billing_address.first_name} {currentOrder.billing_address.last_name}<br />
                {currentOrder.billing_address.address_line_1}<br />
                {hasAddressLine2(currentOrder.billing_address) && (
                  <>{currentOrder.billing_address.address_line_2}<br /></>
                )}
                {currentOrder.billing_address.city}, {currentOrder.billing_address.state} {currentOrder.billing_address.postal_code}<br />
                {currentOrder.billing_address.country}
              </address>
            </div>
          </div>
        </Card>
      </div>

      {/* Order Items */}
      <Card>
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold">Order Items</h2>
        </div>
        <div className="divide-y divide-gray-200">
          {currentOrder.items.map((item) => (
            <div key={item.id} className="p-4 flex flex-col md:flex-row md:items-center">
              <div className="flex items-center flex-grow mb-4 md:mb-0">
                <div className="w-16 h-16 relative flex-shrink-0">
                  {hasProductImages(item.product) ? (
                    <Image
                      src={item.product.images[0].image}
                      alt={item.product.name}
                      fill
                      className="object-cover rounded"
                    />
                  ) : (
                    <div className="w-full h-full bg-gray-200 rounded flex items-center justify-center">
                      <span className="text-gray-500 text-xs">No image</span>
                    </div>
                  )}
                </div>
                <div className="ml-4">
                  <h3 className="font-medium">{item.product.name}</h3>
                  <div className="text-sm text-gray-500">
                    <span>Qty: {item.quantity}</span>
                    {item.returned_quantity && item.returned_quantity > 0 ? (
                      <span className="ml-2 text-red-600">
                        (Returned: {item.returned_quantity})
                      </span>
                    ) : null}
                  </div>
                  <div className="text-sm text-gray-500">
                    <span>Status: {item.status}</span>
                  </div>
                </div>
              </div>
              <div className="flex flex-col md:items-end">
                <span className="font-medium">{formatCurrency(item.total_price)}</span>
                <span className="text-sm text-gray-500">
                  {formatCurrency(item.unit_price)} each
                </span>
                {isReturnableItem(item) && (
                  <Button
                    onClick={() => handleReturnRequest(item)}
                    className="mt-2 text-sm py-1"
                  >
                    Return Item
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Order Timeline */}
      <Card>
        <div className="p-4 border-b border-gray-200">
          <h2 className="font-semibold">Order Timeline</h2>
        </div>
        <div className="p-4">
          <OrderTrackingComponent orderId={currentOrder.id} />
        </div>
      </Card>

      {/* Return Requests */}
      {hasReturnRequests(currentOrder) && (
        <Card>
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold">Return Requests</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {currentOrder.return_requests.map((request) => (
              <div key={request.id} className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-medium">{request.product_name}</h3>
                    <p className="text-sm text-gray-500">
                      Quantity: {request.quantity} | Reason: {request.reason}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${request.status === 'approved' ? 'bg-green-100 text-green-800' :
                    request.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      request.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                        'bg-yellow-100 text-yellow-800'
                    }`}>
                    {request.status}
                  </span>
                </div>
                <p className="text-sm">{request.description}</p>
                {hasRefundAmount(request) && (
                  <p className="text-sm mt-2">
                    Refund Amount: {formatCurrency(request.refund_amount)}
                  </p>
                )}
                {hasReturnTrackingNumber(request) && (
                  <p className="text-sm mt-2">
                    Tracking Number: {request.return_tracking_number}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Replacements */}
      {hasReplacements(currentOrder) && (
        <Card>
          <div className="p-4 border-b border-gray-200">
            <h2 className="font-semibold">Replacements</h2>
          </div>
          <div className="divide-y divide-gray-200">
            {currentOrder.replacements.map((replacement) => (
              <div key={replacement.id} className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h3 className="font-medium">
                      {replacement.product_name} → {replacement.replacement_product_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      Quantity: {replacement.quantity}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${replacement.status === 'approved' ? 'bg-green-100 text-green-800' :
                    replacement.status === 'rejected' ? 'bg-red-100 text-red-800' :
                      replacement.status === 'shipped' ? 'bg-blue-100 text-blue-800' :
                        replacement.status === 'delivered' ? 'bg-indigo-100 text-indigo-800' :
                          'bg-yellow-100 text-yellow-800'
                    }`}>
                    {replacement.status}
                  </span>
                </div>
                {hasTrackingInfo(replacement) && (
                  <p className="text-sm mt-2">
                    Tracking Number: {replacement.tracking_number}
                  </p>
                )}
                {hasShippingDate(replacement) && (
                  <p className="text-sm mt-2">
                    Shipped Date: {formatDate(replacement.shipped_date!)}
                  </p>
                )}
                {hasDeliveryDate(replacement) && (
                  <p className="text-sm mt-2">
                    Delivered Date: {formatDate(replacement.delivered_date!)}
                  </p>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Return Request Form Modal */}
      {showReturnForm && selectedItem && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-semibold mb-4">Return Request</h2>
            <ReturnRequestForm
              orderItem={selectedItem}
              onClose={closeReturnForm}
            />
          </div>
        </div>
      )}

      {/* Cancel Order Dialog */}
      {showCancelDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h2 className="text-xl font-semibold mb-4">Cancel Order</h2>
            <p className="mb-4">Are you sure you want to cancel this order? This action cannot be undone.</p>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reason for Cancellation
              </label>
              <textarea
                className="w-full border border-gray-300 rounded-md p-2"
                rows={3}
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="Please provide a reason for cancellation"
              />
            </div>
            <div className="flex justify-end space-x-3">
              <Button
                onClick={() => setShowCancelDialog(false)}
                className="bg-gray-200 hover:bg-gray-300 text-gray-800"
              >
                Cancel
              </Button>
              <Button
                onClick={handleCancelOrder}
                className="bg-red-600 hover:bg-red-700"
                disabled={!cancelReason.trim()}
              >
                Confirm Cancellation
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};