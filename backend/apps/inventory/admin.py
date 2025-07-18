from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import (
    Inventory, InventoryTransaction, Supplier, 
    Warehouse, PurchaseOrder, PurchaseOrderItem
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'contact_person', 'email', 'phone', 'lead_time_days', 'reliability_rating', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'contact_person', 'email', 'phone')
    ordering = ('name',)
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'is_active')
        }),
        (_('Contact Information'), {
            'fields': ('contact_person', 'email', 'phone', 'address', 'website')
        }),
        (_('Performance Metrics'), {
            'fields': ('lead_time_days', 'reliability_rating')
        }),
        (_('Financial Information'), {
            'fields': ('payment_terms', 'currency')
        }),
    )


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'location', 'capacity', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'location', 'address')
    ordering = ('name',)
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'code', 'is_active')
        }),
        (_('Location Information'), {
            'fields': ('location', 'address')
        }),
        (_('Contact Information'), {
            'fields': ('contact_person', 'email', 'phone')
        }),
        (_('Capacity'), {
            'fields': ('capacity',)
        }),
    )


class InventoryTransactionInline(admin.TabularInline):
    model = InventoryTransaction
    extra = 0
    readonly_fields = ('transaction_type', 'quantity', 'reference_number', 'created_by', 'created_at')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity', 'reserved_quantity', 'available_quantity', 'stock_status', 'last_restocked')
    list_filter = ('warehouse', 'last_restocked', 'supplier')
    search_fields = ('product__name', 'product__sku', 'warehouse__name')
    readonly_fields = ('available_quantity', 'stock_status', 'stock_value')
    inlines = [InventoryTransactionInline]
    actions = ['mark_for_reorder', 'export_to_csv', 'update_cost_prices']
    
    def stock_value(self, obj):
        """Calculate the total value of this inventory item."""
        return obj.quantity * obj.cost_price
    stock_value.short_description = _('Stock Value')
    
    def mark_for_reorder(self, request, queryset):
        """Mark selected inventory items for reorder."""
        from django.contrib import messages
        
        # Create a list of products that need reordering
        reorder_list = []
        for inventory in queryset:
            if inventory.quantity <= inventory.reorder_point:
                reorder_list.append(f"{inventory.product.name} ({inventory.warehouse.name}): {inventory.quantity} units")
        
        if reorder_list:
            message = _("The following items need to be reordered:\n") + "\n".join(reorder_list)
            self.message_user(request, message, messages.WARNING)
        else:
            self.message_user(request, _("No items selected are below reorder point."), messages.INFO)
    mark_for_reorder.short_description = _("Mark selected items for reorder")
    
    def export_to_csv(self, request, queryset):
        """Export selected inventory items to CSV."""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="inventory_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Product ID', 'Product Name', 'SKU', 'Warehouse', 'Quantity', 
            'Reserved', 'Available', 'Minimum Level', 'Maximum Level', 
            'Reorder Point', 'Cost Price', 'Value', 'Last Restocked'
        ])
        
        for inventory in queryset:
            writer.writerow([
                inventory.product.id,
                inventory.product.name,
                inventory.product.sku if hasattr(inventory.product, 'sku') else '',
                inventory.warehouse.name,
                inventory.quantity,
                inventory.reserved_quantity,
                inventory.available_quantity,
                inventory.minimum_stock_level,
                inventory.maximum_stock_level,
                inventory.reorder_point,
                inventory.cost_price,
                inventory.quantity * inventory.cost_price,
                inventory.last_restocked.strftime('%Y-%m-%d %H:%M:%S') if inventory.last_restocked else ''
            ])
        
        return response
    export_to_csv.short_description = _("Export selected items to CSV")
    
    def update_cost_prices(self, request, queryset):
        """Bulk update cost prices for selected inventory items."""
        from django.contrib import messages
        
        selected = queryset.count()
        if selected:
            self.message_user(
                request, 
                _("Please use the bulk update form to update cost prices for %d selected items.") % selected,
                messages.INFO
            )
        else:
            self.message_user(request, _("No items selected for cost price update."), messages.WARNING)
    update_cost_prices.short_description = _("Update cost prices")
    
    fieldsets = (
        (_('Product Information'), {
            'fields': ('product', 'warehouse', 'supplier')
        }),
        (_('Stock Levels'), {
            'fields': ('quantity', 'reserved_quantity', 'available_quantity', 'stock_status')
        }),
        (_('Thresholds'), {
            'fields': ('minimum_stock_level', 'maximum_stock_level', 'reorder_point')
        }),
        (_('Cost Information'), {
            'fields': ('cost_price', 'stock_value')
        }),
        (_('Timestamps'), {
            'fields': ('last_restocked', 'created_at', 'updated_at')
        }),
    )


@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'transaction_type', 'quantity', 'reference_number', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    search_fields = ('inventory__product__name', 'reference_number', 'batch_number', 'notes')
    readonly_fields = ('created_at',)
    fieldsets = (
        (_('Transaction Information'), {
            'fields': ('inventory', 'transaction_type', 'quantity', 'reference_number')
        }),
        (_('Related Entities'), {
            'fields': ('order', 'source_warehouse', 'destination_warehouse')
        }),
        (_('Batch Information'), {
            'fields': ('batch_number', 'expiry_date')
        }),
        (_('Cost Information'), {
            'fields': ('unit_cost', 'total_cost')
        }),
        (_('Notes and Audit'), {
            'fields': ('notes', 'created_by', 'created_at')
        }),
    )


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1
    fields = ('product', 'quantity_ordered', 'quantity_received', 'unit_price', 'total_price', 'is_completed')
    readonly_fields = ('total_price', 'is_completed')


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'warehouse', 'status', 'order_date', 'expected_delivery_date', 'total_amount')
    list_filter = ('status', 'order_date', 'expected_delivery_date')
    search_fields = ('po_number', 'supplier__name', 'warehouse__name', 'notes')
    readonly_fields = ('po_number', 'order_date', 'created_at', 'updated_at')
    inlines = [PurchaseOrderItemInline]
    fieldsets = (
        (_('Order Information'), {
            'fields': ('po_number', 'supplier', 'warehouse', 'status')
        }),
        (_('Dates'), {
            'fields': ('order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        (_('Financial Information'), {
            'fields': ('total_amount', 'tax_amount', 'shipping_cost')
        }),
        (_('Notes and Audit'), {
            'fields': ('notes', 'created_by', 'approved_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity_ordered', 'quantity_received', 'unit_price', 'total_price', 'is_completed')
    list_filter = ('is_completed',)
    search_fields = ('purchase_order__po_number', 'product__name', 'product__sku')
    readonly_fields = ('total_price', 'is_completed')
    fieldsets = (
        (_('Order Information'), {
            'fields': ('purchase_order', 'product')
        }),
        (_('Quantity Information'), {
            'fields': ('quantity_ordered', 'quantity_received', 'is_completed')
        }),
        (_('Price Information'), {
            'fields': ('unit_price', 'total_price')
        }),
    )