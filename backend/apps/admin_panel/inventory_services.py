"""
Advanced Inventory Management System services for comprehensive admin panel.
"""
import uuid
import pandas as pd
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.db import transaction, models
from django.db.models import Q, F, Sum, Avg, Count, Max, Min
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from typing import Dict, List, Optional, Tuple, Any
from apps.products.models import Product
from .inventory_models import (
    Warehouse, Supplier, InventoryLocation, InventoryItem, InventoryValuation, 
    InventoryAdjustment, InventoryTransfer, InventoryReservation, InventoryAlert, 
    InventoryAudit, InventoryAuditItem, InventoryForecast, InventoryOptimization,
    InventoryOptimizationItem
)
from .models import AdminUser


class InventoryTrackingService:
    """Service for real-time inventory tracking and stock level updates."""
    
    @staticmethod
    def get_real_time_stock_levels(warehouse_id: Optional[int] = None) -> Dict[str, Any]:
        """Get real-time stock levels across all or specific warehouse."""
        query = InventoryItem.objects.select_related('product', 'location__warehouse')
        
        if warehouse_id:
            query = query.filter(location__warehouse_id=warehouse_id)
        
        # Aggregate stock levels
        stock_data = query.aggregate(
            total_items=Count('id'),
            total_quantity=Sum('quantity'),
            available_quantity=Sum(F('quantity') - F('reserved_quantity')),
            reserved_quantity=Sum('reserved_quantity'),
            total_value=Sum(F('quantity') * F('unit_cost')),
            low_stock_count=Count('id', filter=Q(quantity__lte=F('product__inventory__reorder_point'))),
            out_of_stock_count=Count('id', filter=Q(quantity=0)),
            expired_count=Count('id', filter=Q(expiry_date__lt=date.today())),
        )
        
        return stock_data
    
    @staticmethod
    def update_stock_level(product_id: int, location_id: int, quantity_change: int, 
                          transaction_type: str, user: AdminUser, notes: str = "") -> InventoryItem:
        """Update stock level for a specific product and location."""
        with transaction.atomic():
            try:
                inventory_item = InventoryItem.objects.select_for_update().get(
                    product_id=product_id, location_id=location_id
                )
                
                # Update quantity
                new_quantity = inventory_item.quantity + quantity_change
                if new_quantity < 0:
                    raise ValidationError("Insufficient stock for this operation.")
                
                inventory_item.quantity = new_quantity
                inventory_item.save()
                
                # Create adjustment record
                InventoryAdjustmentService.create_automatic_adjustment(
                    product_id=product_id,
                    location_id=location_id,
                    quantity_before=inventory_item.quantity - quantity_change,
                    quantity_after=inventory_item.quantity,
                    reason_code=transaction_type,
                    reason_description=notes,
                    user=user
                )
                
                # Check for alerts
                InventoryAlertService.check_and_create_alerts(inventory_item)
                
                return inventory_item
                
            except InventoryItem.DoesNotExist:
                raise ValidationError("Inventory item not found.")
    
    @staticmethod
    def get_stock_movements(product_id: Optional[int] = None, 
                           location_id: Optional[int] = None,
                           date_from: Optional[date] = None,
                           date_to: Optional[date] = None) -> List[Dict[str, Any]]:
        """Get stock movement history with filters."""
        query = InventoryAdjustment.objects.select_related(
            'product', 'location', 'requested_by'
        ).filter(status='applied')
        
        if product_id:
            query = query.filter(product_id=product_id)
        if location_id:
            query = query.filter(location_id=location_id)
        if date_from:
            query = query.filter(applied_date__gte=date_from)
        if date_to:
            query = query.filter(applied_date__lte=date_to)
        
        movements = []
        for adjustment in query.order_by('-applied_date'):
            movements.append({
                'date': adjustment.applied_date,
                'product': adjustment.product.name,
                'location': adjustment.location.location_code,
                'type': adjustment.adjustment_type,
                'quantity_change': adjustment.adjustment_quantity,
                'reason': adjustment.reason_description,
                'user': adjustment.requested_by.username if adjustment.requested_by else 'System',
                'cost_impact': adjustment.total_cost_impact,
            })
        
        return movements


