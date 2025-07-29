// Payment related type definitions

export interface Currency {
  code: string;
  name: string;
  symbol: string;
  exchange_rate: number;
}

export interface PaymentMethod {
  id: string;
  name: string;
  method_type: PaymentMethodType;
  gateway: PaymentGateway;
  icon?: string;
  description?: string;
  processing_fee_percentage: number;
  processing_fee_fixed: number;
  is_active: boolean;
}

export type PaymentMethodType = 
  | 'CARD' 
  | 'UPI' 
  | 'WALLET' 
  | 'NETBANKING' 
  | 'COD' 
  | 'GIFT_CARD'
  | 'IMPS'
  | 'RTGS'
  | 'NEFT';

export type PaymentGateway = 'RAZORPAY' | 'STRIPE' | 'INTERNAL';

export type PaymentStatus = 
  | 'PENDING'
  | 'PROCESSING'
  | 'COMPLETED'
  | 'FAILED'
  | 'REFUNDED'
  | 'PARTIALLY_REFUNDED'
  | 'CANCELLED';

export interface Payment {
  id: string;
  order_id: string;
  amount: number;
  currency: string;
  payment_method: PaymentMethod;
  status: PaymentStatus;
  transaction_id?: string;
  gateway_payment_id?: string;
  gateway_order_id?: string;
  processing_fee: number;
  failure_reason?: string;
  payment_date?: string;
  created_at: string;
  updated_at: string;
}

export interface PaymentResponse {
  payment_id: string;
  status: PaymentStatus;
  amount: number;
  currency: string;
  payment_method: PaymentMethodType;
  gateway_data?: any;
}

export interface WalletDetails {
  id: string;
  user_id: string;
  balance: number;
  currency: Currency;
  is_active: boolean;
}

export interface GiftCard {
  id: string;
  code: string;
  initial_balance: number;
  current_balance: number;
  currency: Currency;
  status: 'ACTIVE' | 'USED' | 'EXPIRED' | 'CANCELLED';
  expiry_date: string;
}

export interface PaymentFormData {
  order_id: string;
  amount: number;
  currency_code: string;
  payment_method_id: string;
  metadata?: Record<string, any>;
}

export interface PaymentVerificationData {
  payment_id: string;
  gateway_payment_id: string;
  gateway_signature: string;
  metadata?: Record<string, any>;
}

export interface CurrencyConversion {
  from_currency: string;
  to_currency: string;
  amount: number;
  converted_amount: number;
  exchange_rate: number;
}