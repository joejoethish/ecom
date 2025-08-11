/**
 * Type guards for conditional rendering and property access
 */
import { Order, OrderItem, ReturnRequest, Replacement, Address, Product, ApiResponse } from '@/types';
/**
 * Type guard to check if an error is an AxiosError
 */
export const isAxiosError = (error: unknown): error is any => {
  return !!(error && typeof error === 'object' && 'response' in error && 'request' in error);
};

/**
 * Type guard to check if an error has a response
 */
export const hasErrorResponse = (error: any): error is any => {
  return !!error.response;
};

/**
 * Type guard to check if an error has request data
 */
export const hasErrorRequest = (error: any): error is any => {
  return !!error.request;
};

/**
 * Type guard to check if an API response is successful
 */
export const isSuccessfulApiResponse = <T>(response: ApiResponse<T>): response is ApiResponse<T> & { success: true; data: T } => {
  return response.success && !!response.data;
};

/**
 * Type guard to check if an API response has an error
 */
export const hasApiError = <T>(response: ApiResponse<T>): response is ApiResponse<T> & { 
  success: false; 
  error: NonNullable<ApiResponse<T>['error']> 
} => {
  return !response.success && !!response.error;
};

/**
 * Type guard to check if an error is a network error
 */
export const isNetworkError = (error: unknown): error is Error & { code: 'network_error' } => {
  return error instanceof Error && 'code' in error && error.code === 'network_error';
};

/**
 * Type guard to check if an error is an API error
 */
export const isApiError = (error: unknown): error is Error & { code: 'api_error' } => {
  return error instanceof Error && 'code' in error && error.code === 'api_error';
};

/**
 * Type guard to check if a value is defined (not null or undefined)
 */
export const isDefined = <T>(value: T | null | undefined): value is T => {
  return value !== null && value !== undefined;
};

/**
 * Type guard to check if a string is not empty
 */
export const isNonEmptyString = (value: string | null | undefined): value is string => {
  return typeof value === 'string' && value.trim().length > 0;
};

/**
 * Type guard to check if an order has timeline events
 */
export const hasTimeline = (order: Order): order is Order & { timeline: NonNullable<Order['timeline']> } => {
  return !!order.timeline && Array.isArray(order.timeline) && order.timeline.length > 0;
};

/**
 * Type guard to check if an order has return requests
 */
export const hasReturnRequests = (order: Order): order is Order & { return_requests: NonNullable<Order['return_requests']> } => {
  return !!order.return_requests && Array.isArray(order.return_requests) && order.return_requests.length > 0;
};

/**
 * Type guard to check if an order has replacements
 */
export const hasReplacements = (order: Order): order is Order & { replacements: NonNullable<Order['replacements']> } => {
  return !!order.replacements && Array.isArray(order.replacements) && order.replacements.length > 0;
};

/**
 * Type guard to check if an order item can be returned
 */
export const isReturnableItem = (item: OrderItem): item is OrderItem & { can_return: true } => {
  return !!item.can_return;
};

/**
 * Type guard to check if a product has images
 */
export const hasProductImages = (product: Product): product is Product & { images: NonNullable<Product['images']> } => {
  return !!product.images && Array.isArray(product.images) && product.images.length > 0;
};

/**
 * Type guard to check if an address has a second address line
 */
export const hasAddressLine2 = (address: Address): address is Address & { address_line_2: NonNullable<Address['address_line_2']> } => {
  return !!address.address_line_2 && address.address_line_2.trim() !== '';
};

/**
 * Type guard to check if a replacement has tracking information
 */
export const hasTrackingInfo = (replacement: Replacement): replacement is Replacement & { 
  tracking_number: NonNullable<Replacement['tracking_number']> 
} => {
  return !!replacement.tracking_number && replacement.tracking_number.trim() !== '';
};

/**
 * Type guard to check if a replacement has shipping date
 */
export const hasShippingDate = (replacement: Replacement): replacement is Replacement & { 
  shipped_date: NonNullable<Replacement['shipped_date']> 
} => {
  return !!replacement.shipped_date;
};

/**
 * Type guard to check if a replacement has delivery date
 */
export const hasDeliveryDate = (replacement: Replacement): replacement is Replacement & { 
  delivered_date: NonNullable<Replacement['delivered_date']> 
} => {
  return !!replacement.delivered_date;
};

/**
 * Type guard to check if a return request has refund amount
 */
export const hasRefundAmount = (request: ReturnRequest): request is ReturnRequest & { 
  refund_amount: NonNullable<ReturnRequest['refund_amount']> 
} => {
  return typeof request.refund_amount === 'number' && request.refund_amount > 0;
};

/**
 * Type guard to check if a return request has tracking number
 */
export const hasReturnTrackingNumber = (request: ReturnRequest): request is ReturnRequest & { 
  return_tracking_number: NonNullable<ReturnRequest['return_tracking_number']> 
} => {
  return !!request.return_tracking_number && request.return_tracking_number.trim() !== '';
};

/**
 * Helper function to create a partial address that satisfies the Address type
 */
export const createPartialAddress = (addressData: Partial<Address>): Address => {
  return {
    id: addressData.id || '',
    type: (addressData.type as Address['type']) || 'HOME',
    is_default: addressData.is_default || false,
    first_name: addressData.first_name || '',
    last_name: addressData.last_name || '',
    address_line_1: addressData.address_line_1 || '',
    address_line_2: addressData.address_line_2,
    city: addressData.city || '',
    state: addressData.state || '',
    postal_code: addressData.postal_code || '',
    country: addressData.country || '',
  };
};