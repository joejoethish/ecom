from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    FormTemplate, Form, FormField, FormSubmission, FormVersion,
    FormAnalytics, FormApprovalWorkflow, FormIntegration, FormABTest
)
from .serializers import (
    FormTemplateSerializer, FormSerializer, FormFieldSerializer,
    FormSubmissionSerializer, FormVersionSerializer, FormAnalyticsSerializer,
    FormApprovalWorkflowSerializer, FormIntegrationSerializer, FormABTestSerializer,
    FormBuilderSerializer, FormSubmissionCreateSerializer, FormAnalyticsReportSerializer
)
from .services import FormBuilderService, FormValidationService, FormAnalyticsService

class FormTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for form templates"""
    queryset = FormTemplate.objects.all()
    serializer_class = FormTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get templates by form type"""
        form_type = request.query_params.get('type')
        if form_type:
            templates = self.queryset.filter(form_type=form_type, is_active=True)
            serializer = self.get_serializer(templates, many=True)
            return Response(serializer.data)
        return Response({'error': 'Form type parameter required'}, status=400)

class FormViewSet(viewsets.ModelViewSet):
    """ViewSet for forms"""
    queryset = Form.objects.all()
    serializer_class = FormSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return FormBuilderSerializer
        return FormSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a form"""
        form = self.get_object()
        service = FormBuilderService()
        duplicated_form = service.duplicate_form(form, request.user)
        serializer = self.get_serializer(duplicated_form)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish a form"""
        form = self.get_object()
        form.status = 'active'
        form.published_at = timezone.now()
        form.save()
        return Response({'status': 'published'})
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish a form"""
        form = self.get_object()
        form.status = 'inactive'
        form.save()
        return Response({'status': 'unpublished'})
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        """Get form preview data"""
        form = self.get_object()
        service = FormBuilderService()
        preview_data = service.generate_preview(form)
        return Response(preview_data)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get form analytics"""
        form = self.get_object()
        service = FormAnalyticsService()
        analytics_data = service.get_form_analytics(form, request.query_params)
        return Response(analytics_data)
    
    @action(detail=True, methods=['post'])
    def create_version(self, request, pk=None):
        """Create a new version of the form"""
        form = self.get_object()
        service = FormBuilderService()
        version = service.create_version(form, request.user, request.data.get('changes', {}))
        serializer = FormVersionSerializer(version)
        return Response(serializer.data)

