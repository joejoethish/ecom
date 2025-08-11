from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, datetime
import json
import re
from typing import Dict, List, Any
import hashlib

from .models import (
    Form, FormField, FormSubmission, FormVersion, FormAnalytics,
    FormTemplate, FormABTest
)

class FormBuilderService:
    """Service for form building operations"""
    
    def duplicate_form(self, form: Form, user) -> Form:
        """Duplicate a form with all its fields"""
        # Create new form
        new_form = Form.objects.create(
            name=f"{form.name} (Copy)",
            slug=f"{form.slug}-copy",
            description=form.description,
            template=form.template,
            schema=form.schema,
            validation_rules=form.validation_rules,
            conditional_logic=form.conditional_logic,
            settings=form.settings,
            status='draft',
            is_multi_step=form.is_multi_step,
            steps_config=form.steps_config,
            auto_save_enabled=form.auto_save_enabled,
            requires_approval=form.requires_approval,
            approval_workflow=form.approval_workflow,
            encryption_enabled=form.encryption_enabled,
            spam_protection_enabled=form.spam_protection_enabled,
            analytics_enabled=form.analytics_enabled,
            created_by=user
        )
        
        # Duplicate fields
        for field in form.fields.all():
            FormField.objects.create(
                form=new_form,
                name=field.name,
                label=field.label,
                field_type=field.field_type,
                placeholder=field.placeholder,
                help_text=field.help_text,
                default_value=field.default_value,
                options=field.options,
                validation_rules=field.validation_rules,
                conditional_logic=field.conditional_logic,
                is_required=field.is_required,
                is_readonly=field.is_readonly,
                is_hidden=field.is_hidden,
                order=field.order,
                step=field.step,
                css_classes=field.css_classes,
                attributes=field.attributes
            )
        
        return new_form
    
    def create_version(self, form: Form, user, changes: Dict) -> FormVersion:
        """Create a new version of the form"""
        # Get current version number
        latest_version = form.versions.order_by('-created_at').first()
        if latest_version:
            version_parts = latest_version.version_number.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            new_version = f"{major}.{minor + 1}"
        else:
            new_version = "1.0"
        
        # Mark previous version as not current
        form.versions.update(is_current=False)
        
        # Create new version
        version = FormVersion.objects.create(
            form=form,
            version_number=new_version,
            schema=form.schema,
            changes=changes,
            created_by=user,
            is_current=True
        )
        
        return version
    
    def restore_version(self, version: FormVersion, user) -> Form:
        """Restore a form to a specific version"""
        form = version.form
        
        # Create new version before restoring
        self.create_version(form, user, {
            'action': 'restore',
            'restored_from': version.version_number
        })
        
        # Restore form schema
        form.schema = version.schema
        form.save()
        
        # Rebuild fields from schema
        form.fields.all().delete()
        if 'fields' in version.schema:
            for field_data in version.schema['fields']:
                FormField.objects.create(form=form, **field_data)
        
        return form
    
    def generate_preview(self, form: Form) -> Dict:
        """Generate form preview data"""
        fields = []
        for field in form.fields.all():
            field_data = {
                'id': str(field.id),
                'name': field.name,
                'label': field.label,
                'type': field.field_type,
                'placeholder': field.placeholder,
                'help_text': field.help_text,
                'default_value': field.default_value,
                'options': field.options,
                'required': field.is_required,
                'readonly': field.is_readonly,
                'hidden': field.is_hidden,
                'order': field.order,
                'step': field.step,
                'css_classes': field.css_classes,
                'attributes': field.attributes,
                'validation_rules': field.validation_rules,
                'conditional_logic': field.conditional_logic
            }
            fields.append(field_data)
        
        return {
            'form': {
                'id': str(form.id),
                'name': form.name,
                'description': form.description,
                'is_multi_step': form.is_multi_step,
                'steps_config': form.steps_config,
                'settings': form.settings
            },
            'fields': fields
        }

