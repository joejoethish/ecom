import os
import csv
import json
import yaml
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from django.apps import apps
from django.core.files.storage import default_storage
from django.contrib.contenttypes.models import ContentType
from django.db import transaction, connection
from django.utils import timezone
from django.conf import settings
from celery import shared_task
import logging
from .models import (
    DataImportJob, DataExportJob, DataMapping, DataSyncJob,
    DataBackup, DataAuditLog, DataQualityRule, DataLineage
)

logger = logging.getLogger(__name__)


class DataImportService:
    """Service for handling data import operations"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'excel', 'json', 'xml', 'yaml']
    
    def create_import_job(self, user, file_path: str, **kwargs) -> DataImportJob:
        """Create a new import job"""
        try:
            # Get content type for target model
            target_model = kwargs.get('target_model')
            content_type = ContentType.objects.get(model=target_model.lower())
            
            # Get file size
            file_size = default_storage.size(file_path) if default_storage.exists(file_path) else 0
            
            job = DataImportJob.objects.create(
                name=kwargs.get('name'),
                description=kwargs.get('description', ''),
                file_path=file_path,
                file_format=kwargs.get('file_format'),
                file_size=file_size,
                target_model=target_model,
                content_type=content_type,
                mapping_config=kwargs.get('mapping_config', {}),
                validation_rules=kwargs.get('validation_rules', {}),
                transformation_rules=kwargs.get('transformation_rules', {}),
                skip_duplicates=kwargs.get('skip_duplicates', True),
                update_existing=kwargs.get('update_existing', False),
                batch_size=kwargs.get('batch_size', 1000),
                created_by=user
            )
            
            # Start processing asynchronously
            process_import_job.delay(str(job.id))
            
            return job
            
        except Exception as e:
            logger.error(f"Error creating import job: {str(e)}")
            raise
    
    def validate_import_data(self, job: DataImportJob) -> Dict[str, Any]:
        """Validate import data before processing"""
        try:
            # Read data from file
            data = self._read_file_data(job.file_path, job.file_format)
            
            # Apply validation rules
            validation_results = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'total_records': len(data),
                'valid_records': 0,
                'invalid_records': 0
            }
            
            for i, record in enumerate(data):
                record_errors = self._validate_record(record, job.validation_rules)
                if record_errors:
                    validation_results['errors'].extend([
                        {'row': i + 1, 'field': error['field'], 'message': error['message']}
                        for error in record_errors
                    ])
                    validation_results['invalid_records'] += 1
                else:
                    validation_results['valid_records'] += 1
            
            validation_results['is_valid'] = validation_results['invalid_records'] == 0
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating import data: {str(e)}")
            return {
                'is_valid': False,
                'errors': [{'message': f"Validation error: {str(e)}"}],
                'warnings': [],
                'total_records': 0,
                'valid_records': 0,
                'invalid_records': 0
            }
    
    def _read_file_data(self, file_path: str, file_format: str) -> List[Dict]:
        """Read data from file based on format"""
        try:
            if not default_storage.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            with default_storage.open(file_path, 'rb') as file:
                if file_format == 'csv':
                    return self._read_csv_data(file)
                elif file_format == 'excel':
                    return self._read_excel_data(file)
                elif file_format == 'json':
                    return self._read_json_data(file)
                elif file_format == 'xml':
                    return self._read_xml_data(file)
                elif file_format == 'yaml':
                    return self._read_yaml_data(file)
                else:
                    raise ValueError(f"Unsupported file format: {file_format}")
                    
        except Exception as e:
            logger.error(f"Error reading file data: {str(e)}")
            raise
    
    def _read_csv_data(self, file) -> List[Dict]:
        """Read CSV data"""
        data = []
        reader = csv.DictReader(file.read().decode('utf-8').splitlines())
        for row in reader:
            data.append(dict(row))
        return data
    
    def _read_excel_data(self, file) -> List[Dict]:
        """Read Excel data"""
        df = pd.read_excel(file)
        return df.to_dict('records')
    
    def _read_json_data(self, file) -> List[Dict]:
        """Read JSON data"""
        data = json.load(file)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("Invalid JSON format")
    
    def _read_xml_data(self, file) -> List[Dict]:
        """Read XML data"""
        tree = ET.parse(file)
        root = tree.getroot()
        data = []
        
        for item in root:
            record = {}
            for child in item:
                record[child.tag] = child.text
            data.append(record)
        
        return data
    
    def _read_yaml_data(self, file) -> List[Dict]:
        """Read YAML data"""
        data = yaml.safe_load(file)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            raise ValueError("Invalid YAML format")
    
    def _validate_record(self, record: Dict, validation_rules: Dict) -> List[Dict]:
        """Validate a single record against rules"""
        errors = []
        
        for field, rules in validation_rules.items():
            value = record.get(field)
            
            # Required field validation
            if rules.get('required', False) and not value:
                errors.append({
                    'field': field,
                    'message': f"Field '{field}' is required"
                })
                continue
            
            if value is not None:
                # Format validation
                if 'format' in rules:
                    if not self._validate_format(value, rules['format']):
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' has invalid format"
                        })
                
                # Range validation
                if 'min_value' in rules or 'max_value' in rules:
                    try:
                        num_value = float(value)
                        if 'min_value' in rules and num_value < rules['min_value']:
                            errors.append({
                                'field': field,
                                'message': f"Field '{field}' is below minimum value"
                            })
                        if 'max_value' in rules and num_value > rules['max_value']:
                            errors.append({
                                'field': field,
                                'message': f"Field '{field}' is above maximum value"
                            })
                    except ValueError:
                        errors.append({
                            'field': field,
                            'message': f"Field '{field}' is not a valid number"
                        })
        
        return errors
    
    def _validate_format(self, value: str, format_type: str) -> bool:
        """Validate value format"""
        import re
        
        formats = {
            'email': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
            'phone': r'^\+?1?\d{9,15}$',
            'url': r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$',
            'date': r'^\d{4}-\d{2}-\d{2}$',
            'datetime': r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
        }
        
        if format_type in formats:
            return bool(re.match(formats[format_type], str(value)))
        
        return True


class DataExportService:
    """Service for handling data export operations"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'excel', 'json', 'xml', 'yaml', 'pdf']
    
    def create_export_job(self, user, **kwargs) -> DataExportJob:
        """Create a new export job"""
        try:
            # Get content type for source model
            source_model = kwargs.get('source_model')
            content_type = ContentType.objects.get(model=source_model.lower())
            
            job = DataExportJob.objects.create(
                name=kwargs.get('name'),
                description=kwargs.get('description', ''),
                source_model=source_model,
                content_type=content_type,
                export_format=kwargs.get('export_format'),
                field_mapping=kwargs.get('field_mapping', {}),
                filter_criteria=kwargs.get('filter_criteria', {}),
                sort_criteria=kwargs.get('sort_criteria', []),
                include_headers=kwargs.get('include_headers', True),
                compress_output=kwargs.get('compress_output', False),
                encrypt_output=kwargs.get('encrypt_output', False),
                created_by=user
            )
            
            # Start processing asynchronously
            process_export_job.delay(str(job.id))
            
            return job
            
        except Exception as e:
            logger.error(f"Error creating export job: {str(e)}")
            raise
    
    def generate_export_file(self, job: DataExportJob) -> str:
        """Generate export file"""
        try:
            # Get model class
            model_class = apps.get_model(job.content_type.app_label, job.content_type.model)
            
            # Build queryset with filters
            queryset = model_class.objects.all()
            
            if job.filter_criteria:
                queryset = queryset.filter(**job.filter_criteria)
            
            if job.sort_criteria:
                queryset = queryset.order_by(*job.sort_criteria)
            
            # Get data
            data = list(queryset.values())
            
            # Apply field mapping
            if job.field_mapping:
                data = self._apply_field_mapping(data, job.field_mapping)
            
            # Generate file
            file_path = self._generate_file(data, job)
            
            return file_path
            
        except Exception as e:
            logger.error(f"Error generating export file: {str(e)}")
            raise
    
    def _apply_field_mapping(self, data: List[Dict], field_mapping: Dict) -> List[Dict]:
        """Apply field mapping to data"""
        mapped_data = []
        
        for record in data:
            mapped_record = {}
            for source_field, target_field in field_mapping.items():
                if source_field in record:
                    mapped_record[target_field] = record[source_field]
            mapped_data.append(mapped_record)
        
        return mapped_data
    
    def _generate_file(self, data: List[Dict], job: DataExportJob) -> str:
        """Generate file based on format"""
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{job.name}_{timestamp}.{job.export_format}"
        file_path = f"exports/{filename}"
        
        if job.export_format == 'csv':
            self._generate_csv_file(data, file_path, job.include_headers)
        elif job.export_format == 'excel':
            self._generate_excel_file(data, file_path, job.include_headers)
        elif job.export_format == 'json':
            self._generate_json_file(data, file_path)
        elif job.export_format == 'xml':
            self._generate_xml_file(data, file_path)
        elif job.export_format == 'yaml':
            self._generate_yaml_file(data, file_path)
        
        return file_path
    
    def _generate_csv_file(self, data: List[Dict], file_path: str, include_headers: bool):
        """Generate CSV file"""
        if not data:
            return
        
        with default_storage.open(file_path, 'w') as file:
            writer = csv.DictWriter(file, fieldnames=data[0].keys())
            if include_headers:
                writer.writeheader()
            writer.writerows(data)
    
    def _generate_excel_file(self, data: List[Dict], file_path: str, include_headers: bool):
        """Generate Excel file"""
        df = pd.DataFrame(data)
        with default_storage.open(file_path, 'wb') as file:
            df.to_excel(file, index=False, header=include_headers)
    
    def _generate_json_file(self, data: List[Dict], file_path: str):
        """Generate JSON file"""
        with default_storage.open(file_path, 'w') as file:
            json.dump(data, file, indent=2, default=str)
    
    def _generate_xml_file(self, data: List[Dict], file_path: str):
        """Generate XML file"""
        root = ET.Element('data')
        
        for record in data:
            item = ET.SubElement(root, 'item')
            for key, value in record.items():
                field = ET.SubElement(item, key)
                field.text = str(value) if value is not None else ''
        
        tree = ET.ElementTree(root)
        with default_storage.open(file_path, 'wb') as file:
            tree.write(file, encoding='utf-8', xml_declaration=True)
    
    def _generate_yaml_file(self, data: List[Dict], file_path: str):
        """Generate YAML file"""
        with default_storage.open(file_path, 'w') as file:
            yaml.dump(data, file, default_flow_style=False)