class InventoryValuationService:
    """Service for inventory valuation with different costing methods."""
    
    @staticmethod
    def calculate_fifo_valuation(product_id: int, warehouse_id: int, 
                                valuation_date: date = None) -> Dict[str, Any]:
        """Calculate inventory valuation using FIFO method."""
        if not valuation_date:
            valuation_date = date.today()
        
        # Get inventory items ordered by received date (FIFO)
        items = InventoryItem.objects.filter(
            product_id=product_id,
            location__warehouse_id=warehouse_id,
            is_available=True,
            received_date__lte=valuation_date
        ).order_by('received_date')
        
        total_quantity = sum(item.quantity for item in items)
        total_value = Decimal('0')
        
        for item in items:
            total_value += item.quantity * item.unit_cost
        
        unit_cost = total_value / total_quantity if total_quantity > 0 else Decimal('0')
        
        return {
            'total_quantity': total_quantity,
            'total_value': total_value,
            'unit_cost': unit_cost,
            'method': 'fifo'
        }
    
    @staticmethod
    def calculate_lifo_valuation(product_id: int, warehouse_id: int, 
                                valuation_date: date = None) -> Dict[str, Any]:
        """Calculate inventory valuation using LIFO method."""
        if not valuation_date:
            valuation_date = date.today()
        
        # Get inventory items ordered by received date (LIFO)
        items = InventoryItem.objects.filter(
            product_id=product_id,
            location__warehouse_id=warehouse_id,
            is_available=True,
            received_date__lte=valuation_date
        ).order_by('-received_date')
        
        total_quantity = sum(item.quantity for item in items)
        total_value = Decimal('0')
        
        for item in items:
            total_value += item.quantity * item.unit_cost
        
        unit_cost = total_value / total_quantity if total_quantity > 0 else Decimal('0')
        
        return {
            'total_quantity': total_quantity,
            'total_value': total_value,
            'unit_cost': unit_cost,
            'method': 'lifo'
        }
    
    @staticmethod
    def calculate_weighted_average_valuation(product_id: int, warehouse_id: int, 
                                           valuation_date: date = None) -> Dict[str, Any]:
        """Calculate inventory valuation using weighted average method."""
        if not valuation_date:
            valuation_date = date.today()
        
        items = InventoryItem.objects.filter(
            product_id=product_id,
            location__warehouse_id=warehouse_id,
            is_available=True,
            received_date__lte=valuation_date
        )
        
        total_quantity = 0
        total_value = Decimal('0')
        
        for item in items:
            total_quantity += item.quantity
            total_value += item.quantity * item.unit_cost
        
        unit_cost = total_value / total_quantity if total_quantity > 0 else Decimal('0')
        
        return {
            'total_quantity': total_quantity,
            'total_value': total_value,
            'unit_cost': unit_cost,
            'method': 'weighted_average'
        }
    
    @staticmethod
    def create_valuation_record(product_id: int, warehouse_id: int, 
                               costing_method: str, user: AdminUser) -> InventoryValuation:
        """Create a valuation record using specified costing method."""
        valuation_methods = {
            'fifo': InventoryValuationService.calculate_fifo_valuation,
            'lifo': InventoryValuationService.calculate_lifo_valuation,
            'weighted_average': InventoryValuationService.calculate_weighted_average_valuation,
        }
        
        if costing_method not in valuation_methods:
            raise ValidationError(f"Unsupported costing method: {costing_method}")
        
        valuation_data = valuation_methods[costing_method](product_id, warehouse_id)
        
        # Get additional cost breakdown (simplified for demo)
        material_cost = valuation_data['total_value'] * Decimal('0.7')  # 70% material
        labor_cost = valuation_data['total_value'] * Decimal('0.2')     # 20% labor
        overhead_cost = valuation_data['total_value'] * Decimal('0.1')  # 10% overhead
        
        valuation = InventoryValuation.objects.create(
            product_id=product_id,
            warehouse_id=warehouse_id,
            costing_method=costing_method,
            total_quantity=valuation_data['total_quantity'],
            available_quantity=valuation_data['total_quantity'],  # Simplified
            reserved_quantity=0,  # Simplified
            unit_cost=valuation_data['unit_cost'],
            total_value=valuation_data['total_value'],
            average_cost=valuation_data['unit_cost'],
            material_cost=material_cost,
            labor_cost=labor_cost,
            overhead_cost=overhead_cost,
            landed_cost=valuation_data['total_value'],
            calculated_by=user,
            calculation_method=f"Calculated using {costing_method} method"
        )
        
        return valuation