class FormValidationService:
    """Service for form validation operations"""
    
    def validate_submission(self, form_id: str, data: Dict) -> Dict:
        """Validate form submission data"""
        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return {'is_valid': False, 'errors': {'form': 'Form not found'}}
        
        errors = {}
        
        # Validate each field
        for field in form.fields.all():
            field_value = data.get(field.name)
            field_errors = self._validate_field(field, field_value)
            if field_errors:
                errors[field.name] = field_errors
        
        # Check conditional logic
        conditional_errors = self._validate_conditional_logic(form, data)
        errors.update(conditional_errors)
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors
        }
    
    def _validate_field(self, field: FormField, value: Any) -> List[str]:
        """Validate individual field"""
        errors = []
        
        # Required field validation
        if field.is_required and (value is None or value == ''):
            errors.append(f"{field.label} is required")
            return errors
        
        # Skip validation if field is empty and not required
        if value is None or value == '':
            return errors
        
        # Type-specific validation
        if field.field_type == 'email':
            if not self._is_valid_email(value):
                errors.append("Invalid email format")
        
        elif field.field_type == 'url':
            if not self._is_valid_url(value):
                errors.append("Invalid URL format")
        
        elif field.field_type == 'number':
            try:
                float(value)
            except (ValueError, TypeError):
                errors.append("Must be a valid number")
        
        elif field.field_type == 'tel':
            if not self._is_valid_phone(value):
                errors.append("Invalid phone number format")
        
        # Custom validation rules
        if field.validation_rules:
            custom_errors = self._validate_custom_rules(field, value)
            errors.extend(custom_errors)
        
        return errors
    
    def _validate_custom_rules(self, field: FormField, value: Any) -> List[str]:
        """Validate custom validation rules"""
        errors = []
        rules = field.validation_rules
        
        if 'min_length' in rules:
            if len(str(value)) < rules['min_length']:
                errors.append(f"Minimum length is {rules['min_length']} characters")
        
        if 'max_length' in rules:
            if len(str(value)) > rules['max_length']:
                errors.append(f"Maximum length is {rules['max_length']} characters")
        
        if 'pattern' in rules:
            if not re.match(rules['pattern'], str(value)):
                errors.append(rules.get('pattern_message', "Invalid format"))
        
        if 'min_value' in rules and field.field_type == 'number':
            try:
                if float(value) < rules['min_value']:
                    errors.append(f"Minimum value is {rules['min_value']}")
            except (ValueError, TypeError):
                pass
        
        if 'max_value' in rules and field.field_type == 'number':
            try:
                if float(value) > rules['max_value']:
                    errors.append(f"Maximum value is {rules['max_value']}")
            except (ValueError, TypeError):
                pass
        
        return errors
    
    def _validate_conditional_logic(self, form: Form, data: Dict) -> Dict:
        """Validate conditional field logic"""
        errors = {}
        
        for field in form.fields.all():
            if field.conditional_logic:
                if not self._evaluate_conditions(field.conditional_logic, data):
                    # Field should be hidden, remove from validation
                    continue
                
                # Field is visible, validate normally
                field_value = data.get(field.name)
                field_errors = self._validate_field(field, field_value)
                if field_errors:
                    errors[field.name] = field_errors
        
        return errors
    
    def _evaluate_conditions(self, conditions: Dict, data: Dict) -> bool:
        """Evaluate conditional logic"""
        if not conditions:
            return True
        
        operator = conditions.get('operator', 'and')
        rules = conditions.get('rules', [])
        
        results = []
        for rule in rules:
            field_name = rule.get('field')
            condition = rule.get('condition')
            value = rule.get('value')
            field_value = data.get(field_name)
            
            if condition == 'equals':
                results.append(field_value == value)
            elif condition == 'not_equals':
                results.append(field_value != value)
            elif condition == 'contains':
                results.append(value in str(field_value) if field_value else False)
            elif condition == 'not_empty':
                results.append(field_value is not None and field_value != '')
            elif condition == 'empty':
                results.append(field_value is None or field_value == '')
        
        if operator == 'and':
            return all(results)
        elif operator == 'or':
            return any(results)
        
        return True
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        pattern = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
        return re.match(pattern, url) is not None
    
    def _is_valid_phone(self, phone: str) -> bool:
        """Validate phone number format"""
        # Simple phone validation - can be enhanced
        pattern = r'^\+?[\d\s\-\(\)]{10,}$'
        return re.match(pattern, phone) is not None
    
    def check_spam(self, request, data: Dict) -> float:
        """Check submission for spam indicators"""
        spam_score = 0.0
        
        # Check for suspicious patterns
        text_content = ' '.join([str(v) for v in data.values() if isinstance(v, str)])
        
        # URL spam check
        url_count = len(re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text_content))
        if url_count > 2:
            spam_score += 0.3
        
        # Repeated characters
        if re.search(r'(.)\1{4,}', text_content):
            spam_score += 0.2
        
        # All caps
        if text_content.isupper() and len(text_content) > 20:
            spam_score += 0.2
        
        # Suspicious keywords
        spam_keywords = ['viagra', 'casino', 'lottery', 'winner', 'congratulations', 'click here']
        for keyword in spam_keywords:
            if keyword.lower() in text_content.lower():
                spam_score += 0.3
                break
        
        # Rate limiting check
        ip_address = request.META.get('REMOTE_ADDR')
        recent_submissions = FormSubmission.objects.filter(
            ip_address=ip_address,
            submitted_at__gte=timezone.now() - timedelta(minutes=5)
        ).count()
        
        if recent_submissions > 3:
            spam_score += 0.4
        
        return min(spam_score, 1.0)