class DataTransformationService:
    """Service for data transformation operations"""
    
    def transform_data(self, data: List[Dict], transformation_rules: Dict) -> List[Dict]:
        """Apply transformation rules to data"""
        transformed_data = []
        
        for record in data:
            transformed_record = record.copy()
            
            for field, rules in transformation_rules.items():
                if field in transformed_record:
                    value = transformed_record[field]
                    transformed_record[field] = self._apply_transformations(value, rules)
            
            transformed_data.append(transformed_record)
        
        return transformed_data
    
    def _apply_transformations(self, value: Any, rules: List[Dict]) -> Any:
        """Apply transformation rules to a value"""
        for rule in rules:
            transformation_type = rule.get('type')
            parameters = rule.get('parameters', {})
            
            if transformation_type == 'uppercase':
                value = str(value).upper()
            elif transformation_type == 'lowercase':
                value = str(value).lower()
            elif transformation_type == 'trim':
                value = str(value).strip()
            elif transformation_type == 'replace':
                old_value = parameters.get('old', '')
                new_value = parameters.get('new', '')
                value = str(value).replace(old_value, new_value)
            elif transformation_type == 'format_date':
                from datetime import datetime
                try:
                    date_obj = datetime.strptime(str(value), parameters.get('input_format', '%Y-%m-%d'))
                    value = date_obj.strftime(parameters.get('output_format', '%Y-%m-%d'))
                except ValueError:
                    pass  # Keep original value if parsing fails
            elif transformation_type == 'format_number':
                try:
                    num_value = float(value)
                    decimals = parameters.get('decimals', 2)
                    value = round(num_value, decimals)
                except ValueError:
                    pass  # Keep original value if conversion fails
        
        return value


