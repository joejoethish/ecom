from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
import logging

from .models import (
    ShippingPartner, 
    ServiceableArea, 
    DeliverySlot, 
    Shipment, 
    ShipmentTracking,
    ShippingRate
)
from .serializers import (
    ShippingPartnerSerializer,
    ServiceableAreaSerializer,
    DeliverySlotSerializer,
    ShipmentSerializer,
    ShipmentTrackingSerializer,
    ShippingRateSerializer,
    ShippingRateCalculationSerializer,
    DeliverySlotAvailabilitySerializer,
    TrackingWebhookSerializer,
    BulkShipmentUpdateSerializer,
    ShipmentAnalyticsSerializer
)
from .services import ShippingPartnerService, ShiprocketService, ShippingException

logger = logging.getLogger(__name__)


class ShippingPartnerViewSet(viewsets.ModelViewSet):
    """ViewSet for shipping partners"""
    queryset = ShippingPartner.objects.all()
    serializer_class = ShippingPartnerSerializer
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=True, methods=['post'])
    def check_connection(self, request, pk=None):
        """Test the connection to the shipping partner API"""
        shipping_partner = self.get_object()
        
        try:
            if shipping_partner.partner_type == 'SHIPROCKET':
                service = ShiprocketService(shipping_partner)
                # Test authentication
                service._authenticate()
                return Response({'status': 'success', 'message': 'Connection successful'})
            else:
                return Response(
                    {'status': 'error', 'message': f'Testing not implemented for {shipping_partner.partner_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except ShippingException as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ServiceableAreaViewSet(viewsets.ModelViewSet):
    """ViewSet for serviceable areas"""
    queryset = ServiceableArea.objects.all()
    serializer_class = ServiceableAreaSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['shipping_partner', 'pin_code', 'city', 'state', 'country', 'is_active']
    search_fields = ['pin_code', 'city', 'state']
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def check_serviceability(self, request):
        """Check if a pin code is serviceable"""
        pin_code = request.query_params.get('pin_code')
        
        if not pin_code:
            return Response(
                {'error': 'Pin code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serviceable_areas = ServiceableArea.objects.filter(
            pin_code=pin_code,
            is_active=True
        ).select_related('shipping_partner')
        
        if not serviceable_areas.exists():
            return Response(
                {'serviceable': False, 'message': 'This pin code is not serviceable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = ServiceableAreaSerializer(serviceable_areas, many=True)
        return Response({
            'serviceable': True,
            'areas': serializer.data
        })


class DeliverySlotViewSet(viewsets.ModelViewSet):
    """ViewSet for delivery slots"""
    queryset = DeliverySlot.objects.all()
    serializer_class = DeliverySlotSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['day_of_week', 'is_active']
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def available_slots(self, request):
        """Get available delivery slots for a specific date and pin code"""
        serializer = DeliverySlotAvailabilitySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        delivery_date = serializer.validated_data['delivery_date']
        pin_code = serializer.validated_data['pin_code']
        
        # Check if pin code is serviceable
        if not ServiceableArea.objects.filter(pin_code=pin_code, is_active=True).exists():
            return Response(
                {'error': 'This pin code is not serviceable'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get day of week (0-6, Monday is 0)
        day_of_week = delivery_date.weekday()
        
        # Get available slots for this day
        slots = DeliverySlot.objects.filter(
            day_of_week=day_of_week,
            is_active=True
        )
        
        # Check slot availability (count shipments for each slot on this date)
        available_slots = []
        for slot in slots:
            shipment_count = Shipment.objects.filter(
                delivery_slot=slot,
                estimated_delivery_date=delivery_date
            ).count()
            
            if shipment_count < slot.max_orders:
                slot_data = DeliverySlotSerializer(slot).data
                slot_data['available_capacity'] = slot.max_orders - shipment_count
                available_slots.append(slot_data)
        
        return Response(available_slots)


class ShipmentViewSet(viewsets.ModelViewSet):
    """ViewSet for shipments"""
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['order', 'shipping_partner', 'status', 'estimated_delivery_date']
    
    def get_queryset(self):
        """Filter shipments based on user role"""
        user = self.request.user
        
        # Admin users can see all shipments
        if user.is_staff:
            return Shipment.objects.all()
        
        # Regular users can only see their own shipments
        return Shipment.objects.filter(order__user=user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update shipment status"""
        shipment = self.get_object()
        status = request.data.get('status')
        description = request.data.get('description', '')
        location = request.data.get('location', '')
        
        if not status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status
        valid_statuses = [s[0] for s in Shipment.STATUS_CHOICES]
        if status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update shipment status
        shipment.status = status
        
        # Update timestamps based on status
        if status == 'SHIPPED' and not shipment.shipped_at:
            shipment.shipped_at = timezone.now()
        elif status == 'DELIVERED' and not shipment.delivered_at:
            shipment.delivered_at = timezone.now()
        
        shipment.save()
        
        # Create tracking update
        tracking = ShipmentTracking.objects.create(
            shipment=shipment,
            status=status,
            description=description,
            location=location,
            timestamp=timezone.now()
        )
        
        return Response(ShipmentSerializer(shipment).data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def track(self, request, pk=None):
        """Track a shipment by tracking number"""
        try:
            # Allow tracking by ID or tracking number
            if pk.isdigit():
                shipment = get_object_or_404(Shipment, id=pk)
            else:
                shipment = get_object_or_404(Shipment, tracking_number=pk)
            
            # Get tracking updates
            tracking_updates = ShipmentTracking.objects.filter(shipment=shipment).order_by('-timestamp')
            
            response_data = {
                'shipment': ShipmentSerializer(shipment).data,
                'tracking_history': ShipmentTrackingSerializer(tracking_updates, many=True).data
            }
            
            return Response(response_data)
        except Shipment.DoesNotExist:
            return Response(
                {'error': 'Shipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def bulk_update_status(self, request):
        """Bulk update shipment statuses"""
        serializer = BulkShipmentUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        shipment_ids = serializer.validated_data['shipment_ids']
        status_value = serializer.validated_data['status']
        description = serializer.validated_data.get('description', '')
        location = serializer.validated_data.get('location', '')
        
        # Get shipments
        shipments = Shipment.objects.filter(id__in=shipment_ids)
        if shipments.count() != len(shipment_ids):
            return Response(
                {'error': 'Some shipments not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Update shipments and create tracking records
        updated_count = 0
        current_time = timezone.now()
        
        for shipment in shipments:
            # Update shipment status
            shipment.status = status_value
            
            # Update timestamps based on status
            if status_value == 'SHIPPED' and not shipment.shipped_at:
                shipment.shipped_at = current_time
            elif status_value == 'DELIVERED' and not shipment.delivered_at:
                shipment.delivered_at = current_time
            
            shipment.save()
            
            # Create tracking update
            ShipmentTracking.objects.create(
                shipment=shipment,
                status=status_value,
                description=description,
                location=location,
                timestamp=current_time
            )
            
            updated_count += 1
        
        return Response({
            'message': f'Successfully updated {updated_count} shipments',
            'updated_count': updated_count
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def analytics(self, request):
        """Get shipment analytics data"""
        serializer = ShipmentAnalyticsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        date_from = serializer.validated_data['date_from']
        date_to = serializer.validated_data['date_to']
        shipping_partner_id = serializer.validated_data.get('shipping_partner_id')
        status_filter = serializer.validated_data.get('status')
        
        # Build query
        query = Q(created_at__date__gte=date_from, created_at__date__lte=date_to)
        
        if shipping_partner_id:
            query &= Q(shipping_partner_id=shipping_partner_id)
        
        if status_filter:
            query &= Q(status=status_filter)
        
        shipments = Shipment.objects.filter(query)
        
        # Calculate analytics
        total_shipments = shipments.count()
        
        # Status breakdown
        status_breakdown = {}
        for choice in Shipment.STATUS_CHOICES:
            status_code = choice[0]
            count = shipments.filter(status=status_code).count()
            status_breakdown[status_code] = {
                'count': count,
                'percentage': round((count / total_shipments * 100) if total_shipments > 0 else 0, 2)
            }
        
        # Partner breakdown
        partner_breakdown = {}
        for partner in ShippingPartner.objects.all():
            count = shipments.filter(shipping_partner=partner).count()
            if count > 0:
                partner_breakdown[partner.name] = {
                    'count': count,
                    'percentage': round((count / total_shipments * 100), 2)
                }
        
        # Average delivery time for delivered shipments
        delivered_shipments = shipments.filter(
            status='DELIVERED',
            shipped_at__isnull=False,
            delivered_at__isnull=False
        )
        
        avg_delivery_time = None
        if delivered_shipments.exists():
            total_delivery_time = sum([
                (shipment.delivered_at - shipment.shipped_at).days
                for shipment in delivered_shipments
                if shipment.delivered_at and shipment.shipped_at
            ])
            avg_delivery_time = round(total_delivery_time / delivered_shipments.count(), 1)
        
        return Response({
            'total_shipments': total_shipments,
            'date_range': {
                'from': date_from,
                'to': date_to
            },
            'status_breakdown': status_breakdown,
            'partner_breakdown': partner_breakdown,
            'average_delivery_time_days': avg_delivery_time,
            'delivered_shipments': delivered_shipments.count(),
            'pending_shipments': shipments.filter(status__in=['PENDING', 'PROCESSING']).count(),
            'failed_shipments': shipments.filter(status='FAILED_DELIVERY').count()
        })
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def webhook(self, request):
        """Webhook endpoint for receiving tracking updates from shipping partners"""
        serializer = TrackingWebhookSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"Invalid webhook data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        tracking_number = serializer.validated_data['tracking_number']
        status_value = serializer.validated_data['status']
        description = serializer.validated_data.get('description', '')
        location = serializer.validated_data.get('location', '')
        timestamp = serializer.validated_data['timestamp']
        partner_data = serializer.validated_data.get('partner_data', {})
        
        try:
            # Find shipment by tracking number
            shipment = Shipment.objects.get(tracking_number=tracking_number)
            
            # Enhanced status mapping with more comprehensive coverage
            status_mapping = {
                # Standard statuses
                'SHIPPED': 'SHIPPED',
                'IN_TRANSIT': 'IN_TRANSIT',
                'OUT_FOR_DELIVERY': 'OUT_FOR_DELIVERY',
                'DELIVERED': 'DELIVERED',
                'FAILED_DELIVERY': 'FAILED_DELIVERY',
                'RETURNED': 'RETURNED',
                'CANCELLED': 'CANCELLED',
                
                # Shiprocket specific statuses
                'PICKUP SCHEDULED': 'PROCESSING',
                'PICKUP GENERATED': 'PROCESSING',
                'AWB ASSIGNED': 'PROCESSING',
                'LABEL GENERATED': 'PROCESSING',
                'PICKUP COMPLETE': 'SHIPPED',
                'RTO INITIATED': 'RETURNED',
                'RTO DELIVERED': 'RETURNED',
                
                # Delhivery specific statuses
                'PICKUP ASSIGNED': 'PROCESSING',
                'DISPATCHED': 'SHIPPED',
                'REACHED DESTINATION HUB': 'IN_TRANSIT',
                
                # Common variations
                'DISPATCHED': 'SHIPPED',
                'IN TRANSIT': 'IN_TRANSIT',
                'OUT FOR DELIVERY': 'OUT_FOR_DELIVERY',
                'DELIVERY ATTEMPTED': 'FAILED_DELIVERY',
                'UNDELIVERED': 'FAILED_DELIVERY',
            }
            
            internal_status = status_mapping.get(status_value.upper(), status_value.upper())
            
            # Prevent duplicate tracking updates for the same status and timestamp
            existing_tracking = ShipmentTracking.objects.filter(
                shipment=shipment,
                status=internal_status,
                timestamp=timestamp
            ).first()
            
            if not existing_tracking:
                # Create tracking update
                tracking = ShipmentTracking.objects.create(
                    shipment=shipment,
                    status=internal_status,
                    description=description,
                    location=location,
                    timestamp=timestamp,
                    raw_response=partner_data
                )
                
                # Update shipment status only if it's a progression
                status_hierarchy = [
                    'PENDING', 'PROCESSING', 'SHIPPED', 'IN_TRANSIT', 
                    'OUT_FOR_DELIVERY', 'DELIVERED', 'FAILED_DELIVERY', 
                    'RETURNED', 'CANCELLED'
                ]
                
                current_index = status_hierarchy.index(shipment.status) if shipment.status in status_hierarchy else 0
                new_index = status_hierarchy.index(internal_status) if internal_status in status_hierarchy else len(status_hierarchy)
                
                # Update status if it's a valid progression or terminal status
                if new_index >= current_index or internal_status in ['DELIVERED', 'CANCELLED', 'RETURNED']:
                    shipment.status = internal_status
                    
                    # Update timestamps based on status
                    if internal_status == 'SHIPPED' and not shipment.shipped_at:
                        shipment.shipped_at = timestamp
                    elif internal_status == 'DELIVERED' and not shipment.delivered_at:
                        shipment.delivered_at = timestamp
                    
                    shipment.save()
            
            return Response({'status': 'success', 'message': 'Tracking update processed'})
        except Shipment.DoesNotExist:
            logger.error(f"Webhook received for unknown tracking number: {tracking_number}")
            return Response(
                {'error': 'Shipment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ShippingRateViewSet(viewsets.ModelViewSet):
    """ViewSet for shipping rates"""
    queryset = ShippingRate.objects.all()
    serializer_class = ShippingRateSerializer
    permission_classes = [permissions.IsAdminUser]
    filterset_fields = ['shipping_partner', 'source_pin_code', 'destination_pin_code']
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Bulk create shipping rates"""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of shipping rates'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ShippingRateSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def sync_partner_rates(self, request):
        """Sync rates from shipping partner API"""
        partner_id = request.data.get('shipping_partner_id')
        if not partner_id:
            return Response(
                {'error': 'shipping_partner_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            shipping_partner = ShippingPartner.objects.get(id=partner_id)
            
            # Create appropriate service based on partner type
            if shipping_partner.partner_type == 'SHIPROCKET':
                service = ShiprocketService(shipping_partner)
                # Implement rate sync logic here
                return Response({'message': 'Rate sync not yet implemented for Shiprocket'})
            else:
                return Response(
                    {'error': f'Rate sync not implemented for {shipping_partner.partner_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except ShippingPartner.DoesNotExist:
            return Response(
                {'error': 'Shipping partner not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def calculate(self, request):
        """Calculate shipping rate for a package"""
        serializer = ShippingRateCalculationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        source_pin_code = serializer.validated_data['source_pin_code']
        destination_pin_code = serializer.validated_data['destination_pin_code']
        weight = serializer.validated_data['weight']
        dimensions = serializer.validated_data.get('dimensions', {})
        shipping_partner_id = serializer.validated_data.get('shipping_partner_id')
        
        # Check if destination is serviceable
        if not ServiceableArea.objects.filter(pin_code=destination_pin_code, is_active=True).exists():
            return Response(
                {'error': 'Destination pin code is not serviceable'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build query for shipping rates
        query = Q(
            min_weight__lte=weight,
            max_weight__gte=weight
        )
        
        # Add pin code filters if they exist in the rates table
        if source_pin_code:
            query &= (
                Q(source_pin_code='') | 
                Q(source_pin_code__isnull=True) | 
                Q(source_pin_code=source_pin_code)
            )
        
        if destination_pin_code:
            query &= (
                Q(destination_pin_code='') | 
                Q(destination_pin_code__isnull=True) | 
                Q(destination_pin_code=destination_pin_code)
            )
        
        # Filter by shipping partner if specified
        if shipping_partner_id:
            query &= Q(shipping_partner_id=shipping_partner_id)
        
        # Get applicable rates
        rates = ShippingRate.objects.filter(query).select_related('shipping_partner')
        
        if not rates.exists():
            # If no specific rates found, try to use a shipping partner service to calculate
            if shipping_partner_id:
                try:
                    shipping_partner = ShippingPartner.objects.get(id=shipping_partner_id)
                    
                    # Create appropriate service based on partner type
                    if shipping_partner.partner_type == 'SHIPROCKET':
                        service = ShiprocketService(shipping_partner)
                    else:
                        return Response(
                            {'error': f'Rate calculation not implemented for {shipping_partner.partner_type}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
                    # Calculate rate using the service
                    package_data = {
                        'weight': float(weight),
                        'dimensions': dimensions,
                        'source_pin_code': source_pin_code,
                        'destination_pin_code': destination_pin_code
                    }
                    
                    rate_data = service.calculate_shipping_rate(package_data)
                    
                    return Response({
                        'shipping_partner': {
                            'id': shipping_partner.id,
                            'name': shipping_partner.name
                        },
                        'rate': rate_data['rate'],
                        'estimated_delivery_days': rate_data.get('estimated_delivery_days'),
                        'is_dynamic_rate': True
                    })
                    
                except ShippingPartner.DoesNotExist:
                    return Response(
                        {'error': 'Shipping partner not found'},
                        status=status.HTTP_404_NOT_FOUND
                    )
                except ShippingException as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return Response(
                {'error': 'No shipping rates found for the given parameters'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate rates for each shipping partner
        results = []
        for rate in rates:
            # Calculate total rate
            total_rate = rate.base_rate
            
            # Add per kg rate
            if rate.per_kg_rate > 0:
                total_rate += rate.per_kg_rate * float(weight)
            
            # Get estimated delivery days from serviceable area
            try:
                area = ServiceableArea.objects.get(
                    shipping_partner=rate.shipping_partner,
                    pin_code=destination_pin_code
                )
                min_days = area.min_delivery_days
                max_days = area.max_delivery_days
            except ServiceableArea.DoesNotExist:
                min_days = 3  # Default values
                max_days = 7
            
            results.append({
                'shipping_partner': {
                    'id': rate.shipping_partner.id,
                    'name': rate.shipping_partner.name
                },
                'rate': total_rate,
                'min_delivery_days': min_days,
                'max_delivery_days': max_days,
                'is_dynamic_rate': False
            })
        
        return Response(results)