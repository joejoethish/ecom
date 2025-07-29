/**
 * Types for seller-related data
 */

export interface SellerProfile {
  id: string;
  business_name: string;
  business_type: string;
  business_type_display: string;
  tax_id: string;
  gstin: string;
  pan_number: string;
  description: string;
  logo: string | null;
  banner: string | null;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  phone_number: string;
  email: string;
  website: string;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'SUSPENDED';
  verification_status_display: string;
  verification_notes: string;
  verified_at: string | null;
  commission_rate: number;
  rating: number;
  total_sales: number;
  is_active: boolean;
  is_featured: boolean;
  created_at: string;
  updated_at: string;
}

export interface SellerKYC {
  id: string;
  document_type: 'ID_PROOF' | 'ADDRESS_PROOF' | 'BUSINESS_PROOF' | 'TAX_DOCUMENT' | 'BANK_STATEMENT' | 'OTHER';
  document_type_display: string;
  document_number: string;
  document_file: string;
  document_name: string;
  issue_date: string | null;
  expiry_date: string | null;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED' | 'EXPIRED';
  verification_status_display: string;
  verification_notes: string;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SellerBankAccount {
  id: string;
  account_holder_name: string;
  bank_name: string;
  account_number: string;
  ifsc_code: string;
  branch_name: string;
  account_type: 'SAVINGS' | 'CURRENT' | 'BUSINESS';
  account_type_display: string;
  is_primary: boolean;
  verification_status: 'PENDING' | 'VERIFIED' | 'REJECTED';
  verification_status_display: string;
  verification_document: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface SellerPayout {
  id: string;
  amount: number;
  transaction_id: string;
  transaction_fee: number;
  payout_date: string;
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED';
  status_display: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface SellerAnalytics {
  total_sales: number;
  total_orders: number;
  total_products: number;
  recent_orders: {
    id: string;
    order_number: string;
    total_amount: number;
    status: string;
    created_at: string;
  }[];
  sales_by_period: {
    period: string;
    amount: number;
  }[];
  top_products: {
    id: string;
    name: string;
    sales: number;
    quantity: number;
  }[];
}

export interface SellerRegistrationData {
  business_name: string;
  business_type: string;
  tax_id: string;
  gstin: string;
  pan_number: string;
  description: string;
  logo?: File;
  banner?: File;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  phone_number: string;
  email: string;
  website: string;
}

export interface KYCDocumentData {
  document_type: string;
  document_number: string;
  document_file: File;
  document_name: string;
  issue_date?: string;
  expiry_date?: string;
}

export interface BankAccountData {
  account_holder_name: string;
  bank_name: string;
  account_number: string;
  ifsc_code: string;
  branch_name: string;
  account_type: string;
  is_primary: boolean;
  verification_document?: File;
}