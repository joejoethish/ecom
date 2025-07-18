from django.db import transaction
from django.utils import timezone
from django.db.models import F, Sum
from django.core.exceptions import ValidationError

from .models import Inventory, InventoryTransaction, PurchaseOrder, PurchaseOrderItem, Warehouse, Supplier


class InventoryService:
    """
    Service class for handling inventory operations with business logic.
    """
    
    @staticmethod
    @transaction.atomic
    def bulk_update_inventory(inventory_updates, user, reference_number="", notes=""):
        """
        Update multiple inventory items in a single transaction.
        
        Args:
            inventory_updates: List of dictionaries with inventory_id and quantity
            user: User performing the action
            reference_number: Reference number for the updates
            notes: Additional notes
            
        Returns:
            list: List of created transactions
        """
        transactions = []
        
        for update in inventory_updates:
            inventory_id = update['inventory_id']
            quantity = update['quantity']
            
            try:
                inventory = Inventory.objects.get(id=inventory_id)
                
                # Determine if this is an addition or removal
                if quantity > 0:
                    transaction = InventoryService.add_stock(
                        inventory=inventory,
                        quantity=quantity,
                        user=user,
                        transaction_type="ADJUSTMENT",
                        reference_number=reference_number,
                        notes=f"Bulk update: {notes}"
                    )
                elif quantity < 0:
                    transaction = InventoryService.remove_stock(
                        inventory=inventory,
                        quantity=abs(quantity),
                        user=user,
                        transaction_type="ADJUSTMENT",
                        reference_number=reference_number,
                        notes=f"Bulk update: {notes}"
                    )
                else:
                    # Skip zero quantity updates
                    continue
                
                transactions.append(transaction)
                
            except Inventory.DoesNotExist:
                raise ValidationError(f"Inventory with ID {inventory_id} does not exist")
            except Exception as e:
                # Re-raise any other exceptions
                raise ValidationError(f"Error updating inventory {inventory_id}: {str(e)}")
        
        return transactions
    
    @staticmethod
    def update_alert_settings(inventory_id, minimum_stock_level=None, 
                             maximum_stock_level=None, reorder_point=None):
        """
        Update inventory alert settings.
        
        Args:
            inventory_id: ID of the inventory to update
            minimum_stock_level: New minimum stock level
            maximum_stock_level: New maximum stock level
            reorder_point: New reorder point
            
        Returns:
            Inventory: The updated inventory
        """
        try:
            inventory = Inventory.objects.get(id=inventory_id)
            
            if minimum_stock_level is not None:
                inventory.minimum_stock_level = minimum_stock_level
            
            if maximum_stock_level is not None:
                inventory.maximum_stock_level = maximum_stock_level
            
            if reorder_point is not None:
                inventory.reorder_point = reorder_point
            
            inventory.save()
            return inventory
            
        except Inventory.DoesNotExist:
            raise ValidationError(f"Inventory with ID {inventory_id} does not exist")
    
    @staticmethod
    def generate_inventory_report(report_type, start_date=None, end_date=None, 
                                 warehouse_id=None, product_id=None):
        """
        Generate inventory reports based on specified parameters.
        
        Args:
            report_type: Type of report ('stock_levels', 'movements', 'valuation', 'turnover')
            start_date: Start date for the report period
            end_date: End date for the report period
            warehouse_id: Filter by warehouse ID
            product_id: Filter by product ID
            
        Returns:
            dict: Report data
        """
        # Base queryset
        inventory_qs = Inventory.objects.all()
        transaction_qs = InventoryTransaction.objects.all()
        
        # Apply filters
        if warehouse_id:
            inventory_qs = inventory_qs.filter(warehouse_id=warehouse_id)
            transaction_qs = transaction_qs.filter(inventory__warehouse_id=warehouse_id)
        
        if product_id:
            inventory_qs = inventory_qs.filter(product_id=product_id)
            transaction_qs = transaction_qs.filter(inventory__product_id=product_id)
        
        if start_date:
            transaction_qs = transaction_qs.filter(created_at__gte=start_date)
        
        if end_date:
            transaction_qs = transaction_qs.filter(created_at__lte=end_date)
        
        # Generate report based on type
        if report_type == 'stock_levels':
            return InventoryService._generate_stock_levels_report(inventory_qs)
        elif report_type == 'movements':
            return InventoryService._generate_movements_report(transaction_qs)
        elif report_type == 'valuation':
            return InventoryService._generate_valuation_report(inventory_qs)
        elif report_type == 'turnover':
            return InventoryService._generate_turnover_report(inventory_qs, transaction_qs, start_date, end_date)
        else:
            raise ValidationError(f"Invalid report type: {report_type}")
    
    @staticmethod
    def _generate_stock_levels_report(inventory_qs):
        """Generate stock levels report."""
        total_items = inventory_qs.count()
        total_quantity = inventory_qs.aggregate(total=Sum('quantity'))['total'] or 0
        total_reserved = inventory_qs.aggregate(total=Sum('reserved_quantity'))['total'] or 0
        
        low_stock_count = inventory_qs.filter(
            quantity__lte=F('reorder_point'),
            quantity__gt=0
        ).count()
        
        out_of_stock_count = inventory_qs.filter(quantity__lte=0).count()
        
        overstock_count = inventory_qs.filter(
            quantity__gte=F('maximum_stock_level')
        ).count()
        
        # Get detailed inventory data
        inventory_data = inventory_qs.values(
            'id', 'product__name', 'warehouse__name', 
            'quantity', 'reserved_quantity', 'minimum_stock_level',
            'maximum_stock_level', 'reorder_point'
        )
        
        return {
            'summary': {
                'total_items': total_items,
                'total_quantity': total_quantity,
                'total_reserved': total_reserved,
                'available_quantity': total_quantity - total_reserved,
                'low_stock_count': low_stock_count,
                'out_of_stock_count': out_of_stock_count,
                'overstock_count': overstock_count
            },
            'details': list(inventory_data)
        }
    
    @staticmethod
    def _generate_movements_report(transaction_qs):
        """Generate inventory movements report."""
        total_transactions = transaction_qs.count()
        
        # Aggregate by transaction type
        transactions_by_type = transaction_qs.values(
            'transaction_type'
        ).annotate(
            count=Count('id'),
            total_quantity=Sum('quantity')
        )
        
        # Get detailed transaction data
        transaction_data = transaction_qs.values(
            'id', 'inventory__product__name', 'inventory__warehouse__name',
            'transaction_type', 'quantity', 'reference_number',
            'created_at', 'created_by__username'
        ).order_by('-created_at')
        
        return {
            'summary': {
                'total_transactions': total_transactions,
                'transactions_by_type': list(transactions_by_type)
            },
            'details': list(transaction_data)
        }
    
    @staticmethod
    def _generate_valuation_report(inventory_qs):
        """Generate inventory valuation report."""
        # Calculate total value
        total_value = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        
        # Calculate value by warehouse
        warehouse_values = inventory_qs.values(
            'warehouse__id', 'warehouse__name'
        ).annotate(
            total_items=Count('id'),
            total_quantity=Sum('quantity'),
            total_value=Sum(F('quantity') * F('cost_price'))
        )
        
        # Get detailed valuation data
        valuation_data = inventory_qs.annotate(
            value=F('quantity') * F('cost_price')
        ).values(
            'id', 'product__name', 'warehouse__name',
            'quantity', 'cost_price', 'value'
        ).order_by('-value')
        
        return {
            'summary': {
                'total_value': total_value,
                'warehouse_values': list(warehouse_values)
            },
            'details': list(valuation_data)
        }
    
    @staticmethod
    def _generate_turnover_report(inventory_qs, transaction_qs, start_date, end_date):
        """Generate inventory turnover report."""
        # Calculate beginning inventory
        beginning_inventory = 0
        if start_date:
            # Sum of quantities before start date
            beginning_transactions = InventoryTransaction.objects.filter(
                created_at__lt=start_date
            )
            if transaction_qs.model._meta.db_table != beginning_transactions.model._meta.db_table:
                # Apply the same filters as transaction_qs except date filters
                for q in transaction_qs.query.where.children:
                    if not any(x in str(q) for x in ['created_at__gte', 'created_at__lte']):
                        beginning_transactions = beginning_transactions.filter(q)
            
            beginning_inventory = beginning_transactions.aggregate(
                total=Sum('quantity')
            )['total'] or 0
        
        # Calculate ending inventory
        ending_inventory = beginning_inventory + transaction_qs.aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        # Calculate average inventory
        average_inventory = (beginning_inventory + ending_inventory) / 2 if average_inventory != 0 else 0
        
        # Calculate cost of goods sold (sum of negative transactions)
        cogs = transaction_qs.filter(
            quantity__lt=0
        ).aggregate(
            total=Sum('total_cost')
        )['total'] or 0
        
        # Calculate turnover ratio
        turnover_ratio = abs(cogs) / average_inventory if average_inventory != 0 else 0
        
        # Get product-level turnover data
        product_turnover = []
        for inventory in inventory_qs:
            product_transactions = transaction_qs.filter(inventory__product=inventory.product)
            
            product_cogs = product_transactions.filter(
                quantity__lt=0
            ).aggregate(
                total=Sum('total_cost')
            )['total'] or 0
            
            product_turnover.append({
                'product_id': inventory.product.id,
                'product_name': inventory.product.name,
                'beginning_inventory': beginning_inventory,
                'ending_inventory': ending_inventory,
                'average_inventory': average_inventory,
                'cogs': abs(product_cogs),
                'turnover_ratio': abs(product_cogs) / average_inventory if average_inventory != 0 else 0
            })
        
        return {
            'summary': {
                'beginning_inventory': beginning_inventory,
                'ending_inventory': ending_inventory,
                'average_inventory': average_inventory,
                'cogs': abs(cogs),
                'turnover_ratio': turnover_ratio
            },
            'product_turnover': product_turnover
        }
    
    @staticmethod
    @transaction.atomic
    def add_stock(inventory, quantity, user, transaction_type="PURCHASE", reference_number="", 
                  batch_number="", expiry_date=None, unit_cost=None, notes=""):
        """
        Add stock to inventory with transaction tracking.
        
        Args:
            inventory: Inventory instance
            quantity: Quantity to add (positive integer)
            user: User performing the action
            transaction_type: Type of transaction (default: PURCHASE)
            reference_number: Reference number for the transaction
            batch_number: Batch number for tracking
            expiry_date: Expiry date for the batch
            unit_cost: Unit cost of the items
            notes: Additional notes
            
        Returns:
            InventoryTransaction: The created transaction
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive when adding stock")
        
        # Update inventory quantity
        inventory.quantity = F('quantity') + quantity
        inventory.last_restocked = timezone.now()
        inventory.save()
        inventory.refresh_from_db()  # Refresh to get the updated quantity
        
        # Create transaction record
        transaction = InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=transaction_type,
            quantity=quantity,  # Positive for additions
            reference_number=reference_number,
            batch_number=batch_number,
            expiry_date=expiry_date,
            unit_cost=unit_cost,
            notes=notes,
            created_by=user
        )
        
        return transaction
    
    @staticmethod
    @transaction.atomic
    def remove_stock(inventory, quantity, user, transaction_type="SALE", reference_number="", 
                     order=None, notes=""):
        """
        Remove stock from inventory with transaction tracking.
        
        Args:
            inventory: Inventory instance
            quantity: Quantity to remove (positive integer)
            user: User performing the action
            transaction_type: Type of transaction (default: SALE)
            reference_number: Reference number for the transaction
            order: Related order if applicable
            notes: Additional notes
            
        Returns:
            InventoryTransaction: The created transaction
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive when removing stock")
        
        if inventory.available_quantity < quantity:
            raise ValidationError(f"Insufficient stock. Available: {inventory.available_quantity}, Requested: {quantity}")
        
        # Update inventory quantity
        inventory.quantity = F('quantity') - quantity
        inventory.save()
        inventory.refresh_from_db()  # Refresh to get the updated quantity
        
        # Create transaction record
        transaction = InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type=transaction_type,
            quantity=-quantity,  # Negative for removals
            reference_number=reference_number,
            order=order,
            notes=notes,
            created_by=user
        )
        
        return transaction
    
    @staticmethod
    @transaction.atomic
    def reserve_stock(inventory, quantity, user, reference_number="", order=None, notes=""):
        """
        Reserve stock without removing it from inventory.
        
        Args:
            inventory: Inventory instance
            quantity: Quantity to reserve (positive integer)
            user: User performing the action
            reference_number: Reference number for the reservation
            order: Related order if applicable
            notes: Additional notes
            
        Returns:
            bool: True if reservation was successful
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive when reserving stock")
        
        if inventory.available_quantity < quantity:
            raise ValidationError(f"Insufficient stock to reserve. Available: {inventory.available_quantity}, Requested: {quantity}")
        
        # Update reserved quantity
        inventory.reserved_quantity = F('reserved_quantity') + quantity
        inventory.save()
        inventory.refresh_from_db()
        
        # Create transaction record for audit trail
        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type="ADJUSTMENT",
            quantity=0,  # Net quantity change is 0 for reservations
            reference_number=reference_number,
            order=order,
            notes=f"Reserved {quantity} units. {notes}",
            created_by=user
        )
        
        return True
    
    @staticmethod
    @transaction.atomic
    def release_reserved_stock(inventory, quantity, user, reference_number="", order=None, notes=""):
        """
        Release previously reserved stock.
        
        Args:
            inventory: Inventory instance
            quantity: Quantity to release (positive integer)
            user: User performing the action
            reference_number: Reference number for the release
            order: Related order if applicable
            notes: Additional notes
            
        Returns:
            bool: True if release was successful
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive when releasing reserved stock")
        
        if inventory.reserved_quantity < quantity:
            raise ValidationError(f"Cannot release more than reserved. Reserved: {inventory.reserved_quantity}, Requested: {quantity}")
        
        # Update reserved quantity
        inventory.reserved_quantity = F('reserved_quantity') - quantity
        inventory.save()
        inventory.refresh_from_db()
        
        # Create transaction record for audit trail
        InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type="ADJUSTMENT",
            quantity=0,  # Net quantity change is 0 for releases
            reference_number=reference_number,
            order=order,
            notes=f"Released {quantity} reserved units. {notes}",
            created_by=user
        )
        
        return True
    
    @staticmethod
    @transaction.atomic
    def transfer_stock(source_inventory, destination_inventory, quantity, user, reference_number="", notes=""):
        """
        Transfer stock between warehouses.
        
        Args:
            source_inventory: Source Inventory instance
            destination_inventory: Destination Inventory instance
            quantity: Quantity to transfer (positive integer)
            user: User performing the action
            reference_number: Reference number for the transfer
            notes: Additional notes
            
        Returns:
            tuple: (source_transaction, destination_transaction)
        """
        if quantity <= 0:
            raise ValidationError("Quantity must be positive when transferring stock")
        
        if source_inventory.product.id != destination_inventory.product.id:
            raise ValidationError("Cannot transfer between different products")
        
        if source_inventory.available_quantity < quantity:
            raise ValidationError(f"Insufficient stock to transfer. Available: {source_inventory.available_quantity}, Requested: {quantity}")
        
        # Remove from source
        source_transaction = InventoryTransaction.objects.create(
            inventory=source_inventory,
            transaction_type="TRANSFER",
            quantity=-quantity,
            reference_number=reference_number,
            source_warehouse=source_inventory.warehouse,
            destination_warehouse=destination_inventory.warehouse,
            notes=notes,
            created_by=user
        )
        
        # Add to destination
        destination_transaction = InventoryTransaction.objects.create(
            inventory=destination_inventory,
            transaction_type="TRANSFER",
            quantity=quantity,
            reference_number=reference_number,
            source_warehouse=source_inventory.warehouse,
            destination_warehouse=destination_inventory.warehouse,
            notes=notes,
            created_by=user
        )
        
        # Update quantities
        source_inventory.quantity = F('quantity') - quantity
        source_inventory.save()
        
        destination_inventory.quantity = F('quantity') + quantity
        destination_inventory.save()
        
        # Refresh from database
        source_inventory.refresh_from_db()
        destination_inventory.refresh_from_db()
        
        return (source_transaction, destination_transaction)
    
    @staticmethod
    @transaction.atomic
    def adjust_inventory(inventory, adjustment_quantity, user, reason, reference_number="", notes=""):
        """
        Make inventory adjustments (for discrepancies, damages, etc.).
        
        Args:
            inventory: Inventory instance
            adjustment_quantity: Quantity to adjust (positive or negative)
            user: User performing the action
            reason: Reason for adjustment
            reference_number: Reference number for the adjustment
            notes: Additional notes
            
        Returns:
            InventoryTransaction: The created transaction
        """
        if adjustment_quantity == 0:
            raise ValidationError("Adjustment quantity cannot be zero")
        
        if adjustment_quantity < 0 and abs(adjustment_quantity) > inventory.quantity:
            raise ValidationError(f"Cannot adjust more than available. Available: {inventory.quantity}, Adjustment: {adjustment_quantity}")
        
        # Update inventory quantity
        inventory.quantity = F('quantity') + adjustment_quantity
        inventory.save()
        inventory.refresh_from_db()
        
        # Create transaction record
        transaction = InventoryTransaction.objects.create(
            inventory=inventory,
            transaction_type="ADJUSTMENT",
            quantity=adjustment_quantity,
            reference_number=reference_number,
            notes=f"Reason: {reason}. {notes}",
            created_by=user
        )
        
        return transaction
    
    @staticmethod
    def get_low_stock_items():
        """
        Get all inventory items that are at or below their reorder point.
        
        Returns:
            QuerySet: Inventory items with low stock
        """
        return Inventory.objects.filter(quantity__lte=F('reorder_point'))
    
    @staticmethod
    def get_overstock_items():
        """
        Get all inventory items that are at or above their maximum stock level.
        
        Returns:
            QuerySet: Inventory items with overstock
        """
        return Inventory.objects.filter(quantity__gte=F('maximum_stock_level'))
    
    @staticmethod
    def get_stock_value():
        """
        Calculate the total value of all inventory.
        
        Returns:
            dict: Dictionary with total value and breakdown by warehouse
        """
        total_value = Inventory.objects.annotate(
            value=F('quantity') * F('cost_price')
        ).aggregate(total=Sum('value'))['total'] or 0
        
        warehouse_values = Warehouse.objects.annotate(
            inventory_value=Sum(F('inventories__quantity') * F('inventories__cost_price'))
        ).values('id', 'name', 'inventory_value')
        
        return {
            'total_value': total_value,
            'warehouse_breakdown': warehouse_values
        }