class DataQualityService:
    """Service for data quality monitoring and validation"""
    
    def check_data_quality(self, model_name: str, data: List[Dict]) -> Dict[str, Any]:
        """Check data quality against defined rules"""
        rules = DataQualityRule.objects.filter(
            target_model=model_name,
            is_active=True
        )
        
        quality_report = {
            'total_records': len(data),
            'quality_score': 0,
            'issues': [],
            'rule_results': []
        }
        
        total_checks = 0
        passed_checks = 0
        
        for rule in rules:
            rule_result = self._check_quality_rule(rule, data)
            quality_report['rule_results'].append(rule_result)
            
            total_checks += rule_result['total_checks']
            passed_checks += rule_result['passed_checks']
            
            if rule_result['issues']:
                quality_report['issues'].extend(rule_result['issues'])
        
        if total_checks > 0:
            quality_report['quality_score'] = (passed_checks / total_checks) * 100
        
        return quality_report
    
    def _check_quality_rule(self, rule: DataQualityRule, data: List[Dict]) -> Dict[str, Any]:
        """Check a specific quality rule against data"""
        result = {
            'rule_name': rule.name,
            'rule_type': rule.rule_type,
            'total_checks': 0,
            'passed_checks': 0,
            'issues': []
        }
        
        for i, record in enumerate(data):
            result['total_checks'] += 1
            
            if self._validate_quality_rule(rule, record):
                result['passed_checks'] += 1
            else:
                result['issues'].append({
                    'row': i + 1,
                    'field': rule.target_field,
                    'rule': rule.name,
                    'severity': rule.severity,
                    'message': f"Quality rule '{rule.name}' failed for field '{rule.target_field}'"
                })
        
        return result
    
    def _validate_quality_rule(self, rule: DataQualityRule, record: Dict) -> bool:
        """Validate a single record against a quality rule"""
        field_value = record.get(rule.target_field)
        rule_config = rule.rule_config
        
        if rule.rule_type == 'required':
            return field_value is not None and str(field_value).strip() != ''
        
        elif rule.rule_type == 'format':
            if field_value is None:
                return True  # Skip format check for null values
            pattern = rule_config.get('pattern', '')
            import re
            return bool(re.match(pattern, str(field_value)))
        
        elif rule.rule_type == 'range':
            if field_value is None:
                return True  # Skip range check for null values
            try:
                num_value = float(field_value)
                min_val = rule_config.get('min_value')
                max_val = rule_config.get('max_value')
                
                if min_val is not None and num_value < min_val:
                    return False
                if max_val is not None and num_value > max_val:
                    return False
                
                return True
            except ValueError:
                return False
        
        elif rule.rule_type == 'unique':
            # This would require checking against existing data in the database
            # Implementation depends on specific requirements
            return True
        
        return True