class InventoryAdjustmentService:
    """Service for inventory adjustments with approval workflows."""
    
    @staticmethod
    def create_adjustment_request(product_id: int, location_id: int, 
                                 quantity_after: int, adjustment_type: str,
                                 reason_code: str, reason_description: str,
                                 user: AdminUser, unit_cost: Decimal = None) -> InventoryAdjustment:
        """Create an inventory adjustment request."""
        try:
            inventory_item = InventoryItem.objects.get(
                product_id=product_id, location_id=location_id
            )
            quantity_before = inventory_item.quantity
        except InventoryItem.DoesNotExist:
            quantity_before = 0
        
        if unit_cost is None:
            try:
                unit_cost = inventory_item.unit_cost
            except:
                unit_cost = Decimal('0')
        
        adjustment = InventoryAdjustment.objects.create(
            product_id=product_id,
            location_id=location_id,
            adjustment_type=adjustment_type,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason_code=reason_code,
            reason_description=reason_description,
            unit_cost=unit_cost,
            requested_by=user,
            status='pending'
        )
        
        return adjustment
    
    @staticmethod
    def approve_adjustment(adjustment_id: int, user: AdminUser, 
                          notes: str = "") -> InventoryAdjustment:
        """Approve an inventory adjustment."""
        with transaction.atomic():
            adjustment = InventoryAdjustment.objects.select_for_update().get(
                id=adjustment_id, status='pending'
            )
            
            adjustment.status = 'approved'
            adjustment.approved_by = user
            adjustment.approved_date = timezone.now()
            if notes:
                adjustment.notes = notes
            adjustment.save()
            
            return adjustment
    
    @staticmethod
    def apply_adjustment(adjustment_id: int, user: AdminUser) -> InventoryAdjustment:
        """Apply an approved inventory adjustment."""
        with transaction.atomic():
            adjustment = InventoryAdjustment.objects.select_for_update().get(
                id=adjustment_id, status='approved'
            )
            
            # Update inventory item
            try:
                inventory_item = InventoryItem.objects.select_for_update().get(
                    product_id=adjustment.product_id,
                    location_id=adjustment.location_id
                )
                inventory_item.quantity = adjustment.quantity_after
                inventory_item.save()
            except InventoryItem.DoesNotExist:
                # Create new inventory item if it doesn't exist
                inventory_item = InventoryItem.objects.create(
                    product_id=adjustment.product_id,
                    location_id=adjustment.location_id,
                    quantity=adjustment.quantity_after,
                    unit_cost=adjustment.unit_cost
                )
            
            # Update adjustment status
            adjustment.status = 'applied'
            adjustment.applied_by = user
            adjustment.applied_date = timezone.now()
            adjustment.save()
            
            # Check for alerts
            InventoryAlertService.check_and_create_alerts(inventory_item)
            
            return adjustment
    
    @staticmethod
    def create_automatic_adjustment(product_id: int, location_id: int,
                                   quantity_before: int, quantity_after: int,
                                   reason_code: str, reason_description: str,
                                   user: AdminUser) -> InventoryAdjustment:
        """Create and automatically apply an adjustment (for system operations)."""
        try:
            inventory_item = InventoryItem.objects.get(
                product_id=product_id, location_id=location_id
            )
            unit_cost = inventory_item.unit_cost
        except InventoryItem.DoesNotExist:
            unit_cost = Decimal('0')
        
        adjustment = InventoryAdjustment.objects.create(
            product_id=product_id,
            location_id=location_id,
            adjustment_type='correction',
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            reason_code=reason_code,
            reason_description=reason_description,
            unit_cost=unit_cost,
            requested_by=user,
            approved_by=user,
            applied_by=user,
            status='applied',
            requested_date=timezone.now(),
            approved_date=timezone.now(),
            applied_date=timezone.now()
        )
        
        return adjustment


