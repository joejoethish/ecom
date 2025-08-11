from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid


class SupplierCategory(models.Model):
    """Categories for organizing suppliers"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Supplier Categories"
    
    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Comprehensive supplier profile model"""
    SUPPLIER_STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending Approval'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    SUPPLIER_TYPE_CHOICES = [
        ('manufacturer', 'Manufacturer'),
        ('distributor', 'Distributor'),
        ('wholesaler', 'Wholesaler'),
        ('service_provider', 'Service Provider'),
        ('dropshipper', 'Dropshipper'),
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
    company_name = models.CharField(max_length=200)
    legal_name = models.CharField(max_length=200, blank=True)
    supplier_type = models.CharField(max_length=20, choices=SUPPLIER_TYPE_CHOICES)
    category = models.ForeignKey(SupplierCategory, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=SUPPLIER_STATUS_CHOICES, default='pending')
    
    # Contact Information
    primary_contact_name = models.CharField(max_length=100)
    primary_contact_email = models.EmailField()
    primary_contact_phone = models.CharField(max_length=20)
    secondary_contact_name = models.CharField(max_length=100, blank=True)
    secondary_contact_email = models.EmailField(blank=True)
    secondary_contact_phone = models.CharField(max_length=20, blank=True)
    
    # Address Information
    address_line1 = models.CharField(max_length=200)
    address_line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    
    # Business Information
    tax_id = models.CharField(max_length=50, blank=True)
    business_license = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    employee_count = models.IntegerField(null=True, blank=True)
    annual_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Performance Metrics
    performance_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0), MaxValueValidator(5)])
    quality_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                      validators=[MinValueValidator(0), MaxValueValidator(5)])
    delivery_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                       validators=[MinValueValidator(0), MaxValueValidator(5)])
    reliability_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                          validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Risk Assessment
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium')
    financial_stability_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                                   validators=[MinValueValidator(0), MaxValueValidator(5)])
    compliance_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                         validators=[MinValueValidator(0), MaxValueValidator(5)])
    
    # Payment Terms
    payment_terms_days = models.IntegerField(default=30)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, default='USD')
    
    # Diversity Information
    is_minority_owned = models.BooleanField(default=False)
    is_women_owned = models.BooleanField(default=False)
    is_veteran_owned = models.BooleanField(default=False)
    is_small_business = models.BooleanField(default=False)
    
    # Sustainability
    sustainability_score = models.DecimalField(max_digits=3, decimal_places=2, default=0.00,
                                             validators=[MinValueValidator(0), MaxValueValidator(5)])
    esg_compliance = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_audit_date = models.DateTimeField(null=True, blank=True)
    next_audit_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['company_name']
    
    def __str__(self):
        return f"{self.supplier_code} - {self.company_name}"