class PurchaseOrderService:
    """
    Service class for handling purchase order operations.
    """
    
    @staticmethod
    @transaction.atomic
    def create_purchase_order(supplier_id, warehouse_id, items, user, notes="", expected_delivery_date=None):
        """
        Create a new purchase order.
        
        Args:
            supplier_id: ID of the supplier
            warehouse_id: ID of the warehouse
            items: List of dictionaries with product_id, quantity, and unit_price
            user: User creating the purchase order
            notes: Additional notes
            expected_delivery_date: Expected delivery date
            
        Returns:
            PurchaseOrder: The created purchase order
        """
        supplier = Supplier.objects.get(id=supplier_id)
        warehouse = Warehouse.objects.get(id=warehouse_id)
        
        # Generate PO number (could be more sophisticated in production)
        po_number = f"PO-{timezone.now().strftime('%Y%m%d')}-{PurchaseOrder.objects.count() + 1}"
        
        # Create purchase order
        purchase_order = PurchaseOrder.objects.create(
            po_number=po_number,
            supplier=supplier,
            warehouse=warehouse,
            expected_delivery_date=expected_delivery_date,
            notes=notes,
            created_by=user
        )
        
        # Create purchase order items
        total_amount = 0
        for item in items:
            po_item = PurchaseOrderItem.objects.create(
                purchase_order=purchase_order,
                product_id=item['product_id'],
                quantity_ordered=item['quantity'],
                unit_price=item['unit_price']
            )
            total_amount += po_item.total_price
        
        # Update total amount
        purchase_order.total_amount = total_amount
        purchase_order.save()
        
        return purchase_order
    
    @staticmethod
    @transaction.atomic
    def receive_purchase_order(purchase_order_id, received_items, user, notes=""):
        """
        Receive items from a purchase order.
        
        Args:
            purchase_order_id: ID of the purchase order
            received_items: Dictionary mapping PO item IDs to received quantities
            user: User receiving the items
            notes: Additional notes
            
        Returns:
            PurchaseOrder: The updated purchase order
        """
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        
        if purchase_order.status == "CANCELLED":
            raise ValidationError("Cannot receive items for a cancelled purchase order")
        
        if purchase_order.status == "RECEIVED":
            raise ValidationError("Purchase order has already been fully received")
        
        # Process each received item
        all_completed = True
        for po_item_id, received_quantity in received_items.items():
            po_item = PurchaseOrderItem.objects.get(id=po_item_id)
            
            if received_quantity <= 0:
                continue  # Skip items with no received quantity
            
            # Ensure we don't receive more than ordered
            if po_item.quantity_received + received_quantity > po_item.quantity_ordered:
                raise ValidationError(f"Cannot receive more than ordered for {po_item.product.name}")
            
            # Update received quantity
            po_item.quantity_received += received_quantity
            
            # Check if item is fully received
            if po_item.quantity_received >= po_item.quantity_ordered:
                po_item.is_completed = True
            else:
                all_completed = False
            
            po_item.save()
            
            # Get or create inventory for this product in the warehouse
            inventory, created = Inventory.objects.get_or_create(
                product=po_item.product,
                warehouse=purchase_order.warehouse,
                defaults={
                    'quantity': 0,
                    'cost_price': po_item.unit_price,
                    'supplier': purchase_order.supplier
                }
            )
            
            # Add stock to inventory
            InventoryService.add_stock(
                inventory=inventory,
                quantity=received_quantity,
                user=user,
                transaction_type="PURCHASE",
                reference_number=purchase_order.po_number,
                unit_cost=po_item.unit_price,
                notes=f"Received from PO: {purchase_order.po_number}. {notes}"
            )
        
        # Update purchase order status
        if all_completed:
            purchase_order.status = "RECEIVED"
            purchase_order.actual_delivery_date = timezone.now().date()
        else:
            purchase_order.status = "PARTIAL"
        
        purchase_order.save()
        
        return purchase_order
    
    @staticmethod
    @transaction.atomic
    def cancel_purchase_order(purchase_order_id, user, reason):
        """
        Cancel a purchase order.
        
        Args:
            purchase_order_id: ID of the purchase order
            user: User cancelling the order
            reason: Reason for cancellation
            
        Returns:
            PurchaseOrder: The cancelled purchase order
        """
        purchase_order = PurchaseOrder.objects.get(id=purchase_order_id)
        
        if purchase_order.status in ["RECEIVED", "CANCELLED"]:
            raise ValidationError(f"Cannot cancel a purchase order with status: {purchase_order.status}")
        
        # Update status and add cancellation notes
        purchase_order.status = "CANCELLED"
        purchase_order.notes += f"\n\nCancelled by {user.username} on {timezone.now()}. Reason: {reason}"
        purchase_order.save()
        
        return purchase_order