class FormFieldViewSet(viewsets.ModelViewSet):
    """ViewSet for form fields"""
    queryset = FormField.objects.all()
    serializer_class = FormFieldSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form_id = self.request.query_params.get('form_id')
        if form_id:
            queryset = queryset.filter(form_id=form_id)
        return queryset.order_by('order')
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder form fields"""
        field_orders = request.data.get('field_orders', [])
        for item in field_orders:
            try:
                field = FormField.objects.get(id=item['id'])
                field.order = item['order']
                field.save()
            except FormField.DoesNotExist:
                continue
        return Response({'status': 'reordered'})

class FormSubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for form submissions"""
    queryset = FormSubmission.objects.all()
    serializer_class = FormSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return FormSubmissionCreateSerializer
        return FormSubmissionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form_id = self.request.query_params.get('form_id')
        status_filter = self.request.query_params.get('status')
        
        if form_id:
            queryset = queryset.filter(form_id=form_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-submitted_at')
    
    def create(self, request, *args, **kwargs):
        """Create form submission with validation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate form data
        validation_service = FormValidationService()
        form_id = serializer.validated_data['form'].id
        form_data = serializer.validated_data['data']
        
        validation_result = validation_service.validate_submission(form_id, form_data)
        if not validation_result['is_valid']:
            return Response({
                'errors': validation_result['errors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for spam
        spam_score = validation_service.check_spam(request, form_data)
        
        submission = serializer.save(
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            spam_score=spam_score,
            is_spam=spam_score > 0.7
        )
        
        # Update analytics
        analytics_service = FormAnalyticsService()
        analytics_service.track_submission(submission)
        
        return Response(FormSubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a submission"""
        submission = self.get_object()
        submission.status = 'approved'
        submission.processed_at = timezone.now()
        submission.save()
        
        # Create approval record
        FormApprovalWorkflow.objects.create(
            submission=submission,
            approver=request.user,
            status='approved',
            comments=request.data.get('comments', '')
        )
        
        return Response({'status': 'approved'})
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a submission"""
        submission = self.get_object()
        submission.status = 'rejected'
        submission.processed_at = timezone.now()
        submission.save()
        
        # Create approval record
        FormApprovalWorkflow.objects.create(
            submission=submission,
            approver=request.user,
            status='rejected',
            comments=request.data.get('comments', '')
        )
        
        return Response({'status': 'rejected'})
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Export form submissions"""
        form_id = request.query_params.get('form_id')
        export_format = request.query_params.get('format', 'csv')
        
        if not form_id:
            return Response({'error': 'form_id required'}, status=400)
        
        submissions = self.get_queryset().filter(form_id=form_id)
        
        # Export logic would go here
        # For now, return basic data
        data = []
        for submission in submissions:
            data.append({
                'id': str(submission.id),
                'submitted_at': submission.submitted_at.isoformat(),
                'status': submission.status,
                'data': submission.data
            })
        
        return Response({
            'format': export_format,
            'count': len(data),
            'data': data
        })

class FormVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for form versions"""
    queryset = FormVersion.objects.all()
    serializer_class = FormVersionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        form_id = self.request.query_params.get('form_id')
        if form_id:
            queryset = queryset.filter(form_id=form_id)
        return queryset
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """Restore a form version"""
        version = self.get_object()
        service = FormBuilderService()
        restored_form = service.restore_version(version, request.user)
        return Response(FormSerializer(restored_form).data)

class FormAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for form analytics"""
    queryset = FormAnalytics.objects.all()
    serializer_class = FormAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def generate_report(self, request):
        """Generate analytics report"""
        serializer = FormAnalyticsReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        service = FormAnalyticsService()
        report = service.generate_report(serializer.validated_data)
        return Response(report)
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Get analytics dashboard data"""
        service = FormAnalyticsService()
        dashboard_data = service.get_dashboard_data(request.user)
        return Response(dashboard_data)

class FormIntegrationViewSet(viewsets.ModelViewSet):
    """ViewSet for form integrations"""
    queryset = FormIntegration.objects.all()
    serializer_class = FormIntegrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """Test integration"""
        integration = self.get_object()
        # Test integration logic would go here
        return Response({'status': 'test_completed', 'success': True})

class FormABTestViewSet(viewsets.ModelViewSet):
    """ViewSet for A/B tests"""
    queryset = FormABTest.objects.all()
    serializer_class = FormABTestSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start A/B test"""
        test = self.get_object()
        test.status = 'running'
        test.start_date = timezone.now()
        test.save()
        return Response({'status': 'started'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop A/B test"""
        test = self.get_object()
        test.status = 'completed'
        test.end_date = timezone.now()
        test.save()
        return Response({'status': 'stopped'})
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get A/B test results"""
        test = self.get_object()
        # Calculate results logic would go here
        return Response({
            'original_conversions': 0,
            'variant_conversions': 0,
            'confidence': 0,
            'winner': None
        })

# Public API for form rendering and submission
class PublicFormViewSet(viewsets.ReadOnlyModelViewSet):
    """Public API for form rendering"""
    queryset = Form.objects.filter(status='active')
    serializer_class = FormBuilderSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['post'])
    def submit(self, request, slug=None):
        """Public form submission endpoint"""
        form = self.get_object()
        
        # Create submission
        submission_data = {
            'form': form.id,
            'data': request.data.get('data', {}),
            'files': request.data.get('files', {}),
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'referrer': request.META.get('HTTP_REFERER', ''),
            'session_id': request.session.session_key or ''
        }
        
        serializer = FormSubmissionCreateSerializer(data=submission_data)
        serializer.is_valid(raise_exception=True)
        
        # Validate form data
        validation_service = FormValidationService()
        validation_result = validation_service.validate_submission(
            form.id, 
            serializer.validated_data['data']
        )
        
        if not validation_result['is_valid']:
            return Response({
                'success': False,
                'errors': validation_result['errors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check for spam
        spam_score = validation_service.check_spam(request, serializer.validated_data['data'])
        
        submission = serializer.save(
            spam_score=spam_score,
            is_spam=spam_score > 0.7
        )
        
        # Update analytics
        analytics_service = FormAnalyticsService()
        analytics_service.track_submission(submission)
        
        return Response({
            'success': True,
            'submission_id': str(submission.id),
            'message': 'Form submitted successfully'
        })
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip