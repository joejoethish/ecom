/**
 * Type guards for conditional rendering and property access
 */
import { Order, OrderItem, ReturnRequest, Replacement, Address, Product, ApiResponse } from '@/types';
/**
 * Type guard to check if an error is an AxiosError
 */
  return !!(error && typeof error === &apos;object&apos; && &apos;response&apos; in error && &apos;request&apos; in error);
};

/**
 * Type guard to check if an error has a response
 */
  return !!error.response;
};

/**
 * Type guard to check if an error has request data
 */
  return !!error.request;
};

/**
 * Type guard to check if an API response is successful
 */
  return response.success && !!response.data;
};

/**
 * Type guard to check if an API response has an error
 */
  success: false; 
  error: NonNullable<ApiResponse<T>[&apos;error&apos;]> 
} => {
  return !response.success && !!response.error;
};

/**
 * Type guard to check if an error is a network error
 */
  return error instanceof Error && &apos;code&apos; in error && error.code === &apos;network_error&apos;;
};

/**
 * Type guard to check if an error is an API error
 */
  return error instanceof Error && &apos;code&apos; in error && error.code === &apos;api_error&apos;;
};

/**
 * Type guard to check if a value is defined (not null or undefined)
 */
  return value !== null && value !== undefined;
};

/**
 * Type guard to check if a string is not empty
 */
  return typeof value === &apos;string&apos; && value.trim().length > 0;
};

/**
 * Type guard to check if an order has timeline events
 */
  return !!order.timeline && Array.isArray(order.timeline) && order.timeline.length > 0;
};

/**
 * Type guard to check if an order has return requests
 */
  return !!order.return_requests && Array.isArray(order.return_requests) && order.return_requests.length > 0;
};

/**
 * Type guard to check if an order has replacements
 */
  return !!order.replacements && Array.isArray(order.replacements) && order.replacements.length > 0;
};

/**
 * Type guard to check if an order item can be returned
 */
  return !!item.can_return;
};

/**
 * Type guard to check if a product has images
 */
  return !!product.images && Array.isArray(product.images) && product.images.length > 0;
};

/**
 * Type guard to check if an address has a second address line
 */
  return !!address.address_line_2 && address.address_line_2.trim() !== &apos;&apos;;
};

/**
 * Type guard to check if a replacement has tracking information
 */
  tracking_number: NonNullable<Replacement['tracking_number']> 
} => {
  return !!replacement.tracking_number && replacement.tracking_number.trim() !== &apos;&apos;;
};

/**
 * Type guard to check if a replacement has shipping date
 */
  shipped_date: NonNullable<Replacement['shipped_date']> 
} => {
  return !!replacement.shipped_date;
};

/**
 * Type guard to check if a replacement has delivery date
 */
  delivered_date: NonNullable<Replacement['delivered_date']> 
} => {
  return !!replacement.delivered_date;
};

/**
 * Type guard to check if a return request has refund amount
 */
  refund_amount: NonNullable<ReturnRequest['refund_amount']> 
} => {
  return typeof request.refund_amount === &apos;number&apos; && request.refund_amount > 0;
};

/**
 * Type guard to check if a return request has tracking number
 */
  return_tracking_number: NonNullable<ReturnRequest['return_tracking_number']> 
} => {
  return !!request.return_tracking_number && request.return_tracking_number.trim() !== &apos;&apos;;
};

/**
 * Helper function to create a partial address that satisfies the Address type
 */
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