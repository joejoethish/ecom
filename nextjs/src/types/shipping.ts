// Shipping and logistics type definitions

export interface ShippingPartner {
  id: string;
  name: string;
  code: string;
  partner_type: 'SHIPROCKET' | 'DELHIVERY' | 'OTHER';
  base_url: string;
  is_active: boolean;
  supports_cod: boolean;
  supports_prepaid: boolean;
  supports_international: boolean;
  supports_return: boolean;
  contact_person?: string;
  contact_email?: string;
  contact_phone?: string;
  created_at: string;
  updated_at: string;
}

export interface ServiceableArea {
  id: string;
  shipping_partner: string;
  pin_code: string;
  city: string;
  state: string;
  country: string;
  min_delivery_days: number;
  max_delivery_days: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface DeliverySlot {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  day_of_week: number;
  day_of_week_display: string;
  additional_fee: number;
  max_orders: number;
  is_active: boolean;
  available_capacity?: number;
  created_at: string;
  updated_at: string;
}

export interface ShipmentTracking {
  id: string;
  shipment: string;
  status: ShipmentStatus;
  status_display: string;
  description: string;
  location: string;
  timestamp: string;
  created_at: string;
}

export interface Shipment {
  id: string;
  order: string;
  shipping_partner: string;
  shipping_partner_name: string;
  tracking_number: string;
  shipping_label_url?: string;
  partner_order_id?: string;
  partner_shipment_id?: string;
  status: ShipmentStatus;
  status_display: string;
  estimated_delivery_date?: string;
  delivery_slot?: string;
  delivery_slot_display?: string;
  shipping_address: ShippingAddress;
  weight?: number;
  dimensions: Record<string, any>;
  shipping_cost: number;
  created_at: string;
  updated_at: string;
  shipped_at?: string;
  delivered_at?: string;
  tracking_updates: ShipmentTracking[];
}

export interface ShippingAddress {
  first_name: string;
  last_name: string;
  company?: string;
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  phone?: string;
}

export interface ShippingRate {
  id: string;
  shipping_partner: string;
  shipping_partner_name: string;
  source_pin_code?: string;
  destination_pin_code?: string;
  min_weight: number;
  max_weight: number;
  min_distance?: number;
  max_distance?: number;
  base_rate: number;
  per_kg_rate: number;
  per_km_rate: number;
  created_at: string;
  updated_at: string;
}

export interface ShippingRateCalculation {
  source_pin_code: string;
  destination_pin_code: string;
  weight: number;
  dimensions?: Record<string, any>;
  shipping_partner_id?: string;
}

export interface ShippingRateResult {
  shipping_partner: {
    id: string;
    name: string;
  };
  rate: number;
  min_delivery_days?: number;
  max_delivery_days?: number;
  estimated_delivery_days?: number;
  is_dynamic_rate: boolean;
}

export interface DeliverySlotAvailability {
  delivery_date: string;
  pin_code: string;
}

export interface ServiceabilityCheck {
  pin_code: string;
}

export interface ServiceabilityResult {
  serviceable: boolean;
  message?: string;
  areas?: ServiceableArea[];
}

export type ShipmentStatus =
  | 'PENDING'
  | 'PROCESSING'
  | 'SHIPPED'
  | 'IN_TRANSIT'
  | 'OUT_FOR_DELIVERY'
  | 'DELIVERED'
  | 'FAILED_DELIVERY'
  | 'RETURNED'
  | 'CANCELLED';

export interface ShippingState {
  partners: ShippingPartner[];
  serviceableAreas: ServiceableArea[];
  deliverySlots: DeliverySlot[];
  shipments: Shipment[];
  currentShipment: Shipment | null;
  shippingRates: ShippingRateResult[];
  selectedDeliverySlot: DeliverySlot | null;
  selectedShippingAddress: ShippingAddress | null;
  loading: boolean;
  error: string | null;
}

export interface TrackingInfo {
  shipment: Shipment;
  tracking_history: ShipmentTracking[];
}