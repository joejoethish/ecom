import { apiClient } from '../utils/api';
import {
  ShippingPartner,
  ServiceableArea,
  DeliverySlot,
  Shipment,
  ShippingRateCalculation,
  ShippingRateResult,
  DeliverySlotAvailability,
  ServiceabilityResult,
  TrackingInfo,
  ApiResponse,
  PaginatedResponse
} from '../types';

  // Shipping Partners
  getShippingPartners: (): Promise<ApiResponse<ShippingPartner[]>> => {
    return apiClient.get(&apos;/shipping/partners/&apos;);
  },

  getShippingPartner: (id: string): Promise<ApiResponse<ShippingPartner>> => {
    return apiClient.get(`/shipping/partners/${id}/`);
  },

  // Serviceability
  checkServiceability: (pinCode: string): Promise<ApiResponse<ServiceabilityResult>> => {
    return apiClient.get(`/shipping/serviceable-areas/check_serviceability/?pin_code=${pinCode}`);
  },

  getServiceableAreas: (params?: {
    shipping_partner?: string;
    pin_code?: string;
    city?: string;
    state?: string;
    country?: string;
    is_active?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<ServiceableArea>>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/shipping/serviceable-areas/?${queryParams.toString()}`);
  },

  // Delivery Slots
  getDeliverySlots: (params?: {
    day_of_week?: number;
    is_active?: boolean;
  }): Promise<ApiResponse<PaginatedResponse<DeliverySlot>>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/shipping/delivery-slots/?${queryParams.toString()}`);
  },

  getAvailableDeliverySlots: (data: DeliverySlotAvailability): Promise<ApiResponse<DeliverySlot[]>> => {
    return apiClient.post(&apos;/shipping/delivery-slots/available_slots/&apos;, data);
  },

  // Shipping Rates
  calculateShippingRates: (data: ShippingRateCalculation): Promise<ApiResponse<ShippingRateResult[]>> => {
    return apiClient.post(&apos;/shipping/shipping-rates/calculate/&apos;, data);
  },

  getShippingRates: (params?: {
    shipping_partner?: string;
    source_pin_code?: string;
    destination_pin_code?: string;
  }): Promise<ApiResponse<PaginatedResponse<ShippingRateResult>>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/shipping/shipping-rates/?${queryParams.toString()}`);
  },

  // Shipments
  getUserShipments: (params?: {
    order?: string;
    shipping_partner?: string;
    status?: string;
    estimated_delivery_date?: string;
  }): Promise<ApiResponse<PaginatedResponse<Shipment>>> => {
    const queryParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          queryParams.append(key, value.toString());
        }
      });
    }
    return apiClient.get(`/shipping/shipments/?${queryParams.toString()}`);
  },

  getShipment: (id: string): Promise<ApiResponse<Shipment>> => {
    return apiClient.get(`/shipping/shipments/${id}/`);
  },

  createShipment: (data: Partial<Shipment>): Promise<ApiResponse<Shipment>> => {
    return apiClient.post(&apos;/shipping/shipments/&apos;, data);
  },

  updateShipment: (id: string, data: Partial<Shipment>): Promise<ApiResponse<Shipment>> => {
    return apiClient.patch(`/shipping/shipments/${id}/`, data);
  },

  updateShipmentStatus: (id: string, data: {
    status: string;
    description?: string;
    location?: string;
  }): Promise<ApiResponse<Shipment>> => {
    return apiClient.post(`/shipping/shipments/${id}/update_status/`, data);
  },

  // Tracking
  trackShipment: (trackingNumber: string): Promise<ApiResponse<TrackingInfo>> => {
    return apiClient.get(`/shipping/shipments/${trackingNumber}/track/`);
  },

  trackShipmentById: (id: string): Promise<ApiResponse<TrackingInfo>> => {
    return apiClient.get(`/shipping/shipments/${id}/track/`);
  },

  // Bulk operations (admin only)
  bulkUpdateShipmentStatus: (data: {
    shipment_ids: string[];
    status: string;
    description?: string;
    location?: string;
  }): Promise<ApiResponse<{ message: string; updated_count: number }>> => {
    return apiClient.post(&apos;/shipping/shipments/bulk_update_status/&apos;, data);
  },

  // Analytics (admin only)
  getShipmentAnalytics: (data: {
    date_from: string;
    date_to: string;
    shipping_partner_id?: string;
    status?: string;
  }): Promise<ApiResponse<unknown>> => {
    return apiClient.post(&apos;/shipping/shipments/analytics/&apos;, data);
  },

  // Webhooks (for shipping partners)
  processTrackingWebhook: (data: {
    tracking_number: string;
    status: string;
    description?: string;
    location?: string;
    timestamp: string;
    partner_data?: Record<string, unknown>;
  }): Promise<ApiResponse<{ status: string; message: string }>> => {
    return apiClient.post('/shipping/shipments/webhook/', data);
  },
};