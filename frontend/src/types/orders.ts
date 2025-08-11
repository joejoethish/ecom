// Order related type definitions

export interface OrderTracking {
  id: string;
  status: string;
  description: string;
  location?: string;
  created_by?: string;
  created_at: string;
}

export interface OrderDetail {
  id: string;
  order_number: string;
  customer: string;
  customer_name: string;
  status: string;
  payment_status: string;
  total_amount: number;
  shipping_amount: number;
  tax_amount: number;
  discount_amount: number;
  shipping_address: Record<string, unknown>;
  billing_address: Record<string, unknown>;
  shipping_method: string;
  payment_method: string;
  estimated_delivery_date?: string;
  actual_delivery_date?: string;
  tracking_number?: string;
  invoice_number?: string;
  notes?: string;
  items: OrderItem[];
  total_items: number;
  timeline: OrderTracking[];
  can_cancel: boolean;
  can_return: boolean;
  return_requests: ReturnRequest[];
  replacements: Replacement[];
  has_invoice: boolean;
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: string;
  product: {
    id: string;
    name: string;
    slug: string;
    price: number;
    images: Array<{
      id: string;
      image: string;
      alt_text: string;
      is_primary: boolean;
    }>;
  };
  quantity: number;
  unit_price: number;
  total_price: number;
  status: string;
  is_gift: boolean;
  gift_message?: string;
  returned_quantity?: number;
  refunded_amount?: number;
  can_return: boolean;
}

export interface ReturnRequest {
  id: string;
  order: string;
  order_number: string;
  order_item: string;
  product_name: string;
  quantity: number;
  reason: string;
  description: string;
  status: string;
  refund_amount: number;
  refund_method: string;
  return_tracking_number?: string;
  return_received_date?: string;
  refund_processed_date?: string;
  processed_by?: string;
  processed_by_name?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface Replacement {
  id: string;
  return_request?: string;
  order: string;
  order_number: string;
  order_item: string;
  product_name: string;
  replacement_product: string;
  replacement_product_name: string;
  quantity: number;
  status: string;
  shipping_address: Record<string, unknown>;
  tracking_number?: string;
  shipped_date?: string;
  delivered_date?: string;
  processed_by?: string;
  processed_by_name?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface ReturnRequestFormData {
  order_item_id: string;
  quantity: number;
  reason: string;
  description: string;
}

  { value: 'damaged', label: 'Product Damaged' },
  { value: 'defective', label: 'Product Defective' },
  { value: 'wrong_item', label: 'Wrong Item Received' },
  { value: 'not_as_described', label: 'Not As Described' },
  { value: 'unwanted', label: 'No Longer Wanted' },
  { value: 'size_issue', label: 'Size/Fit Issue' },
  { value: 'quality_issue', label: 'Quality Issue' },
  { value: 'other', label: 'Other' },
];