class InventoryTransferService:
    """Service for inventory transfers between locations."""
    
    @staticmethod
    def create_transfer_request(product_id: int, source_location_id: int,
                               destination_location_id: int, quantity: int,
                               reason: str, user: AdminUser) -> InventoryTransfer:
        """Create an inventory transfer request."""
        # Validate source has sufficient stock
        try:
            source_item = InventoryItem.objects.get(
                product_id=product_id, location_id=source_location_id
            )
            if source_item.available_quantity < quantity:
                raise ValidationError("Insufficient stock at source location.")
        except InventoryItem.DoesNotExist:
            raise ValidationError("Product not found at source location.")
        
        transfer = InventoryTransfer.objects.create(
            product_id=product_id,
            source_location_id=source_location_id,
            destination_location_id=destination_location_id,
            quantity_requested=quantity,
            reason=reason,
            requested_by=user,
            status='pending'
        )
        
        return transfer
    
    @staticmethod
    def ship_transfer(transfer_id: int, user: AdminUser, 
                     tracking_number: str = "") -> InventoryTransfer:
        """Mark transfer as shipped and reserve inventory."""
        with transaction.atomic():
            transfer = InventoryTransfer.objects.select_for_update().get(
                id=transfer_id, status='pending'
            )
            
            # Reserve inventory at source
            source_item = InventoryItem.objects.select_for_update().get(
                product_id=transfer.product_id,
                location_id=transfer.source_location_id
            )
            
            if source_item.available_quantity < transfer.quantity_requested:
                raise ValidationError("Insufficient available stock for transfer.")
            
            source_item.reserved_quantity += transfer.quantity_requested
            source_item.save()
            
            # Update transfer
            transfer.status = 'in_transit'
            transfer.quantity_shipped = transfer.quantity_requested
            transfer.shipped_by = user
            transfer.shipped_date = timezone.now()
            transfer.tracking_number = tracking_number
            transfer.save()
            
            return transfer
    
    @staticmethod
    def receive_transfer(transfer_id: int, quantity_received: int, 
                        user: AdminUser) -> InventoryTransfer:
        """Receive transfer and update inventory."""
        with transaction.atomic():
            transfer = InventoryTransfer.objects.select_for_update().get(
                id=transfer_id, status='in_transit'
            )
            
            # Update source inventory
            source_item = InventoryItem.objects.select_for_update().get(
                product_id=transfer.product_id,
                location_id=transfer.source_location_id
            )
            source_item.quantity -= quantity_received
            source_item.reserved_quantity -= transfer.quantity_shipped
            source_item.save()
            
            # Update or create destination inventory
            try:
                dest_item = InventoryItem.objects.select_for_update().get(
                    product_id=transfer.product_id,
                    location_id=transfer.destination_location_id
                )
                dest_item.quantity += quantity_received
                dest_item.save()
            except InventoryItem.DoesNotExist:
                dest_item = InventoryItem.objects.create(
                    product_id=transfer.product_id,
                    location_id=transfer.destination_location_id,
                    quantity=quantity_received,
                    unit_cost=source_item.unit_cost
                )
            
            # Update transfer
            transfer.quantity_received = quantity_received
            transfer.received_by = user
            transfer.received_date = timezone.now()
            transfer.status = 'completed' if quantity_received >= transfer.quantity_requested else 'partial'
            transfer.save()
            
            return transfer


class InventoryReservationService:
    """Service for inventory reservation system."""
    
    @staticmethod
    def create_reservation(product_id: int, location_id: int, quantity: int,
                          reservation_type: str, expiry_hours: int,
                          user: AdminUser, related_object=None,
                          priority: int = 1) -> InventoryReservation:
        """Create an inventory reservation."""
        # Check available quantity
        try:
            inventory_item = InventoryItem.objects.get(
                product_id=product_id, location_id=location_id
            )
            if inventory_item.available_quantity < quantity:
                raise ValidationError("Insufficient available stock for reservation.")
        except InventoryItem.DoesNotExist:
            raise ValidationError("Product not found at specified location.")
        
        expiry_date = timezone.now() + timedelta(hours=expiry_hours)
        
        reservation = InventoryReservation.objects.create(
            product_id=product_id,
            location_id=location_id,
            reservation_type=reservation_type,
            quantity_reserved=quantity,
            expiry_date=expiry_date,
            reserved_by=user,
            priority=priority
        )
        
        if related_object:
            reservation.content_object = related_object
            reservation.save()
        
        # Update reserved quantity
        with transaction.atomic():
            inventory_item = InventoryItem.objects.select_for_update().get(
                product_id=product_id, location_id=location_id
            )
            inventory_item.reserved_quantity += quantity
            inventory_item.save()
        
        return reservation
    
    @staticmethod
    def fulfill_reservation(reservation_id: int, quantity_fulfilled: int,
                           user: AdminUser) -> InventoryReservation:
        """Fulfill a reservation (partially or completely)."""
        with transaction.atomic():
            reservation = InventoryReservation.objects.select_for_update().get(
                id=reservation_id, status='active'
            )
            
            if quantity_fulfilled > reservation.remaining_quantity:
                raise ValidationError("Cannot fulfill more than remaining quantity.")
            
            # Update reservation
            reservation.quantity_fulfilled += quantity_fulfilled
            if reservation.quantity_fulfilled >= reservation.quantity_reserved:
                reservation.status = 'fulfilled'
                reservation.fulfilled_date = timezone.now()
            else:
                reservation.status = 'partial'
            reservation.save()
            
            # Update inventory
            inventory_item = InventoryItem.objects.select_for_update().get(
                product_id=reservation.product_id,
                location_id=reservation.location_id
            )
            inventory_item.quantity -= quantity_fulfilled
            inventory_item.reserved_quantity -= quantity_fulfilled
            inventory_item.save()
            
            return reservation
    
    @staticmethod
    def cancel_reservation(reservation_id: int, user: AdminUser) -> InventoryReservation:
        """Cancel a reservation and release reserved stock."""
        with transaction.atomic():
            reservation = InventoryReservation.objects.select_for_update().get(
                id=reservation_id, status__in=['active', 'partial']
            )
            
            remaining_quantity = reservation.remaining_quantity
            
            # Update reservation
            reservation.status = 'cancelled'
            reservation.save()
            
            # Release reserved stock
            inventory_item = InventoryItem.objects.select_for_update().get(
                product_id=reservation.product_id,
                location_id=reservation.location_id
            )
            inventory_item.reserved_quantity -= remaining_quantity
            inventory_item.save()
            
            return reservation
    
    @staticmethod
    def cleanup_expired_reservations() -> int:
        """Clean up expired reservations (to be run as scheduled task)."""
        expired_reservations = InventoryReservation.objects.filter(
            status='active',
            expiry_date__lt=timezone.now()
        )
        
        count = 0
        for reservation in expired_reservations:
            try:
                InventoryReservationService.cancel_reservation(
                    reservation.id, reservation.reserved_by
                )
                reservation.status = 'expired'
                reservation.save()
                count += 1
            except Exception:
                continue
        
        return count


