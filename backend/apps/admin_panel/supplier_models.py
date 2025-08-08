"""
Comprehensive Supplier and Vendor Management System Models
"""
import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from core.models import TimestampedModel
from .models import AdminUser


class SupplierCategory(TimestampedModel):
    """
    Categories for organizing suppliers by type/industry.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'supplier_categories'
        verbose_name = 'Supplier Category'
        verbose_name_plural = 'Supplier Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class SupplierProfile(TimestampedModel):
    """
    Comprehensive supplier profiles with contact information and performance metrics.
    """
    SUPPLIER_TYPE_CHOICES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
        ('dropshipper', 'Dropshipper'),
        ('service_provider', 'Service Provider'),
        ('consultant', 'Consultant'),
        ('contractor', 'Contractor'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
        ('under_review', 'Under Review'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    supplier_code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPE_CHOICES)
    category = models.ForeignKey(SupplierCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact Information
    primary_contact_name = models.CharField(max_length=100)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
        )]
    )
    
    # Address Information
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Business Information
    tax_id = models.CharField(max_length=50, blank=True)
    business_license = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    established_date = models.DateField(null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Status and Classification
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES, default='medium')
    is_preferred = models.BooleanField(default=False)
    is_certified = models.BooleanField(default=False)
    is_minority_owned = models.BooleanField(default=False)
    is_woman_owned = models.BooleanField(default=False)
    is_veteran_owned = models.BooleanField(default=False)
    
    # Performance Metrics
    overall_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    quality_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    delivery_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    service_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    
    # Financial Information
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_terms_days = models.IntegerField(default=30)
    discount_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Operational Information
    lead_time_days = models.IntegerField(default=7)
    minimum_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    capacity_rating = models.IntegerField(
        default=100,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Compliance and Certifications
    iso_certified = models.BooleanField(default=False)
    iso_certifications = models.JSONField(default=list, blank=True)
    compliance_status = models.CharField(max_length=20, default='compliant')
    last_audit_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    
    # ESG (Environmental, Social, Governance)
    sustainability_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=Decimal('0.00'),
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    carbon_footprint_score = models.IntegerField(null=True, blank=True)
    social_responsibility_score = models.IntegerField(null=True, blank=True)
    
    # Metadata
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='created_suppliers')
    last_modified_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='modified_suppliers')
    notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'supplier_profiles'
        verbose_name = 'Supplier Profile'
        verbose_name_plural = 'Supplier Profiles'
        ordering = ['name']
        indexes = [
            models.Index(fields=['supplier_code']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
            models.Index(fields=['supplier_type']),
            models.Index(fields=['risk_level']),
            models.Index(fields=['is_preferred']),
            models.Index(fields=['overall_rating']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.supplier_code} - {self.name}"

    @property
    def total_orders(self):
        """Get total number of purchase orders."""
        return self.purchase_orders.count()

    @property
    def total_spent(self):
        """Get total amount spent with this supplier."""
        return self.purchase_orders.aggregate(
            total=models.Sum('total_amount')
        )['total'] or Decimal('0.00')

    @property
    def average_delivery_time(self):
        """Calculate average delivery time in days."""
        completed_orders = self.purchase_orders.filter(
            status='completed',
            delivered_date__isnull=False
        )
        if not completed_orders.exists():
            return None
        
        total_days = sum([
            (order.delivered_date - order.created_at.date()).days
            for order in completed_orders
        ])
        return total_days / completed_orders.count()


class SupplierContact(TimestampedModel):
    """
    Additional contacts for suppliers beyond primary contact.
    """
    CONTACT_TYPE_CHOICES = [
        ('primary', 'Primary Contact'),
        ('sales', 'Sales Representative'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing Contact'),
        ('shipping', 'Shipping Contact'),
        ('quality', 'Quality Assurance'),
        ('management', 'Management'),
        ('emergency', 'Emergency Contact'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'supplier_contacts'
        verbose_name = 'Supplier Contact'
        verbose_name_plural = 'Supplier Contacts'
        unique_together = ['supplier', 'contact_type', 'email']

    def __str__(self):
        return f"{self.supplier.name} - {self.name} ({self.get_contact_type_display()})"


class SupplierDocument(TimestampedModel):
    """
    Document management for supplier onboarding and compliance.
    """
    DOCUMENT_TYPE_CHOICES = [
        ('business_license', 'Business License'),
        ('tax_certificate', 'Tax Certificate'),
        ('insurance_certificate', 'Insurance Certificate'),
        ('quality_certificate', 'Quality Certificate'),
        ('iso_certificate', 'ISO Certificate'),
        ('contract', 'Contract'),
        ('nda', 'Non-Disclosure Agreement'),
        ('w9_form', 'W-9 Form'),
        ('bank_details', 'Bank Details'),
        ('product_catalog', 'Product Catalog'),
        ('price_list', 'Price List'),
        ('capability_statement', 'Capability Statement'),
        ('reference_letter', 'Reference Letter'),
        ('audit_report', 'Audit Report'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('requires_update', 'Requires Update'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='supplier_documents/')
    file_size = models.IntegerField(null=True, blank=True)
    mime_type = models.CharField(max_length=100, blank=True)
    
    # Status and validation
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_required = models.BooleanField(default=False)
    is_confidential = models.BooleanField(default=False)
    
    # Dates
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    
    # Review information
    reviewed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    
    # Metadata
    uploaded_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='uploaded_supplier_docs')
    version = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'supplier_documents'
        verbose_name = 'Supplier Document'
        verbose_name_plural = 'Supplier Documents'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.supplier.name} - {self.title}"

    @property
    def is_expired(self):
        """Check if document has expired."""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False


class PurchaseOrder(TimestampedModel):
    """
    Purchase order management with approval workflows and tracking.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Supplier'),
        ('acknowledged', 'Acknowledged by Supplier'),
        ('in_progress', 'In Progress'),
        ('partially_received', 'Partially Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('disputed', 'Disputed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    # Order identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.PROTECT, related_name='purchase_orders')
    
    # Order details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    order_date = models.DateField(default=timezone.now)
    required_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    delivered_date = models.DateField(null=True, blank=True)
    
    # Financial information
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Delivery information
    delivery_address = models.JSONField(default=dict)
    shipping_method = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    
    # Terms and conditions
    payment_terms = models.CharField(max_length=100, default='Net 30')
    delivery_terms = models.CharField(max_length=100, blank=True)
    warranty_terms = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    
    # Approval workflow
    created_by = models.ForeignKey(AdminUser, on_delete=models.PROTECT, related_name='created_pos')
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Communication
    supplier_contact = models.ForeignKey(SupplierContact, on_delete=models.SET_NULL, null=True, blank=True)
    last_communication_date = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    attachments = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'purchase_orders'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['po_number']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['required_date']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(TimestampedModel):
    """
    Individual items within a purchase order.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    line_number = models.IntegerField()
    
    # Product information
    product_code = models.CharField(max_length=100)
    product_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    specifications = models.JSONField(default=dict, blank=True)
    
    # Quantity and pricing
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=3)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=3, default=Decimal('0.000'))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Delivery information
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    
    # Quality and inspection
    quality_approved = models.BooleanField(default=False)
    inspection_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'purchase_order_items'
        verbose_name = 'Purchase Order Item'
        verbose_name_plural = 'Purchase Order Items'
        unique_together = ['purchase_order', 'line_number']
        ordering = ['line_number']

    def __str__(self):
        return f"{self.purchase_order.po_number} - Line {self.line_number}: {self.product_name}"

    @property
    def quantity_pending(self):
        """Calculate quantity still pending delivery."""
        return self.quantity_ordered - self.quantity_received


class SupplierPerformanceMetric(TimestampedModel):
    """
    Track supplier performance metrics over time.
    """
    METRIC_TYPE_CHOICES = [
        ('delivery_time', 'Delivery Time'),
        ('quality_score', 'Quality Score'),
        ('service_rating', 'Service Rating'),
        ('cost_competitiveness', 'Cost Competitiveness'),
        ('communication', 'Communication'),
        ('flexibility', 'Flexibility'),
        ('innovation', 'Innovation'),
        ('sustainability', 'Sustainability'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='performance_metrics')
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPE_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    target_value = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    measurement_date = models.DateField(default=timezone.now)
    measurement_period = models.CharField(max_length=20, default='monthly')  # daily, weekly, monthly, quarterly
    
    # Context
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    measured_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'supplier_performance_metrics'
        verbose_name = 'Supplier Performance Metric'
        verbose_name_plural = 'Supplier Performance Metrics'
        ordering = ['-measurement_date']
        indexes = [
            models.Index(fields=['supplier', 'metric_type', 'measurement_date']),
            models.Index(fields=['measurement_date']),
        ]

    def __str__(self):
        return f"{self.supplier.name} - {self.get_metric_type_display()}: {self.value}"


class SupplierCommunication(TimestampedModel):
    """
    Track all communications with suppliers.
    """
    COMMUNICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('video_call', 'Video Call'),
        ('message', 'Instant Message'),
        ('letter', 'Letter'),
        ('fax', 'Fax'),
        ('portal', 'Supplier Portal'),
    ]
    
    DIRECTION_CHOICES = [
        ('inbound', 'Inbound'),
        ('outbound', 'Outbound'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    
    # Communication details
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Participants
    admin_user = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    supplier_contact = models.ForeignKey(SupplierContact, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Related objects
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Metadata
    attachments = models.JSONField(default=list, blank=True)
    is_important = models.BooleanField(default=False)
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'supplier_communications'
        verbose_name = 'Supplier Communication'
        verbose_name_plural = 'Supplier Communications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.supplier.name} - {self.subject}"


class SupplierContract(TimestampedModel):
    """
    Manage supplier contracts with terms, renewals, and compliance tracking.
    """
    CONTRACT_TYPE_CHOICES = [
        ('master_agreement', 'Master Service Agreement'),
        ('purchase_agreement', 'Purchase Agreement'),
        ('supply_agreement', 'Supply Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('quality_agreement', 'Quality Agreement'),
        ('service_agreement', 'Service Agreement'),
        ('consulting_agreement', 'Consulting Agreement'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPE_CHOICES)
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Contract terms
    start_date = models.DateField()
    end_date = models.DateField()
    auto_renewal = models.BooleanField(default=False)
    renewal_period_months = models.IntegerField(null=True, blank=True)
    notice_period_days = models.IntegerField(default=30)
    
    # Financial terms
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_terms = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status and compliance
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    compliance_status = models.CharField(max_length=20, default='compliant')
    last_review_date = models.DateField(null=True, blank=True)
    next_review_date = models.DateField(null=True, blank=True)
    
    # Document management
    contract_file = models.FileField(upload_to='supplier_contracts/', null=True, blank=True)
    signed_file = models.FileField(upload_to='supplier_contracts/signed/', null=True, blank=True)
    
    # Approval and management
    created_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='created_contracts')
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_contracts')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    terms_and_conditions = models.TextField(blank=True)
    special_clauses = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'supplier_contracts'
        verbose_name = 'Supplier Contract'
        verbose_name_plural = 'Supplier Contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract_number']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['end_date']),
            models.Index(fields=['next_review_date']),
        ]

    def __str__(self):
        return f"{self.contract_number} - {self.supplier.name}"

    @property
    def is_expiring_soon(self):
        """Check if contract is expiring within 30 days."""
        if self.end_date:
            days_until_expiry = (self.end_date - timezone.now().date()).days
            return days_until_expiry <= 30
        return False

    @property
    def days_until_expiry(self):
        """Calculate days until contract expiry."""
        if self.end_date:
            return (self.end_date - timezone.now().date()).days
        return None


class SupplierAudit(TimestampedModel):
    """
    Supplier audit tools with evaluation forms and corrective action tracking.
    """
    AUDIT_TYPE_CHOICES = [
        ('quality', 'Quality Audit'),
        ('compliance', 'Compliance Audit'),
        ('financial', 'Financial Audit'),
        ('security', 'Security Audit'),
        ('operational', 'Operational Audit'),
        ('sustainability', 'Sustainability Audit'),
        ('performance', 'Performance Review'),
    ]
    
    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('follow_up_required', 'Follow-up Required'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='audits')
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES)
    audit_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Scheduling
    planned_date = models.DateField()
    actual_date = models.DateField(null=True, blank=True)
    duration_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Status and results
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')
    overall_score = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    pass_fail_result = models.CharField(max_length=10, blank=True)  # Pass/Fail/Conditional
    
    # Team and participants
    lead_auditor = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='led_audits')
    audit_team = models.ManyToManyField(AdminUser, blank=True, related_name='participated_audits')
    supplier_participants = models.JSONField(default=list, blank=True)
    
    # Documentation
    audit_checklist = models.JSONField(default=dict, blank=True)
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    next_audit_date = models.DateField(null=True, blank=True)
    
    # Files and attachments
    audit_report = models.FileField(upload_to='supplier_audits/', null=True, blank=True)
    attachments = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'supplier_audits'
        verbose_name = 'Supplier Audit'
        verbose_name_plural = 'Supplier Audits'
        ordering = ['-planned_date']

    def __str__(self):
        return f"{self.audit_number} - {self.supplier.name} ({self.get_audit_type_display()})"


class SupplierRiskAssessment(TimestampedModel):
    """
    Supplier risk assessment with financial stability and compliance monitoring.
    """
    RISK_CATEGORY_CHOICES = [
        ('financial', 'Financial Risk'),
        ('operational', 'Operational Risk'),
        ('compliance', 'Compliance Risk'),
        ('quality', 'Quality Risk'),
        ('delivery', 'Delivery Risk'),
        ('security', 'Security Risk'),
        ('reputation', 'Reputation Risk'),
        ('geographic', 'Geographic Risk'),
        ('technology', 'Technology Risk'),
        ('environmental', 'Environmental Risk'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
        ('critical', 'Critical'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='risk_assessments')
    assessment_date = models.DateField(default=timezone.now)
    assessment_period = models.CharField(max_length=20, default='annual')
    
    # Overall risk
    overall_risk_level = models.CharField(max_length=15, choices=RISK_LEVEL_CHOICES)
    overall_risk_score = models.DecimalField(
        max_digits=5, decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Individual risk categories
    financial_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    operational_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    compliance_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    quality_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    delivery_risk_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    
    # Assessment details
    risk_factors = models.JSONField(default=list, blank=True)
    mitigation_strategies = models.TextField(blank=True)
    monitoring_requirements = models.TextField(blank=True)
    
    # Financial indicators
    credit_rating = models.CharField(max_length=10, blank=True)
    financial_stability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    debt_to_equity_ratio = models.DecimalField(max_digits=8, decimal_places=4, null=True, blank=True)
    
    # Compliance status
    regulatory_compliance_status = models.CharField(max_length=20, default='compliant')
    certification_status = models.CharField(max_length=20, default='current')
    
    # Assessment team
    assessed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True)
    reviewed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_risk_assessments')
    
    # Follow-up
    next_assessment_date = models.DateField(null=True, blank=True)
    action_items = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'supplier_risk_assessments'
        verbose_name = 'Supplier Risk Assessment'
        verbose_name_plural = 'Supplier Risk Assessments'
        ordering = ['-assessment_date']

    def __str__(self):
        return f"{self.supplier.name} - Risk Assessment ({self.assessment_date})"


class SupplierQualification(TimestampedModel):
    """
    Supplier qualification and certification management.
    """
    QUALIFICATION_TYPE_CHOICES = [
        ('initial', 'Initial Qualification'),
        ('requalification', 'Re-qualification'),
        ('certification', 'Certification'),
        ('pre_qualification', 'Pre-qualification'),
        ('vendor_assessment', 'Vendor Assessment'),
    ]
    
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('qualified', 'Qualified'),
        ('not_qualified', 'Not Qualified'),
        ('conditionally_qualified', 'Conditionally Qualified'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='qualifications')
    qualification_type = models.CharField(max_length=20, choices=QUALIFICATION_TYPE_CHOICES)
    qualification_number = models.CharField(max_length=50, unique=True)
    
    # Qualification details
    start_date = models.DateField(default=timezone.now)
    completion_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='in_progress')
    
    # Assessment criteria
    technical_capability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    quality_system_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    financial_stability_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    delivery_performance_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Requirements and documentation
    requirements_checklist = models.JSONField(default=dict, blank=True)
    required_documents = models.JSONField(default=list, blank=True)
    submitted_documents = models.JSONField(default=list, blank=True)
    
    # Assessment team
    assessor = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, related_name='assessed_qualifications')
    approver = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_qualifications')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Results and feedback
    assessment_notes = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    
    class Meta:
        db_table = 'supplier_qualifications'
        verbose_name = 'Supplier Qualification'
        verbose_name_plural = 'Supplier Qualifications'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.qualification_number} - {self.supplier.name}"

    @property
    def is_expired(self):
        """Check if qualification has expired."""
        if self.expiry_date:
            return timezone.now().date() > self.expiry_date
        return False


class SupplierPayment(TimestampedModel):
    """
    Supplier payment management with terms, invoicing, and payment tracking.
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('ach', 'ACH Transfer'),
        ('wire_transfer', 'Wire Transfer'),
        ('paypal', 'PayPal'),
        ('other', 'Other'),
    ]
    
    supplier = models.ForeignKey(SupplierProfile, on_delete=models.CASCADE, related_name='payments')
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment identification
    payment_number = models.CharField(max_length=50, unique=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    invoice_date = models.DateField(null=True, blank=True)
    
    # Payment amounts
    invoice_amount = models.DecimalField(max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Payment terms and dates
    payment_terms = models.CharField(max_length=100)
    due_date = models.DateField()
    payment_date = models.DateField(null=True, blank=True)
    
    # Payment details
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=15, choices=PAYMENT_STATUS_CHOICES, default='pending')
    
    # Approval workflow
    approved_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_payments')
    approved_at = models.DateTimeField(null=True, blank=True)
    processed_by = models.ForeignKey(AdminUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_payments')
    
    # Documentation
    invoice_file = models.FileField(upload_to='supplier_invoices/', null=True, blank=True)
    payment_receipt = models.FileField(upload_to='payment_receipts/', null=True, blank=True)
    
    # Metadata
    notes = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    class Meta:
        db_table = 'supplier_payments'
        verbose_name = 'Supplier Payment'
        verbose_name_plural = 'Supplier Payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment_number']),
            models.Index(fields=['supplier', 'status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.payment_number} - {self.supplier.name}"

    @property
    def is_overdue(self):
        """Check if payment is overdue."""
        if self.due_date and self.status not in ['paid', 'cancelled']:
            return timezone.now().date() > self.due_date
        return False

    @property
    def days_overdue(self):
        """Calculate days overdue."""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0

    @property
    def outstanding_amount(self):
        """Calculate outstanding amount."""
        return self.net_amount - self.paid_amount