"""
Services for Supplier and Vendor Management System
"""
import csv
import io
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg, F
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, List, Any, Optional

from .supplier_models import (
    SupplierProfile, SupplierContact, SupplierDocument, PurchaseOrder,
    SupplierPerformanceMetric, SupplierCommunication, SupplierContract,
    SupplierAudit, SupplierRiskAssessment, SupplierQualification,
    SupplierPayment
)


class SupplierOnboardingService:
    """Service for managing supplier onboarding workflow."""
    
    @staticmethod
    def initiate_onboarding(supplier_data: Dict[str, Any], user) -> SupplierProfile:
        """Initiate supplier onboarding process."""
        with transaction.atomic():
            # Create supplier with pending status
            supplier = SupplierProfile.objects.create(
                **supplier_data,
                status='pending',
                created_by=user
            )
            
            # Create initial communication record
            SupplierCommunication.objects.create(
                supplier=supplier,
                communication_type='email',
                direction='outbound',
                subject='Welcome to Our Supplier Network',
                content='Thank you for your interest in becoming our supplier. We will review your application and get back to you soon.',
                admin_user=user
            )
            
            # Create initial risk assessment
            SupplierRiskAssessment.objects.create(
                supplier=supplier,
                overall_risk_level='medium',
                overall_risk_score=Decimal('50.00'),
                assessed_by=user
            )
            
            return supplier
    
    @staticmethod
    def get_required_documents(supplier_type: str) -> List[str]:
        """Get required documents based on supplier type."""
        base_documents = [
            'business_license',
            'tax_certificate',
            'insurance_certificate',
            'w9_form'
        ]
        
        type_specific = {
            'manufacturer': ['quality_certificate', 'iso_certificate'],
            'distributor': ['distribution_agreement'],
            'service_provider': ['capability_statement'],
            'consultant': ['professional_certifications']
        }
        
        return base_documents + type_specific.get(supplier_type, [])
    
    @staticmethod
    def check_onboarding_completion(supplier: SupplierProfile) -> Dict[str, Any]:
        """Check if supplier onboarding is complete."""
        required_docs = SupplierOnboardingService.get_required_documents(supplier.supplier_type)
        submitted_docs = supplier.documents.filter(
            document_type__in=required_docs,
            status='approved'
        ).values_list('document_type', flat=True)
        
        missing_docs = set(required_docs) - set(submitted_docs)
        
        # Check if all contacts are provided
        has_primary_contact = supplier.contacts.filter(contact_type='primary').exists()
        has_billing_contact = supplier.contacts.filter(contact_type='billing').exists()
        
        completion_status = {
            'is_complete': len(missing_docs) == 0 and has_primary_contact and has_billing_contact,
            'missing_documents': list(missing_docs),
            'has_primary_contact': has_primary_contact,
            'has_billing_contact': has_billing_contact,
            'completion_percentage': max(0, 100 - (len(missing_docs) * 20))
        }
        
        return completion_status
    
    @staticmethod
    def approve_supplier(supplier: SupplierProfile, user) -> bool:
        """Approve supplier after successful onboarding."""
        completion_status = SupplierOnboardingService.check_onboarding_completion(supplier)
        
        if not completion_status['is_complete']:
            return False
        
        with transaction.atomic():
            supplier.status = 'active'
            supplier.last_modified_by = user
            supplier.save()
            
            # Create approval communication
            SupplierCommunication.objects.create(
                supplier=supplier,
                communication_type='email',
                direction='outbound',
                subject='Supplier Application Approved',
                content='Congratulations! Your supplier application has been approved. You can now start receiving purchase orders.',
                admin_user=user
            )
            
            # Create initial qualification record
            SupplierQualification.objects.create(
                supplier=supplier,
                qualification_type='initial',
                status='qualified',
                assessor=user,
                approver=user,
                approved_at=timezone.now(),
                completion_date=timezone.now().date()
            )
        
        return True