class InventoryAlertService:
    """Service for inventory alert system."""
    
    @staticmethod
    def check_and_create_alerts(inventory_item: InventoryItem) -> List[InventoryAlert]:
        """Check inventory item and create alerts if needed."""
        alerts_created = []
        
        # Low stock alert
        try:
            reorder_point = inventory_item.product.inventory.reorder_point
            if inventory_item.quantity <= reorder_point:
                alert = InventoryAlertService.create_alert(
                    product=inventory_item.product,
                    location=inventory_item.location,
                    alert_type='low_stock',
                    severity='medium',
                    title=f'Low Stock Alert: {inventory_item.product.name}',
                    description=f'Stock level ({inventory_item.quantity}) is at or below reorder point ({reorder_point})',
                    current_value=inventory_item.quantity,
                    threshold_value=reorder_point
                )
                alerts_created.append(alert)
        except:
            pass
        
        # Out of stock alert
        if inventory_item.quantity == 0:
            alert = InventoryAlertService.create_alert(
                product=inventory_item.product,
                location=inventory_item.location,
                alert_type='out_of_stock',
                severity='high',
                title=f'Out of Stock: {inventory_item.product.name}',
                description=f'Product is completely out of stock at {inventory_item.location.location_code}',
                current_value=0,
                threshold_value=1
            )
            alerts_created.append(alert)
        
        # Expiring soon alert
        if inventory_item.expiry_date:
            days_until_expiry = (inventory_item.expiry_date - date.today()).days
            if 0 < days_until_expiry <= 30:  # Expiring within 30 days
                alert = InventoryAlertService.create_alert(
                    product=inventory_item.product,
                    location=inventory_item.location,
                    alert_type='expiring_soon',
                    severity='medium',
                    title=f'Expiring Soon: {inventory_item.product.name}',
                    description=f'Product expires in {days_until_expiry} days',
                    current_value=days_until_expiry,
                    threshold_value=30
                )
                alerts_created.append(alert)
            elif days_until_expiry <= 0:  # Already expired
                alert = InventoryAlertService.create_alert(
                    product=inventory_item.product,
                    location=inventory_item.location,
                    alert_type='expired',
                    severity='critical',
                    title=f'Expired Product: {inventory_item.product.name}',
                    description=f'Product expired {abs(days_until_expiry)} days ago',
                    current_value=days_until_expiry,
                    threshold_value=0
                )
                alerts_created.append(alert)
        
        return alerts_created
    
    @staticmethod
    def create_alert(product: Product, location: InventoryLocation,
                    alert_type: str, severity: str, title: str,
                    description: str, current_value: Decimal,
                    threshold_value: Decimal) -> InventoryAlert:
        """Create an inventory alert."""
        # Check if similar alert already exists and is active
        existing_alert = InventoryAlert.objects.filter(
            product=product,
            location=location,
            alert_type=alert_type,
            status='active'
        ).first()
        
        if existing_alert:
            # Update existing alert
            existing_alert.current_value = current_value
            existing_alert.description = description
            existing_alert.save()
            return existing_alert
        
        # Create new alert
        alert = InventoryAlert.objects.create(
            product=product,
            location=location,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            current_value=current_value,
            threshold_value=threshold_value
        )
        
        return alert
    
    @staticmethod
    def acknowledge_alert(alert_id: int, user: AdminUser, notes: str = "") -> InventoryAlert:
        """Acknowledge an alert."""
        alert = InventoryAlert.objects.get(id=alert_id, status='active')
        alert.status = 'acknowledged'
        alert.acknowledged_by = user
        alert.acknowledged_date = timezone.now()
        if notes:
            alert.notes = notes
        alert.save()
        return alert
    
    @staticmethod
    def resolve_alert(alert_id: int, user: AdminUser, notes: str = "") -> InventoryAlert:
        """Resolve an alert."""
        alert = InventoryAlert.objects.get(id=alert_id, status__in=['active', 'acknowledged'])
        alert.status = 'resolved'
        alert.resolved_by = user
        alert.resolved_date = timezone.now()
        if notes:
            alert.notes = notes
        alert.save()
        return alert