# Celery tasks for asynchronous processing
@shared_task
def process_import_job(job_id: str):
    """Process import job asynchronously"""
    try:
        job = DataImportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        service = DataImportService()
        
        # Validate data
        validation_results = service.validate_import_data(job)
        job.validation_errors = validation_results['errors']
        job.total_records = validation_results['total_records']
        job.save()
        
        if not validation_results['is_valid']:
            job.status = 'failed'
            job.completed_at = timezone.now()
            job.save()
            return
        
        # Process data in batches
        data = service._read_file_data(job.file_path, job.file_format)
        
        # Apply transformations
        if job.transformation_rules:
            transformation_service = DataTransformationService()
            data = transformation_service.transform_data(data, job.transformation_rules)
        
        # Import data
        model_class = apps.get_model(job.content_type.app_label, job.content_type.model)
        
        batch_size = job.batch_size
        total_batches = (len(data) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(data))
            batch_data = data[start_idx:end_idx]
            
            # Process batch
            for record in batch_data:
                try:
                    # Create or update record
                    if job.update_existing:
                        # Try to find existing record and update
                        # Implementation depends on specific model requirements
                        pass
                    else:
                        # Create new record
                        model_class.objects.create(**record)
                    
                    job.successful_records += 1
                    
                except Exception as e:
                    job.failed_records += 1
                    job.error_log.append({
                        'record': record,
                        'error': str(e)
                    })
                
                job.processed_records += 1
            
            # Update progress
            job.progress_percentage = int((job.processed_records / job.total_records) * 100)
            job.save()
        
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.save()
        
    except Exception as e:
        logger.error(f"Error processing import job {job_id}: {str(e)}")
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_log.append({'error': str(e)})
        job.save()


@shared_task
def process_export_job(job_id: str):
    """Process export job asynchronously"""
    try:
        job = DataExportJob.objects.get(id=job_id)
        job.status = 'processing'
        job.started_at = timezone.now()
        job.save()
        
        service = DataExportService()
        file_path = service.generate_export_file(job)
        
        job.file_path = file_path
        job.file_size = default_storage.size(file_path) if default_storage.exists(file_path) else 0
        job.status = 'completed'
        job.completed_at = timezone.now()
        job.progress_percentage = 100
        job.save()
        
    except Exception as e:
        logger.error(f"Error processing export job {job_id}: {str(e)}")
        job.status = 'failed'
        job.completed_at = timezone.now()
        job.error_log.append({'error': str(e)})
        job.save()


@shared_task
def cleanup_expired_exports():
    """Clean up expired export files"""
    try:
        expired_jobs = DataExportJob.objects.filter(
            expires_at__lt=timezone.now(),
            status='completed'
        )
        
        for job in expired_jobs:
            if job.file_path and default_storage.exists(job.file_path):
                default_storage.delete(job.file_path)
            job.delete()
            
    except Exception as e:
        logger.error(f"Error cleaning up expired exports: {str(e)}")