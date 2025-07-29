import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Card } from '../ui';
import {
  fetchAvailableDeliverySlots,
  setSelectedDeliverySlot
} from '../../store/slices/shippingSlice';
import { DeliverySlot } from '../../types/shipping';
import { AppDispatch, RootState } from '../../store';

interface DeliverySlotSelectorProps {
  onSelect?: (slot: DeliverySlot) => void;
  selectedSlotId?: string;
  pincode?: string;
}

const DeliverySlotSelector: React.FC<DeliverySlotSelectorProps> = ({
  onSelect,
  selectedSlotId: propSelectedSlotId,
  pincode
}) => {
  const dispatch = useDispatch<AppDispatch>();
  const {
    deliverySlots,
    selectedDeliverySlot,
    loading,
    error
  } = useSelector((state: RootState) => state.shipping);

  const [selectedDate, setSelectedDate] = useState<string>('');
  const [availableDates, setAvailableDates] = useState<string[]>([]);

  // Use the prop selectedSlotId if provided, otherwise use the one from the store
  const selectedSlotId = propSelectedSlotId || selectedDeliverySlot?.id;

  useEffect(() => {
    if (pincode) {
      // Generate next 7 days for demo purposes
      const dates = [];
      for (let i = 0; i < 7; i++) {
        const date = new Date();
        date.setDate(date.getDate() + i);
        dates.push(date.toISOString().split('T')[0]);
      }
      setAvailableDates(dates);
      setSelectedDate(dates[0]);

      // Fetch available slots for the pincode
      dispatch(fetchAvailableDeliverySlots({
        delivery_date: dates[0],
        pin_code: pincode
      }));
    }
  }, [dispatch, pincode]);

  useEffect(() => {
    if (selectedDate && pincode) {
      dispatch(fetchAvailableDeliverySlots({
        delivery_date: selectedDate,
        pin_code: pincode
      }));
    }
  }, [dispatch, selectedDate, pincode]);

  const handleSelectSlot = (slot: DeliverySlot) => {
    dispatch(setSelectedDeliverySlot(slot));
    if (onSelect) {
      onSelect(slot);
    }
  };

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = {
      weekday: 'short',
      month: 'short',
      day: 'numeric'
    };
    return new Date(dateString).toLocaleDateString('en-US', options);
  };

  const formatTimeSlot = (slot: DeliverySlot) => {
    return `${slot.start_time} - ${slot.end_time}`;
  };

  if (!pincode) {
    return (
      <div className="text-center py-4 text-gray-500">
        Please enter a pincode to view available delivery slots.
      </div>
    );
  }

  if (loading) {
    return <div className="text-center py-4">Loading delivery slots...</div>;
  }

  if (error) {
    return (
      <div className="text-center py-4 text-red-500">
        Error loading delivery slots: {error}
      </div>
    );
  }

  return (
    <div className="delivery-slot-selector">
      <h3 className="text-lg font-semibold mb-4">Select Delivery Date</h3>

      <div className="flex overflow-x-auto space-x-2 pb-2 mb-4">
        {availableDates.map(date => (
          <Button
            key={date}
            onClick={() => setSelectedDate(date)}
            variant={selectedDate === date ? 'primary' : 'outline'}
            className="whitespace-nowrap"
          >
            {formatDate(date)}
          </Button>
        ))}
      </div>

      <h3 className="text-lg font-semibold mb-4">Select Delivery Time</h3>

      {deliverySlots.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          No delivery slots available for this date.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {deliverySlots.map(slot => {
            const isSelected = selectedSlotId === slot.id;
            const isAvailable = slot.is_active && (slot.available_capacity || 0) > 0;

            return (
              <div
                key={slot.id}
                className={`cursor-pointer transition-all ${!isAvailable ? 'opacity-50 cursor-not-allowed' :
                  isSelected ? 'border-2 border-blue-500 bg-blue-50' : 'hover:border-gray-300'
                  }`}
                onClick={() => isAvailable && handleSelectSlot(slot)}
              >
                <Card>
                <div className="flex justify-between items-start">
                  <div>
                    <h4 className="font-medium">{slot.name}</h4>
                    <p className="text-sm text-gray-600">{formatTimeSlot(slot)}</p>
                    <p className="text-xs text-gray-500 mt-1">{slot.day_of_week_display}</p>
                  </div>
                  <div className="text-right">
                    {slot.additional_fee > 0 ? (
                      <span className="text-sm font-medium text-orange-600">
                        +₹{slot.additional_fee}
                      </span>
                    ) : (
                      <span className="text-sm text-green-600 font-medium">
                        Free
                      </span>
                    )}
                  </div>
                </div>
                <div className="mt-3 flex justify-between items-center">
                  <div className="text-xs text-gray-500">
                    {slot.available_capacity ? `${slot.available_capacity} slots left` : 'Limited slots'}
                  </div>
                  {!isAvailable ? (
                    <span className="text-xs text-red-600 font-medium">Not available</span>
                  ) : isSelected ? (
                    <span className="text-xs text-blue-600 font-medium flex items-center">
                      <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Selected
                    </span>
                  ) : null}
                </div>
                </Card>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DeliverySlotSelector;