class InventoryOptimizationService:
    """Service for inventory optimization and ABC analysis."""
    
    @staticmethod
    def perform_abc_analysis(warehouse_id: int, user: AdminUser,
                            period_days: int = 365) -> InventoryOptimization:
        """Perform ABC analysis on inventory."""
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days)
        
        # Get products with usage data
        products_data = []
        products = Product.objects.filter(
            inventory_items__location__warehouse_id=warehouse_id
        ).distinct()
        
        for product in products:
            # Calculate annual usage (simplified - would use actual transaction data)
            current_stock = InventoryItem.objects.filter(
                product=product,
                location__warehouse_id=warehouse_id
            ).aggregate(
                total_quantity=Sum('quantity'),
                total_value=Sum(F('quantity') * F('unit_cost'))
            )
            
            # Mock usage calculation (in real implementation, use actual sales/usage data)
            annual_usage_quantity = current_stock['total_quantity'] or 0
            annual_usage_value = current_stock['total_value'] or Decimal('0')
            
            if annual_usage_value > 0:
                products_data.append({
                    'product': product,
                    'annual_usage_value': annual_usage_value,
                    'annual_usage_quantity': annual_usage_quantity,
                    'current_stock_value': current_stock['total_value'] or Decimal('0'),
                    'current_stock_quantity': current_stock['total_quantity'] or 0,
                })
        
        # Sort by annual usage value (descending)
        products_data.sort(key=lambda x: x['annual_usage_value'], reverse=True)
        
        # Calculate cumulative percentages
        total_value = sum(p['annual_usage_value'] for p in products_data)
        cumulative_value = Decimal('0')
        
        # Classify products
        for i, product_data in enumerate(products_data):
            cumulative_value += product_data['annual_usage_value']
            cumulative_percentage = (cumulative_value / total_value) * 100 if total_value > 0 else 0
            
            if cumulative_percentage <= 80:
                product_data['abc_category'] = 'A'
            elif cumulative_percentage <= 95:
                product_data['abc_category'] = 'B'
            else:
                product_data['abc_category'] = 'C'
        
        # Create optimization record
        optimization = InventoryOptimization.objects.create(
            analysis_type='abc',
            warehouse_id=warehouse_id,
            analysis_date=date.today(),
            period_start=start_date,
            period_end=end_date,
            total_products_analyzed=len(products_data),
            total_value_analyzed=total_value,
            analyzed_by=user,
            methodology="ABC Analysis based on annual usage value"
        )
        
        # Create optimization items
        category_counts = {'A': 0, 'B': 0, 'C': 0}
        category_values = {'A': Decimal('0'), 'B': Decimal('0'), 'C': Decimal('0')}
        
        for product_data in products_data:
            category = product_data['abc_category']
            category_counts[category] += 1
            category_values[category] += product_data['annual_usage_value']
            
            InventoryOptimizationItem.objects.create(
                optimization=optimization,
                product=product_data['product'],
                abc_category=category,
                annual_usage_value=product_data['annual_usage_value'],
                annual_usage_quantity=product_data['annual_usage_quantity'],
                current_stock_value=product_data['current_stock_value'],
                current_stock_quantity=product_data['current_stock_quantity'],
                turnover_rate=Decimal('12'),  # Simplified
                days_of_supply=Decimal('30'),  # Simplified
            )
        
        # Update optimization summary
        optimization.category_a_count = category_counts['A']
        optimization.category_b_count = category_counts['B']
        optimization.category_c_count = category_counts['C']
        optimization.category_a_value = category_values['A']
        optimization.category_b_value = category_values['B']
        optimization.category_c_value = category_values['C']
        optimization.save()
        
        return optimization
    
    @staticmethod
    def identify_slow_moving_items(warehouse_id: int, days_threshold: int = 90) -> List[Dict[str, Any]]:
        """Identify slow-moving inventory items."""
        cutoff_date = date.today() - timedelta(days=days_threshold)
        
        # Find items with no recent movement
        slow_moving_items = []
        items = InventoryItem.objects.filter(
            location__warehouse_id=warehouse_id,
            quantity__gt=0
        ).select_related('product', 'location')
        
        for item in items:
            # Check for recent adjustments (simplified - would check actual sales/usage)
            recent_activity = InventoryAdjustment.objects.filter(
                product=item.product,
                location=item.location,
                applied_date__gte=cutoff_date
            ).exists()
            
            if not recent_activity:
                slow_moving_items.append({
                    'product': item.product,
                    'location': item.location,
                    'quantity': item.quantity,
                    'value': item.quantity * item.unit_cost,
                    'days_since_movement': days_threshold,
                    'recommendation': 'Consider promotion or liquidation'
                })
        
        return slow_moving_items