class FormAnalyticsService:
    """Service for form analytics operations"""
    
    def track_submission(self, submission: FormSubmission):
        """Track form submission for analytics"""
        today = timezone.now().date()
        
        # Get or create analytics record for today
        analytics, created = FormAnalytics.objects.get_or_create(
            form=submission.form,
            date=today,
            defaults={
                'views': 0,
                'starts': 0,
                'completions': 0,
                'abandonment_rate': 0.0,
                'conversion_rate': 0.0,
                'field_analytics': {},
                'device_analytics': {},
                'source_analytics': {}
            }
        )
        
        # Update completion count
        analytics.completions += 1
        
        # Update conversion rate
        if analytics.views > 0:
            analytics.conversion_rate = (analytics.completions / analytics.views) * 100
        
        # Update abandonment rate
        if analytics.starts > 0:
            analytics.abandonment_rate = ((analytics.starts - analytics.completions) / analytics.starts) * 100
        
        analytics.save()
    
    def track_form_view(self, form: Form):
        """Track form view for analytics"""
        today = timezone.now().date()
        
        analytics, created = FormAnalytics.objects.get_or_create(
            form=form,
            date=today,
            defaults={
                'views': 0,
                'starts': 0,
                'completions': 0,
                'abandonment_rate': 0.0,
                'conversion_rate': 0.0,
                'field_analytics': {},
                'device_analytics': {},
                'source_analytics': {}
            }
        )
        
        analytics.views += 1
        analytics.save()
    
    def get_form_analytics(self, form: Form, params: Dict) -> Dict:
        """Get analytics data for a form"""
        date_range = params.get('date_range', 'last_30_days')
        
        # Calculate date range
        end_date = timezone.now().date()
        if date_range == 'today':
            start_date = end_date
        elif date_range == 'yesterday':
            start_date = end_date - timedelta(days=1)
            end_date = start_date
        elif date_range == 'last_7_days':
            start_date = end_date - timedelta(days=7)
        elif date_range == 'last_30_days':
            start_date = end_date - timedelta(days=30)
        elif date_range == 'last_90_days':
            start_date = end_date - timedelta(days=90)
        else:
            start_date = end_date - timedelta(days=30)
        
        # Get analytics data
        analytics = FormAnalytics.objects.filter(
            form=form,
            date__range=[start_date, end_date]
        ).order_by('date')
        
        # Aggregate data
        total_views = sum(a.views for a in analytics)
        total_starts = sum(a.starts for a in analytics)
        total_completions = sum(a.completions for a in analytics)
        
        conversion_rate = (total_completions / total_views * 100) if total_views > 0 else 0
        abandonment_rate = ((total_starts - total_completions) / total_starts * 100) if total_starts > 0 else 0
        
        # Get submissions data
        submissions = FormSubmission.objects.filter(
            form=form,
            submitted_at__date__range=[start_date, end_date]
        )
        
        # Calculate average completion time
        completion_times = [s.completion_time for s in submissions if s.completion_time]
        avg_completion_time = sum(completion_times, timedelta()) / len(completion_times) if completion_times else None
        
        return {
            'summary': {
                'total_views': total_views,
                'total_starts': total_starts,
                'total_completions': total_completions,
                'conversion_rate': round(conversion_rate, 2),
                'abandonment_rate': round(abandonment_rate, 2),
                'average_completion_time': str(avg_completion_time) if avg_completion_time else None
            },
            'daily_data': [
                {
                    'date': a.date.isoformat(),
                    'views': a.views,
                    'starts': a.starts,
                    'completions': a.completions,
                    'conversion_rate': a.conversion_rate,
                    'abandonment_rate': a.abandonment_rate
                }
                for a in analytics
            ],
            'field_analytics': self._get_field_analytics(form, submissions),
            'device_analytics': self._get_device_analytics(submissions),
            'source_analytics': self._get_source_analytics(submissions)
        }
    
    def _get_field_analytics(self, form: Form, submissions) -> Dict:
        """Get field-level analytics"""
        field_data = {}
        
        for field in form.fields.all():
            field_submissions = [s for s in submissions if field.name in s.data]
            completion_rate = (len(field_submissions) / len(submissions) * 100) if submissions else 0
            
            field_data[field.name] = {
                'label': field.label,
                'type': field.field_type,
                'completion_rate': round(completion_rate, 2),
                'total_responses': len(field_submissions)
            }
        
        return field_data
    
    def _get_device_analytics(self, submissions) -> Dict:
        """Get device analytics"""
        device_data = {'desktop': 0, 'mobile': 0, 'tablet': 0, 'unknown': 0}
        
        for submission in submissions:
            user_agent = submission.user_agent.lower()
            if 'mobile' in user_agent:
                device_data['mobile'] += 1
            elif 'tablet' in user_agent:
                device_data['tablet'] += 1
            elif any(browser in user_agent for browser in ['chrome', 'firefox', 'safari', 'edge']):
                device_data['desktop'] += 1
            else:
                device_data['unknown'] += 1
        
        return device_data
    
    def _get_source_analytics(self, submissions) -> Dict:
        """Get traffic source analytics"""
        source_data = {}
        
        for submission in submissions:
            referrer = submission.referrer
            if not referrer:
                source = 'direct'
            elif 'google' in referrer:
                source = 'google'
            elif 'facebook' in referrer:
                source = 'facebook'
            elif 'twitter' in referrer:
                source = 'twitter'
            else:
                source = 'other'
            
            source_data[source] = source_data.get(source, 0) + 1
        
        return source_data
    
    def generate_report(self, params: Dict) -> Dict:
        """Generate comprehensive analytics report"""
        form_id = params['form_id']
        date_range = params['date_range']
        metrics = params['metrics']
        
        try:
            form = Form.objects.get(id=form_id)
        except Form.DoesNotExist:
            return {'error': 'Form not found'}
        
        analytics_data = self.get_form_analytics(form, {'date_range': date_range})
        
        # Filter metrics based on request
        filtered_data = {}
        for metric in metrics:
            if metric in analytics_data:
                filtered_data[metric] = analytics_data[metric]
        
        return {
            'form': {
                'id': str(form.id),
                'name': form.name
            },
            'date_range': date_range,
            'generated_at': timezone.now().isoformat(),
            'data': filtered_data
        }
    
    def get_dashboard_data(self, user) -> Dict:
        """Get dashboard analytics data"""
        # Get user's forms
        forms = Form.objects.filter(created_by=user)
        
        # Get recent analytics
        recent_analytics = FormAnalytics.objects.filter(
            form__in=forms,
            date__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # Aggregate data
        total_forms = forms.count()
        total_submissions = FormSubmission.objects.filter(form__in=forms).count()
        total_views = sum(a.views for a in recent_analytics)
        avg_conversion_rate = sum(a.conversion_rate for a in recent_analytics) / len(recent_analytics) if recent_analytics else 0
        
        # Top performing forms
        top_forms = forms.annotate(
            submission_count=Count('submissions')
        ).order_by('-submission_count')[:5]
        
        return {
            'summary': {
                'total_forms': total_forms,
                'total_submissions': total_submissions,
                'total_views': total_views,
                'average_conversion_rate': round(avg_conversion_rate, 2)
            },
            'top_forms': [
                {
                    'id': str(form.id),
                    'name': form.name,
                    'submissions': form.submission_count
                }
                for form in top_forms
            ],
            'recent_activity': self._get_recent_activity(forms)
        }
    
    def _get_recent_activity(self, forms) -> List[Dict]:
        """Get recent form activity"""
        recent_submissions = FormSubmission.objects.filter(
            form__in=forms
        ).order_by('-submitted_at')[:10]
        
        return [
            {
                'type': 'submission',
                'form_name': submission.form.name,
                'timestamp': submission.submitted_at.isoformat(),
                'status': submission.status
            }
            for submission in recent_submissions
        ]