class SupplierDocument(models.Model):
    """Documents associated with suppliers"""
    DOCUMENT_TYPE_CHOICES = [
        ('business_license', 'Business License'),
        ('tax_certificate', 'Tax Certificate'),
        ('insurance', 'Insurance Certificate'),
        ('quality_certificate', 'Quality Certificate'),
        ('contract', 'Contract'),
        ('audit_report', 'Audit Report'),
        ('financial_statement', 'Financial Statement'),
        ('compliance_certificate', 'Compliance Certificate'),
        ('other', 'Other'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='supplier_documents/')
    description = models.TextField(blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.supplier.company_name} - {self.title}"


class SupplierContact(models.Model):
    """Additional contacts for suppliers"""
    CONTACT_TYPE_CHOICES = [
        ('sales', 'Sales'),
        ('technical', 'Technical'),
        ('finance', 'Finance'),
        ('quality', 'Quality'),
        ('logistics', 'Logistics'),
        ('management', 'Management'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(max_length=20, choices=CONTACT_TYPE_CHOICES)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.supplier.company_name} - {self.name}"


class SupplierPerformanceMetric(models.Model):
    """Historical performance tracking"""
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='performance_history')
    metric_date = models.DateField()
    
    # Delivery Metrics
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    average_delivery_days = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Quality Metrics
    defect_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    return_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    # Financial Metrics
    total_orders = models.IntegerField(default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Service Metrics
    response_time_hours = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    issue_resolution_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['supplier', 'metric_date']
        ordering = ['-metric_date']


class PurchaseOrder(models.Model):
    """Purchase orders to suppliers"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('sent', 'Sent to Supplier'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('partially_received', 'Partially Received'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po_number = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='purchase_orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Dates
    order_date = models.DateTimeField(auto_now_add=True)
    required_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    
    # Financial
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    # Additional Information
    notes = models.TextField(blank=True)
    terms_and_conditions = models.TextField(blank=True)
    
    # Approval Workflow
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_pos')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_pos')
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"PO-{self.po_number} - {self.supplier.company_name}"


class PurchaseOrderItem(models.Model):
    """Items in purchase orders"""
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_sku = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    quantity_ordered = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_received = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Delivery tracking
    expected_delivery_date = models.DateField(null=True, blank=True)
    actual_delivery_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        self.total_price = self.quantity_ordered * self.unit_price
        super().save(*args, **kwargs)


class SupplierAudit(models.Model):
    """Supplier audit records"""
    AUDIT_TYPE_CHOICES = [
        ('quality', 'Quality Audit'),
        ('financial', 'Financial Audit'),
        ('compliance', 'Compliance Audit'),
        ('performance', 'Performance Review'),
        ('sustainability', 'Sustainability Audit'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='audits')
    audit_type = models.CharField(max_length=20, choices=AUDIT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Dates
    scheduled_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    
    # Results
    overall_score = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(5)])
    findings = models.TextField(blank=True)
    recommendations = models.TextField(blank=True)
    corrective_actions = models.TextField(blank=True)
    
    # Personnel
    auditor = models.ForeignKey(User, on_delete=models.CASCADE)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.supplier.company_name} - {self.audit_type} - {self.scheduled_date}"


class SupplierCommunication(models.Model):
    """Communication history with suppliers"""
    COMMUNICATION_TYPE_CHOICES = [
        ('email', 'Email'),
        ('phone', 'Phone Call'),
        ('meeting', 'Meeting'),
        ('video_call', 'Video Call'),
        ('message', 'Internal Message'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='communications')
    communication_type = models.CharField(max_length=20, choices=COMMUNICATION_TYPE_CHOICES)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    # Participants
    internal_contact = models.ForeignKey(User, on_delete=models.CASCADE)
    supplier_contact = models.ForeignKey(SupplierContact, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Follow-up
    requires_follow_up = models.BooleanField(default=False)
    follow_up_date = models.DateField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.supplier.company_name} - {self.subject}"


class SupplierContract(models.Model):
    """Supplier contracts management"""
    CONTRACT_TYPE_CHOICES = [
        ('supply_agreement', 'Supply Agreement'),
        ('service_agreement', 'Service Agreement'),
        ('nda', 'Non-Disclosure Agreement'),
        ('master_agreement', 'Master Service Agreement'),
        ('purchase_agreement', 'Purchase Agreement'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    ]
    
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='contracts')
    contract_type = models.CharField(max_length=30, choices=CONTRACT_TYPE_CHOICES)
    contract_number = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Dates
    start_date = models.DateField()
    end_date = models.DateField()
    renewal_date = models.DateField(null=True, blank=True)
    
    # Financial Terms
    contract_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    payment_terms = models.CharField(max_length=100, blank=True)
    
    # Documents
    contract_file = models.FileField(upload_to='supplier_contracts/', blank=True)
    
    # Terms
    terms_and_conditions = models.TextField(blank=True)
    special_terms = models.TextField(blank=True)
    
    # Auto-renewal
    auto_renewal = models.BooleanField(default=False)
    renewal_notice_days = models.IntegerField(default=30)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.supplier.company_name} - {self.title}"