class InventoryReportService:
    """Service for inventory reporting and analytics."""
    
    @staticmethod
    def generate_stock_levels_report(warehouse_id: Optional[int] = None,
                                   format: str = 'dict') -> Dict[str, Any]:
        """Generate stock levels report."""
        query = InventoryItem.objects.select_related('product', 'location__warehouse')
        
        if warehouse_id:
            query = query.filter(location__warehouse_id=warehouse_id)
        
        items = []
        for item in query:
            items.append({
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'location': item.location.location_code,
                'warehouse': item.location.warehouse.name,
                'quantity': item.quantity,
                'reserved_quantity': item.reserved_quantity,
                'available_quantity': item.available_quantity,
                'unit_cost': item.unit_cost,
                'total_value': item.quantity * item.unit_cost,
                'condition': item.condition,
                'expiry_date': item.expiry_date,
            })
        
        summary = {
            'total_items': len(items),
            'total_quantity': sum(item['quantity'] for item in items),
            'total_value': sum(item['total_value'] for item in items),
            'total_reserved': sum(item['reserved_quantity'] for item in items),
        }
        
        return {
            'summary': summary,
            'items': items,
            'generated_at': timezone.now(),
        }
    
    @staticmethod
    def generate_movement_report(warehouse_id: Optional[int] = None,
                               date_from: Optional[date] = None,
                               date_to: Optional[date] = None) -> Dict[str, Any]:
        """Generate inventory movement report."""
        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()
        
        query = InventoryAdjustment.objects.filter(
            applied_date__range=[date_from, date_to],
            status='applied'
        ).select_related('product', 'location__warehouse', 'requested_by')
        
        if warehouse_id:
            query = query.filter(location__warehouse_id=warehouse_id)
        
        movements = []
        for adjustment in query:
            movements.append({
                'date': adjustment.applied_date,
                'product_name': adjustment.product.name,
                'location': adjustment.location.location_code,
                'warehouse': adjustment.location.warehouse.name,
                'adjustment_type': adjustment.adjustment_type,
                'quantity_change': adjustment.adjustment_quantity,
                'reason': adjustment.reason_description,
                'user': adjustment.requested_by.username if adjustment.requested_by else 'System',
                'cost_impact': adjustment.total_cost_impact,
            })
        
        summary = {
            'total_movements': len(movements),
            'total_cost_impact': sum(m['cost_impact'] for m in movements),
            'period_start': date_from,
            'period_end': date_to,
        }
        
        return {
            'summary': summary,
            'movements': movements,
            'generated_at': timezone.now(),
        }