class SupplierPerformanceService:
    """Service for tracking and analyzing supplier performance."""
    
    @staticmethod
    def calculate_delivery_performance(supplier: SupplierProfile, period_days: int = 90) -> Dict[str, Any]:
        """Calculate delivery performance metrics."""
        cutoff_date = timezone.now().date() - timedelta(days=period_days)
        
        completed_orders = supplier.purchase_orders.filter(
            status='completed',
            delivered_date__gte=cutoff_date,
            delivered_date__isnull=False
        )
        
        if not completed_orders.exists():
            return {
                'total_orders': 0,
                'on_time_deliveries': 0,
                'on_time_percentage': 0,
                'average_delay_days': 0,
                'early_deliveries': 0
            }
        
        on_time_count = 0
        early_count = 0
        total_delay_days = 0
        
        for order in completed_orders:
            if order.delivered_date <= order.required_date:
                if order.delivered_date < order.required_date:
                    early_count += 1
                on_time_count += 1
            else:
                delay_days = (order.delivered_date - order.required_date).days
                total_delay_days += delay_days
        
        total_orders = completed_orders.count()
        
        return {
            'total_orders': total_orders,
            'on_time_deliveries': on_time_count,
            'on_time_percentage': (on_time_count / total_orders) * 100 if total_orders > 0 else 0,
            'average_delay_days': total_delay_days / (total_orders - on_time_count) if total_orders > on_time_count else 0,
            'early_deliveries': early_count
        }
    
    @staticmethod
    def calculate_quality_performance(supplier: SupplierProfile, period_days: int = 90) -> Dict[str, Any]:
        """Calculate quality performance metrics."""
        cutoff_date = timezone.now().date() - timedelta(days=period_days)
        
        received_items = supplier.purchase_orders.filter(
            created_at__gte=cutoff_date
        ).values_list('items__quality_approved', flat=True)
        
        total_items = len(received_items)
        approved_items = sum(1 for approved in received_items if approved)
        
        return {
            'total_items_received': total_items,
            'quality_approved_items': approved_items,
            'quality_approval_rate': (approved_items / total_items) * 100 if total_items > 0 else 0,
            'defect_rate': ((total_items - approved_items) / total_items) * 100 if total_items > 0 else 0
        }
    
    @staticmethod
    def update_performance_ratings(supplier: SupplierProfile) -> None:
        """Update supplier performance ratings based on recent performance."""
        delivery_perf = SupplierPerformanceService.calculate_delivery_performance(supplier)
        quality_perf = SupplierPerformanceService.calculate_quality_performance(supplier)
        
        # Calculate delivery rating (0-5 scale)
        on_time_percentage = delivery_perf['on_time_percentage']
        if on_time_percentage >= 95:
            delivery_rating = Decimal('5.0')
        elif on_time_percentage >= 90:
            delivery_rating = Decimal('4.5')
        elif on_time_percentage >= 85:
            delivery_rating = Decimal('4.0')
        elif on_time_percentage >= 80:
            delivery_rating = Decimal('3.5')
        elif on_time_percentage >= 75:
            delivery_rating = Decimal('3.0')
        else:
            delivery_rating = Decimal('2.0')
        
        # Calculate quality rating (0-5 scale)
        quality_rate = quality_perf['quality_approval_rate']
        if quality_rate >= 98:
            quality_rating = Decimal('5.0')
        elif quality_rate >= 95:
            quality_rating = Decimal('4.5')
        elif quality_rate >= 90:
            quality_rating = Decimal('4.0')
        elif quality_rate >= 85:
            quality_rating = Decimal('3.5')
        elif quality_rate >= 80:
            quality_rating = Decimal('3.0')
        else:
            quality_rating = Decimal('2.0')
        
        # Update supplier ratings
        supplier.delivery_rating = delivery_rating
        supplier.quality_rating = quality_rating
        supplier.overall_rating = (delivery_rating + quality_rating) / 2
        supplier.save(update_fields=['delivery_rating', 'quality_rating', 'overall_rating'])
        
        # Create performance metric records
        SupplierPerformanceMetric.objects.create(
            supplier=supplier,
            metric_type='delivery_time',
            value=Decimal(str(delivery_perf['on_time_percentage'])),
            target_value=Decimal('95.0')
        )
        
        SupplierPerformanceMetric.objects.create(
            supplier=supplier,
            metric_type='quality_score',
            value=Decimal(str(quality_perf['quality_approval_rate'])),
            target_value=Decimal('98.0')
        )
    
    @staticmethod
    def generate_performance_report(supplier: SupplierProfile, period_days: int = 90) -> Dict[str, Any]:
        """Generate comprehensive performance report for supplier."""
        delivery_perf = SupplierPerformanceService.calculate_delivery_performance(supplier, period_days)
        quality_perf = SupplierPerformanceService.calculate_quality_performance(supplier, period_days)
        
        # Financial performance
        cutoff_date = timezone.now().date() - timedelta(days=period_days)
        total_spent = supplier.purchase_orders.filter(
            created_at__gte=cutoff_date,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        # Communication metrics
        communications = supplier.communications.filter(
            created_at__gte=timezone.now() - timedelta(days=period_days)
        )
        
        return {
            'period_days': period_days,
            'delivery_performance': delivery_perf,
            'quality_performance': quality_perf,
            'financial_performance': {
                'total_spent': float(total_spent),
                'average_order_value': float(total_spent / delivery_perf['total_orders']) if delivery_perf['total_orders'] > 0 else 0
            },
            'communication_metrics': {
                'total_communications': communications.count(),
                'response_rate': 95.0,  # This would be calculated from actual response data
                'average_response_time_hours': 4.5  # This would be calculated from actual response times
            },
            'overall_score': float(supplier.overall_rating),
            'recommendations': SupplierPerformanceService._generate_recommendations(supplier, delivery_perf, quality_perf)
        }
    
    @staticmethod
    def _generate_recommendations(supplier: SupplierProfile, delivery_perf: Dict, quality_perf: Dict) -> List[str]:
        """Generate performance improvement recommendations."""
        recommendations = []
        
        if delivery_perf['on_time_percentage'] < 90:
            recommendations.append("Improve delivery time performance - consider discussing lead time adjustments")
        
        if quality_perf['quality_approval_rate'] < 95:
            recommendations.append("Address quality issues - schedule quality review meeting")
        
        if supplier.overall_rating < 3.5:
            recommendations.append("Consider supplier development program or alternative sourcing")
        
        if delivery_perf['total_orders'] > 0 and delivery_perf['average_delay_days'] > 5:
            recommendations.append("Significant delivery delays detected - review supplier capacity")
        
        return recommendations


class SupplierRiskService:
    """Service for managing supplier risk assessment and monitoring."""
    
    @staticmethod
    def calculate_risk_score(supplier: SupplierProfile) -> Dict[str, Any]:
        """Calculate comprehensive risk score for supplier."""
        risk_factors = {
            'financial_risk': SupplierRiskService._assess_financial_risk(supplier),
            'operational_risk': SupplierRiskService._assess_operational_risk(supplier),
            'compliance_risk': SupplierRiskService._assess_compliance_risk(supplier),
            'quality_risk': SupplierRiskService._assess_quality_risk(supplier),
            'delivery_risk': SupplierRiskService._assess_delivery_risk(supplier)
        }
        
        # Calculate weighted overall risk score
        weights = {
            'financial_risk': 0.25,
            'operational_risk': 0.20,
            'compliance_risk': 0.20,
            'quality_risk': 0.20,
            'delivery_risk': 0.15
        }
        
        overall_score = sum(
            risk_factors[factor] * weights[factor]
            for factor in risk_factors
        )
        
        # Determine risk level
        if overall_score <= 20:
            risk_level = 'low'
        elif overall_score <= 40:
            risk_level = 'medium'
        elif overall_score <= 70:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        return {
            'overall_score': overall_score,
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'mitigation_strategies': SupplierRiskService._generate_mitigation_strategies(risk_factors)
        }
    
    @staticmethod
    def _assess_financial_risk(supplier: SupplierProfile) -> float:
        """Assess financial risk factors."""
        risk_score = 0
        
        # Credit limit utilization
        if supplier.credit_limit > 0:
            utilization = (supplier.current_balance / supplier.credit_limit) * 100
            if utilization > 90:
                risk_score += 30
            elif utilization > 75:
                risk_score += 20
            elif utilization > 50:
                risk_score += 10
        
        # Payment history
        overdue_payments = supplier.payments.filter(
            status__in=['pending', 'approved'],
            due_date__lt=timezone.now().date()
        ).count()
        
        if overdue_payments > 5:
            risk_score += 25
        elif overdue_payments > 2:
            risk_score += 15
        elif overdue_payments > 0:
            risk_score += 5
        
        # Company size and stability
        if supplier.annual_revenue and supplier.annual_revenue < 1000000:
            risk_score += 15
        
        if supplier.employee_count and supplier.employee_count < 10:
            risk_score += 10
        
        return min(risk_score, 100)
    
    @staticmethod
    def _assess_operational_risk(supplier: SupplierProfile) -> float:
        """Assess operational risk factors."""
        risk_score = 0
        
        # Capacity utilization
        if supplier.capacity_rating < 50:
            risk_score += 20
        elif supplier.capacity_rating < 75:
            risk_score += 10
        
        # Geographic risk
        high_risk_countries = ['Country1', 'Country2']  # This would be configurable
        if supplier.country in high_risk_countries:
            risk_score += 25
        
        # Single source dependency
        total_suppliers_in_category = SupplierProfile.objects.filter(
            category=supplier.category,
            status='active'
        ).count()
        
        if total_suppliers_in_category < 3:
            risk_score += 20
        
        return min(risk_score, 100)
    
    @staticmethod
    def _assess_compliance_risk(supplier: SupplierProfile) -> float:
        """Assess compliance risk factors."""
        risk_score = 0
        
        # Certification status
        if not supplier.is_certified:
            risk_score += 20
        
        if not supplier.iso_certified:
            risk_score += 15
        
        # Audit history
        if supplier.last_audit_date:
            days_since_audit = (timezone.now().date() - supplier.last_audit_date).days
            if days_since_audit > 730:  # 2 years
                risk_score += 25
            elif days_since_audit > 365:  # 1 year
                risk_score += 15
        else:
            risk_score += 30
        
        # Document compliance
        expired_docs = supplier.documents.filter(
            expiry_date__lt=timezone.now().date(),
            is_required=True
        ).count()
        
        risk_score += expired_docs * 10
        
        return min(risk_score, 100)
    
    @staticmethod
    def _assess_quality_risk(supplier: SupplierProfile) -> float:
        """Assess quality risk factors."""
        risk_score = 0
        
        # Quality rating
        if supplier.quality_rating < 2.0:
            risk_score += 40
        elif supplier.quality_rating < 3.0:
            risk_score += 25
        elif supplier.quality_rating < 4.0:
            risk_score += 10
        
        # Recent quality issues
        recent_quality_issues = supplier.purchase_orders.filter(
            created_at__gte=timezone.now() - timedelta(days=90),
            items__quality_approved=False
        ).count()
        
        risk_score += min(recent_quality_issues * 5, 30)
        
        return min(risk_score, 100)
    
    @staticmethod
    def _assess_delivery_risk(supplier: SupplierProfile) -> float:
        """Assess delivery risk factors."""
        risk_score = 0
        
        # Delivery rating
        if supplier.delivery_rating < 2.0:
            risk_score += 40
        elif supplier.delivery_rating < 3.0:
            risk_score += 25
        elif supplier.delivery_rating < 4.0:
            risk_score += 10
        
        # Lead time reliability
        if supplier.lead_time_days > 30:
            risk_score += 15
        elif supplier.lead_time_days > 14:
            risk_score += 10
        
        return min(risk_score, 100)
    
    @staticmethod
    def _generate_mitigation_strategies(risk_factors: Dict[str, float]) -> List[str]:
        """Generate risk mitigation strategies."""
        strategies = []
        
        if risk_factors['financial_risk'] > 50:
            strategies.append("Implement credit monitoring and payment terms review")
            strategies.append("Consider requiring payment guarantees or insurance")
        
        if risk_factors['operational_risk'] > 50:
            strategies.append("Develop alternative supplier sources")
            strategies.append("Implement supplier capacity monitoring")
        
        if risk_factors['compliance_risk'] > 50:
            strategies.append("Schedule immediate compliance audit")
            strategies.append("Require updated certifications and documentation")
        
        if risk_factors['quality_risk'] > 50:
            strategies.append("Implement enhanced quality control measures")
            strategies.append("Schedule quality improvement meetings")
        
        if risk_factors['delivery_risk'] > 50:
            strategies.append("Review and adjust lead times")
            strategies.append("Implement delivery performance monitoring")
        
        return strategies


class SupplierAnalyticsService:
    """Service for supplier analytics and reporting."""
    
    @staticmethod
    def generate_supplier_dashboard_data() -> Dict[str, Any]:
        """Generate data for supplier management dashboard."""
        # Key metrics
        total_suppliers = SupplierProfile.objects.count()
        active_suppliers = SupplierProfile.objects.filter(status='active').count()
        preferred_suppliers = SupplierProfile.objects.filter(is_preferred=True).count()
        
        # Risk distribution
        risk_distribution = dict(
            SupplierProfile.objects.values('risk_level').annotate(
                count=Count('id')
            ).values_list('risk_level', 'count')
        )
        
        # Performance metrics
        avg_rating = SupplierProfile.objects.aggregate(
            avg=Avg('overall_rating')
        )['avg'] or 0
        
        # Recent activities
        recent_orders = PurchaseOrder.objects.select_related('supplier').order_by('-created_at')[:10]
        recent_communications = SupplierCommunication.objects.select_related('supplier').order_by('-created_at')[:10]
        
        # Alerts
        alerts = []
        
        # High risk suppliers
        high_risk_count = SupplierProfile.objects.filter(risk_level__in=['high', 'critical']).count()
        if high_risk_count > 0:
            alerts.append({
                'type': 'warning',
                'message': f'{high_risk_count} suppliers are high/critical risk',
                'count': high_risk_count
            })
        
        # Expiring contracts
        expiring_contracts = SupplierContract.objects.filter(
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=30)
        ).count()
        
        if expiring_contracts > 0:
            alerts.append({
                'type': 'info',
                'message': f'{expiring_contracts} contracts expiring within 30 days',
                'count': expiring_contracts
            })
        
        # Overdue payments
        overdue_payments = SupplierPayment.objects.filter(
            status__in=['pending', 'approved'],
            due_date__lt=timezone.now().date()
        ).count()
        
        if overdue_payments > 0:
            alerts.append({
                'type': 'error',
                'message': f'{overdue_payments} payments are overdue',
                'count': overdue_payments
            })
        
        return {
            'key_metrics': {
                'total_suppliers': total_suppliers,
                'active_suppliers': active_suppliers,
                'preferred_suppliers': preferred_suppliers,
                'average_rating': float(avg_rating)
            },
            'risk_distribution': risk_distribution,
            'recent_activities': {
                'orders': [
                    {
                        'id': order.id,
                        'po_number': order.po_number,
                        'supplier_name': order.supplier.name,
                        'total_amount': float(order.total_amount),
                        'status': order.status,
                        'created_at': order.created_at
                    }
                    for order in recent_orders
                ],
                'communications': [
                    {
                        'id': comm.id,
                        'supplier_name': comm.supplier.name,
                        'subject': comm.subject,
                        'type': comm.communication_type,
                        'created_at': comm.created_at
                    }
                    for comm in recent_communications
                ]
            },
            'alerts': alerts
        }
    
    @staticmethod
    def generate_performance_trends(period_months: int = 12) -> Dict[str, Any]:
        """Generate supplier performance trends over time."""
        cutoff_date = timezone.now().date() - timedelta(days=period_months * 30)
        
        # Monthly performance data
        monthly_data = []
        for i in range(period_months):
            month_start = timezone.now().date() - timedelta(days=(i + 1) * 30)
            month_end = timezone.now().date() - timedelta(days=i * 30)
            
            month_metrics = SupplierPerformanceMetric.objects.filter(
                measurement_date__gte=month_start,
                measurement_date__lt=month_end
            ).aggregate(
                avg_delivery=Avg('value', filter=Q(metric_type='delivery_time')),
                avg_quality=Avg('value', filter=Q(metric_type='quality_score'))
            )
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'delivery_performance': float(month_metrics['avg_delivery'] or 0),
                'quality_performance': float(month_metrics['avg_quality'] or 0)
            })
        
        return {
            'monthly_trends': list(reversed(monthly_data)),
            'period_months': period_months
        }
    
    @staticmethod
    def export_supplier_data(supplier_ids: List[int] = None, format: str = 'csv') -> str:
        """Export supplier data in specified format."""
        queryset = SupplierProfile.objects.all()
        if supplier_ids:
            queryset = queryset.filter(id__in=supplier_ids)
        
        if format == 'csv':
            return SupplierAnalyticsService._export_csv(queryset)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    @staticmethod
    def _export_csv(queryset) -> str:
        """Export suppliers to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Supplier Code', 'Name', 'Type', 'Status', 'Contact Email',
            'Phone', 'City', 'Country', 'Overall Rating', 'Risk Level',
            'Is Preferred', 'Total Orders', 'Total Spent', 'Created Date'
        ])
        
        # Write data
        for supplier in queryset:
            writer.writerow([
                supplier.supplier_code,
                supplier.name,
                supplier.get_supplier_type_display(),
                supplier.get_status_display(),
                supplier.primary_contact_email,
                supplier.primary_contact_phone,
                supplier.city,
                supplier.country,
                float(supplier.overall_rating),
                supplier.get_risk_level_display(),
                supplier.is_preferred,
                supplier.total_orders,
                float(supplier.total_spent),
                supplier.created_at.strftime('%Y-%m-%d')
            ])
        
        return output.getvalue()


class SupplierNotificationService:
    """Service for managing supplier notifications and communications."""
    
    @staticmethod
    def send_contract_expiry_notifications():
        """Send notifications for contracts expiring soon."""
        expiring_contracts = SupplierContract.objects.filter(
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=30),
            end_date__gt=timezone.now().date()
        )
        
        for contract in expiring_contracts:
            days_until_expiry = (contract.end_date - timezone.now().date()).days
            
            # Send email notification
            subject = f"Contract Expiring Soon: {contract.contract_number}"
            message = f"""
            Dear Team,
            
            The contract {contract.contract_number} with {contract.supplier.name} 
            is expiring in {days_until_expiry} days on {contract.end_date}.
            
            Please review and take necessary action for renewal or replacement.
            
            Contract Details:
            - Supplier: {contract.supplier.name}
            - Contract Type: {contract.get_contract_type_display()}
            - Value: {contract.contract_value}
            - End Date: {contract.end_date}
            
            Best regards,
            Supplier Management System
            """
            
            # This would send to relevant stakeholders
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, ['procurement@company.com'])
            
            # Create communication record
            SupplierCommunication.objects.create(
                supplier=contract.supplier,
                communication_type='email',
                direction='outbound',
                subject=subject,
                content=message
            )
    
    @staticmethod
    def send_payment_reminders():
        """Send payment reminders for overdue invoices."""
        overdue_payments = SupplierPayment.objects.filter(
            status__in=['pending', 'approved'],
            due_date__lt=timezone.now().date()
        )
        
        for payment in overdue_payments:
            days_overdue = (timezone.now().date() - payment.due_date).days
            
            subject = f"Payment Overdue: {payment.payment_number}"
            message = f"""
            Dear Finance Team,
            
            Payment {payment.payment_number} to {payment.supplier.name} 
            is overdue by {days_overdue} days.
            
            Payment Details:
            - Invoice Number: {payment.invoice_number}
            - Amount: {payment.net_amount}
            - Due Date: {payment.due_date}
            - Supplier: {payment.supplier.name}
            
            Please process this payment immediately.
            
            Best regards,
            Supplier Management System
            """
            
            # This would send to finance team
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, ['finance@company.com'])
    
    @staticmethod
    def send_performance_alerts():
        """Send alerts for poor supplier performance."""
        poor_performers = SupplierProfile.objects.filter(
            status='active',
            overall_rating__lt=3.0
        )
        
        for supplier in poor_performers:
            subject = f"Supplier Performance Alert: {supplier.name}"
            message = f"""
            Dear Procurement Team,
            
            Supplier {supplier.name} ({supplier.supplier_code}) has a low performance rating 
            of {supplier.overall_rating}/5.0.
            
            Performance Breakdown:
            - Overall Rating: {supplier.overall_rating}/5.0
            - Quality Rating: {supplier.quality_rating}/5.0
            - Delivery Rating: {supplier.delivery_rating}/5.0
            - Service Rating: {supplier.service_rating}/5.0
            
            Please review and consider corrective actions.
            
            Best regards,
            Supplier Management System
            """
            
            # This would send to procurement team
            # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, ['procurement@company.com'])
            
            # Create communication record
            SupplierCommunication.objects.create(
                supplier=supplier,
                communication_type='email',
                direction='outbound',
                subject=subject,
                content=message
            )