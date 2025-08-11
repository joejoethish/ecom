import { useSelector } from 'react-redux';
import { useCallback } from 'react';
import { RootState, AppDispatch, useAppDispatch } from '../store';
import {
  fetchShippingPartners,
  checkServiceability,
  fetchAvailableDeliverySlots,
  calculateShippingRates,
  trackShipment,
  fetchUserShipments,
  setSelectedDeliverySlot,
  setSelectedShippingAddress,
  clearShippingRates,
  clearDeliverySlots,
  setCurrentShipment,
  resetShippingState,
  clearError
} from '../store/slices/shippingSlice';
import { 
  DeliverySlot, 
  ShippingAddress, 
  ShippingRateCalculation,
  DeliverySlotAvailability,
  ServiceabilityCheck
} from '../types/shipping';

export const useShipping = () => {
  const dispatch = useAppDispatch();
  const shippingState = useSelector((state: RootState) => state.shipping);

  // Shipping partners
  const loadShippingPartners = useCallback(() => {
    return dispatch(fetchShippingPartners());
  }, [dispatch]);

  // Serviceability
  const checkDeliveryAvailability = useCallback((pinCode: string) => {
    return dispatch(checkServiceability({ pin_code: pinCode }));
  }, [dispatch]);

  // Delivery slots
  const loadAvailableDeliverySlots = useCallback((data: DeliverySlotAvailability) => {
    return dispatch(fetchAvailableDeliverySlots(data));
  }, [dispatch]);

  const selectDeliverySlot = useCallback((slot: DeliverySlot | null) => {
    dispatch(setSelectedDeliverySlot(slot));
  }, [dispatch]);

  const clearDeliverySlotSelection = useCallback(() => {
    dispatch(clearDeliverySlots());
  }, [dispatch]);

  // Shipping address
  const selectShippingAddress = useCallback((address: ShippingAddress | null) => {
    dispatch(setSelectedShippingAddress(address));
  }, [dispatch]);

  // Shipping rates
  const calculateRates = useCallback((data: ShippingRateCalculation) => {
    return dispatch(calculateShippingRates(data));
  }, [dispatch]);

  const clearRates = useCallback(() => {
    dispatch(clearShippingRates());
  }, [dispatch]);

  // Tracking
  const trackOrder = useCallback((trackingNumber: string) => {
    return dispatch(trackShipment(trackingNumber));
  }, [dispatch]);

  const loadUserShipments = useCallback(() => {
    return dispatch(fetchUserShipments());
  }, [dispatch]);

  const selectCurrentShipment = useCallback((shipment: any) => {
    dispatch(setCurrentShipment(shipment));
  }, [dispatch]);

  // Utility actions
  const clearErrors = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  const resetState = useCallback(() => {
    dispatch(resetShippingState());
  }, [dispatch]);

  // Computed values
  const isLoading = shippingState.loading;
  const hasError = !!shippingState.error;

  return {
    // State
    ...shippingState,
    isLoading,
    hasError,

    // Actions
    loadShippingPartners,
    checkDeliveryAvailability,
    loadAvailableDeliverySlots,
    selectDeliverySlot,
    clearDeliverySlotSelection,
    selectShippingAddress,
    calculateRates,
    clearRates,
    trackOrder,
    loadUserShipments,
    selectCurrentShipment,
    clearErrors,
    resetState
  };
};