class InventoryImportExportService:
    """Service for inventory data import/export operations."""
    
    @staticmethod
    def import_inventory_data(file_path: str, import_type: str, 
                             warehouse_id: int, user: AdminUser,
                             validate_only: bool = False) -> Dict[str, Any]:
        """Import inventory data from file."""
        try:
            # Read file based on extension
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValidationError("Unsupported file format")
            
            results = {
                'total_rows': len(df),
                'processed': 0,
                'errors': [],
                'warnings': [],
            }
            
            if import_type == 'items':
                results.update(
                    InventoryImportExportService._import_inventory_items(
                        df, warehouse_id, user, validate_only
                    )
                )
            elif import_type == 'locations':
                results.update(
                    InventoryImportExportService._import_locations(
                        df, warehouse_id, user, validate_only
                    )
                )
            # Add more import types as needed
            
            return results
            
        except Exception as e:
            return {
                'total_rows': 0,
                'processed': 0,
                'errors': [f"Import failed: {str(e)}"],
                'warnings': [],
            }
    
    @staticmethod
    def _import_inventory_items(df: pd.DataFrame, warehouse_id: int, 
                               user: AdminUser, validate_only: bool) -> Dict[str, Any]:
        """Import inventory items from DataFrame."""
        processed = 0
        errors = []
        warnings = []
        
        required_columns = ['product_sku', 'location_code', 'quantity', 'unit_cost']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return {'processed': 0, 'errors': errors, 'warnings': warnings}
        
        for index, row in df.iterrows():
            try:
                # Validate product exists
                try:
                    product = Product.objects.get(sku=row['product_sku'])
                except Product.DoesNotExist:
                    errors.append(f"Row {index + 1}: Product with SKU '{row['product_sku']}' not found")
                    continue
                
                # Validate location exists
                try:
                    location = InventoryLocation.objects.get(
                        location_code=row['location_code'],
                        warehouse_id=warehouse_id
                    )
                except InventoryLocation.DoesNotExist:
                    errors.append(f"Row {index + 1}: Location '{row['location_code']}' not found")
                    continue
                
                # Validate numeric fields
                try:
                    quantity = int(row['quantity'])
                    unit_cost = Decimal(str(row['unit_cost']))
                except (ValueError, TypeError):
                    errors.append(f"Row {index + 1}: Invalid quantity or unit cost")
                    continue
                
                if not validate_only:
                    # Create or update inventory item
                    item, created = InventoryItem.objects.update_or_create(
                        product=product,
                        location=location,
                        defaults={
                            'quantity': quantity,
                            'unit_cost': unit_cost,
                            'serial_number': row.get('serial_number', ''),
                            'lot_number': row.get('lot_number', ''),
                            'batch_number': row.get('batch_number', ''),
                            'condition': row.get('condition', 'new'),
                        }
                    )
                    
                    if created:
                        processed += 1
                    else:
                        processed += 1
                        warnings.append(f"Row {index + 1}: Updated existing item")
                else:
                    processed += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {'processed': processed, 'errors': errors, 'warnings': warnings}
    
    @staticmethod
    def _import_locations(df: pd.DataFrame, warehouse_id: int, 
                         user: AdminUser, validate_only: bool) -> Dict[str, Any]:
        """Import inventory locations from DataFrame."""
        processed = 0
        errors = []
        warnings = []
        
        required_columns = ['zone', 'aisle', 'shelf']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
            return {'processed': 0, 'errors': errors, 'warnings': warnings}
        
        for index, row in df.iterrows():
            try:
                if not validate_only:
                    # Create location
                    location, created = InventoryLocation.objects.get_or_create(
                        warehouse_id=warehouse_id,
                        zone=row['zone'],
                        aisle=row['aisle'],
                        shelf=row['shelf'],
                        bin=row.get('bin', ''),
                        defaults={
                            'capacity': row.get('capacity', 100),
                            'location_type': row.get('location_type', 'standard'),
                        }
                    )
                    
                    if created:
                        processed += 1
                    else:
                        warnings.append(f"Row {index + 1}: Location already exists")
                else:
                    processed += 1
                    
            except Exception as e:
                errors.append(f"Row {index + 1}: {str(e)}")
        
        return {'processed': processed, 'errors': errors, 'warnings': warnings}
    
    @staticmethod
    def export_inventory_data(export_type: str, format: str = 'csv',
                             filters: Dict[str, Any] = None) -> str:
        """Export inventory data to file."""
        if export_type == 'stock_levels':
            data = InventoryReportService.generate_stock_levels_report(
                warehouse_id=filters.get('warehouse_id') if filters else None
            )
            df = pd.DataFrame(data['items'])
        elif export_type == 'movements':
            data = InventoryReportService.generate_movement_report(
                warehouse_id=filters.get('warehouse_id') if filters else None,
                date_from=filters.get('date_from') if filters else None,
                date_to=filters.get('date_to') if filters else None
            )
            df = pd.DataFrame(data['movements'])
        else:
            raise ValidationError(f"Unsupported export type: {export_type}")
        
        # Generate filename
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"inventory_{export_type}_{timestamp}.{format}"
        file_path = f"exports/{filename}"
        
        # Save file
        if format == 'csv':
            df.to_csv(file_path, index=False)
        elif format == 'excel':
            df.to_excel(file_path, index=False)
        else:
            raise ValidationError(f"Unsupported export format: {format}")
        
        return file_path