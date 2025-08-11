"""
Advanced Content Management System services.
"""
from django.db import transaction
from django.db import models
from django.utils import timezone
from django.core.files.base import ContentFile
from django.contrib.auth import get_user_model
import json
import uuid
import mimetypes
from typing import Dict, List, Any, Optional

from .models import (
    AdvancedContentPage, ContentVersion, ContentWorkflow, ContentWorkflowInstance,
    ContentAsset, ContentCategory, ContentTag, ContentTemplate, ContentSchedule,
    ContentAnalytics
)

User = get_user_model()


class AdvancedContentService:
    """
    Service for advanced content management operations.
    """
    
    @staticmethod
    def create_version(content_page: AdvancedContentPage, user: User, change_summary: str = "") -> ContentVersion:
        """
        Create a new version of a content page.
        """
        with transaction.atomic():
            # Get next version number
            last_version = content_page.versions.order_by('-version_number').first()
            next_version = (last_version.version_number + 1) if last_version else 1
            
            # Mark all previous versions as not current
            content_page.versions.update(is_current=False)
            
            # Create new version
            version = ContentVersion.objects.create(
                content_page=content_page,
                version_number=next_version,
                title=content_page.title,
                content=content_page.content,
                content_json=content_page.content_json,
                change_summary=change_summary,
                created_by=user,
                is_current=True,
                metadata_snapshot={
                    'status': content_page.status,
                    'meta_title': content_page.meta_title,
                    'meta_description': content_page.meta_description,
                    'personalization_type': content_page.personalization_type,
                    'language': content_page.language,
                }
            )
            
            return version
    
    @staticmethod
    def revert_to_version(content_page: AdvancedContentPage, version_number: int, user: User) -> None:
        """
        Revert content page to a specific version.
        """
        version = content_page.versions.filter(version_number=version_number).first()
        if not version:
            raise ValueError(f"Version {version_number} not found")
        
        with transaction.atomic():
            # Update content page with version data
            content_page.title = version.title
            content_page.content = version.content
            content_page.content_json = version.content_json
            content_page.status = 'draft'  # Reset to draft when reverting
            content_page.save()
            
            # Create a new version for this revert
            AdvancedContentService.create_version(
                content_page, user, f"Reverted to version {version_number}"
            )
    
    @staticmethod
    def publish_content(content_page: AdvancedContentPage, user: User, publish_date: Optional[str] = None) -> None:
        """
        Publish content page.
        """
        with transaction.atomic():
            content_page.status = 'published'
            content_page.is_published = True
            content_page.publish_date = timezone.now() if not publish_date else publish_date
            content_page.save()
            
            # Create version for publish action
            AdvancedContentService.create_version(
                content_page, user, "Content published"
            )
    
    @staticmethod
    def unpublish_content(content_page: AdvancedContentPage, user: User) -> None:
        """
        Unpublish content page.
        """
        with transaction.atomic():
            content_page.is_published = False
            content_page.unpublish_date = timezone.now()
            content_page.save()
            
            # Create version for unpublish action
            AdvancedContentService.create_version(
                content_page, user, "Content unpublished"
            )
    
    @staticmethod
    def duplicate_content(content_page: AdvancedContentPage, user: User) -> AdvancedContentPage:
        """
        Duplicate a content page.
        """
        # Create a copy
        content_page.pk = None
        content_page.title = f"{content_page.title} (Copy)"
        content_page.slug = f"{content_page.slug}-copy-{uuid.uuid4().hex[:8]}"
        content_page.status = 'draft'
        content_page.is_published = False
        content_page.author = user
        content_page.publish_date = None
        content_page.unpublish_date = None
        content_page.view_count = 0
        content_page.engagement_score = 0
        content_page.conversion_rate = 0
        content_page.bounce_rate = 0
        content_page.save()
        
        # Create initial version
        AdvancedContentService.create_version(
            content_page, user, "Initial version of duplicated content"
        )
        
        return content_page
    
    @staticmethod
    def get_dashboard_data() -> Dict[str, Any]:
        """
        Get content management dashboard data.
        """
        total_pages = AdvancedContentPage.objects.filter(is_deleted=False).count()
        published_pages = AdvancedContentPage.objects.filter(
            is_deleted=False, is_published=True
        ).count()
        draft_pages = AdvancedContentPage.objects.filter(
            is_deleted=False, status='draft'
        ).count()
        pending_approval = ContentWorkflowInstance.objects.filter(
            is_deleted=False, status__in=['pending', 'in_progress']
        ).count()
        
        total_views = AdvancedContentPage.objects.filter(
            is_deleted=False
        ).aggregate(total=models.Sum('view_count'))['total'] or 0
        
        total_assets = ContentAsset.objects.filter(is_deleted=False).count()
        
        # Recent activity (last 10 activities)
        recent_activity = []
        recent_pages = AdvancedContentPage.objects.filter(
            is_deleted=False
        ).order_by('-updated_at')[:5]
        
        for page in recent_pages:
            recent_activity.append({
                'type': 'page_updated',
                'title': page.title,
                'user': page.author.username,
                'timestamp': page.updated_at,
                'status': page.status
            })
        
        # Top performing pages
        top_performing = AdvancedContentPage.objects.filter(
            is_deleted=False, is_published=True
        ).order_by('-view_count')[:10]
        
        top_performing_data = []
        for page in top_performing:
            top_performing_data.append({
                'page_id': page.id,
                'title': page.title,
                'page_type': page.page_type,
                'views': page.view_count,
                'engagement_score': float(page.engagement_score),
                'conversion_rate': float(page.conversion_rate),
                'bounce_rate': float(page.bounce_rate),
                'avg_time_on_page': 0,  # Would need analytics integration
                'social_shares': 0  # Would need social media integration
            })
        
        return {
            'total_pages': total_pages,
            'published_pages': published_pages,
            'draft_pages': draft_pages,
            'pending_approval': pending_approval,
            'total_views': total_views,
            'total_assets': total_assets,
            'recent_activity': recent_activity,
            'top_performing_pages': top_performing_data
        }
    
    @staticmethod
    def get_category_tree() -> List[Dict[str, Any]]:
        """
        Get hierarchical category tree.
        """
        def build_tree(parent=None):
            categories = ContentCategory.objects.filter(
                parent=parent, is_deleted=False, is_active=True
            ).order_by('sort_order', 'name')
            
            tree = []
            for category in categories:
                tree.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'description': category.description,
                    'icon': category.icon,
                    'color': category.color,
                    'sort_order': category.sort_order,
                    'children': build_tree(category)
                })
            
            return tree
        
        return build_tree()
    
    @staticmethod
    def export_content(export_data: Dict[str, Any]) -> Any:
        """
        Export content in various formats.
        """
        content_ids = export_data['content_ids']
        export_format = export_data['export_format']
        include_assets = export_data.get('include_assets', False)
        include_versions = export_data.get('include_versions', False)
        
        pages = AdvancedContentPage.objects.filter(
            id__in=content_ids, is_deleted=False
        )
        
        export_result = []
        for page in pages:
            page_data = {
                'id': page.id,
                'title': page.title,
                'slug': page.slug,
                'page_type': page.page_type,
                'content': page.content,
                'content_json': page.content_json,
                'status': page.status,
                'meta_title': page.meta_title,
                'meta_description': page.meta_description,
                'language': page.language,
                'created_at': page.created_at.isoformat(),
                'updated_at': page.updated_at.isoformat(),
            }
            
            if include_versions:
                versions = page.versions.all().order_by('-version_number')
                page_data['versions'] = [
                    {
                        'version_number': v.version_number,
                        'title': v.title,
                        'content': v.content,
                        'change_summary': v.change_summary,
                        'created_at': v.created_at.isoformat(),
                    }
                    for v in versions
                ]
            
            if include_assets:
                # This would include related assets
                page_data['assets'] = []
            
            export_result.append(page_data)
        
        return export_result
    
    @staticmethod
    def import_content(import_data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """
        Import content from various formats.
        """
        import_file = import_data['import_file']
        import_format = import_data['import_format']
        overwrite_existing = import_data.get('overwrite_existing', False)
        create_backup = import_data.get('create_backup', True)
        
        # Parse import file based on format
        if import_format == 'json':
            content_data = json.loads(import_file.read().decode('utf-8'))
        else:
            raise ValueError(f"Import format {import_format} not yet implemented")
        
        imported_count = 0
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for item in content_data:
                try:
                    slug = item.get('slug')
                    existing_page = AdvancedContentPage.objects.filter(
                        slug=slug, is_deleted=False
                    ).first()
                    
                    if existing_page and not overwrite_existing:
                        errors.append(f"Page with slug '{slug}' already exists")
                        continue
                    
                    if existing_page and create_backup:
                        # Create backup version
                        AdvancedContentService.create_version(
                            existing_page, user, "Backup before import"
                        )
                    
                    # Create or update page
                    page_data = {
                        'title': item['title'],
                        'slug': item['slug'],
                        'page_type': item.get('page_type', 'page'),
                        'content': item['content'],
                        'content_json': item.get('content_json', {}),
                        'status': item.get('status', 'draft'),
                        'meta_title': item.get('meta_title', ''),
                        'meta_description': item.get('meta_description', ''),
                        'language': item.get('language', 'en'),
                        'author': user,
                    }
                    
                    if existing_page:
                        for key, value in page_data.items():
                            setattr(existing_page, key, value)
                        existing_page.save()
                        updated_count += 1
                    else:
                        AdvancedContentPage.objects.create(**page_data)
                        imported_count += 1
                
                except Exception as e:
                    errors.append(f"Error importing item: {str(e)}")
        
        return {
            'imported_count': imported_count,
            'updated_count': updated_count,
            'errors': errors
        }
    
    @staticmethod
    def bulk_operations(operation: str, content_ids: List[int], operation_data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """
        Perform bulk operations on content.
        """
        pages = AdvancedContentPage.objects.filter(
            id__in=content_ids, is_deleted=False
        )
        
        updated_count = 0
        errors = []
        
        with transaction.atomic():
            for page in pages:
                try:
                    if operation == 'publish':
                        AdvancedContentService.publish_content(page, user)
                        updated_count += 1
                    elif operation == 'unpublish':
                        AdvancedContentService.unpublish_content(page, user)
                        updated_count += 1
                    elif operation == 'update_status':
                        page.status = operation_data.get('status', 'draft')
                        page.save()
                        updated_count += 1
                    elif operation == 'update_category':
                        category_id = operation_data.get('category_id')
                        if category_id:
                            page.category_id = category_id
                            page.save()
                            updated_count += 1
                    elif operation == 'delete':
                        page.is_deleted = True
                        page.save()
                        updated_count += 1
                    else:
                        errors.append(f"Unknown operation: {operation}")
                
                except Exception as e:
                    errors.append(f"Error processing page {page.id}: {str(e)}")
        
        return {
            'updated_count': updated_count,
            'errors': errors
        }
    
    @staticmethod
    def schedule_content_action(content_id: int, action_type: str, scheduled_time: str, action_data: Dict[str, Any], user: User) -> ContentSchedule:
        """
        Schedule a content action.
        """
        content_page = AdvancedContentPage.objects.get(id=content_id, is_deleted=False)
        
        schedule = ContentSchedule.objects.create(
            content_page=content_page,
            action_type=action_type,
            scheduled_time=scheduled_time,
            action_data=action_data,
            created_by=user
        )
        
        return schedule


class ContentWorkflowService:
    """
    Service for content workflow management.
    """
    
    @staticmethod
    def submit_for_review(content_page: AdvancedContentPage, workflow_id: Optional[int], user: User) -> ContentWorkflowInstance:
        """
        Submit content page for workflow review.
        """
        if workflow_id:
            workflow = ContentWorkflow.objects.get(id=workflow_id, is_active=True)
        else:
            # Use default workflow
            workflow = ContentWorkflow.objects.filter(is_default=True, is_active=True).first()
            if not workflow:
                raise ValueError("No default workflow found")
        
        # Check if there's already an active workflow
        active_workflow = content_page.workflow_instances.filter(
            status__in=['pending', 'in_progress']
        ).first()
        
        if active_workflow:
            raise ValueError("Content already has an active workflow")
        
        workflow_instance = ContentWorkflowInstance.objects.create(
            content_page=content_page,
            workflow=workflow,
            status='pending',
            current_step=0,
            initiated_by=user,
            workflow_data={'steps_completed': []}
        )
        
        return workflow_instance
    
    @staticmethod
    def process_workflow_step(workflow_instance: ContentWorkflowInstance, user: User, action_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a workflow step (approve, reject, etc.).
        """
        action = action_data['action']
        comments = action_data.get('comments', '')
        
        with transaction.atomic():
            if action == 'approve':
                workflow_instance.current_step += 1
                workflow_instance.workflow_data['steps_completed'].append({
                    'step': workflow_instance.current_step - 1,
                    'action': 'approved',
                    'user': user.username,
                    'timestamp': timezone.now().isoformat(),
                    'comments': comments
                })
                
                # Check if workflow is complete
                total_steps = len(workflow_instance.workflow.steps)
                if workflow_instance.current_step >= total_steps:
                    workflow_instance.status = 'approved'
                    workflow_instance.completion_date = timezone.now()
                    
                    # Auto-publish if configured
                    if workflow_instance.workflow.auto_publish:
                        AdvancedContentService.publish_content(
                            workflow_instance.content_page, user
                        )
                else:
                    workflow_instance.status = 'in_progress'
                
            elif action == 'reject':
                workflow_instance.status = 'rejected'
                workflow_instance.rejection_reason = comments
                workflow_instance.completion_date = timezone.now()
                
            elif action == 'request_changes':
                workflow_instance.status = 'pending'
                workflow_instance.current_step = 0
                workflow_instance.comments = comments
            
            workflow_instance.save()
        
        return {
            'status': workflow_instance.status,
            'current_step': workflow_instance.current_step,
            'message': f'Workflow {action} processed successfully'
        }


class ContentAssetService:
    """
    Service for content asset management.
    """
    
    @staticmethod
    def bulk_upload_assets(files: List, user: User, category_id: Optional[int] = None, is_public: bool = True) -> List[ContentAsset]:
        """
        Bulk upload content assets.
        """
        uploaded_assets = []
        
        for file in files:
            # Determine asset type based on MIME type
            mime_type, _ = mimetypes.guess_type(file.name)
            asset_type = 'other'
            
            if mime_type:
                if mime_type.startswith('image/'):
                    asset_type = 'image'
                elif mime_type.startswith('video/'):
                    asset_type = 'video'
                elif mime_type.startswith('audio/'):
                    asset_type = 'audio'
                elif mime_type in ['application/pdf', 'application/msword', 'text/plain']:
                    asset_type = 'document'
                elif mime_type in ['application/zip', 'application/x-rar']:
                    asset_type = 'archive'
            
            asset = ContentAsset.objects.create(
                name=file.name,
                asset_type=asset_type,
                file=file,
                file_size=file.size,
                mime_type=mime_type or 'application/octet-stream',
                original_filename=file.name,
                category_id=category_id,
                is_public=is_public,
                uploaded_by=user
            )
            
            uploaded_assets.append(asset)
        
        return uploaded_assets


class PageBuilderService:
    """
    Service for page builder functionality.
    """
    
    @staticmethod
    def save_page_data(page_id: int, page_data: Dict[str, Any]) -> None:
        """
        Save page builder data to content page.
        """
        content_page = AdvancedContentPage.objects.get(id=page_id, is_deleted=False)
        content_page.content_json = page_data
        content_page.save()
    
    @staticmethod
    def get_page_data(page_id: int) -> Dict[str, Any]:
        """
        Get page builder data from content page.
        """
        content_page = AdvancedContentPage.objects.get(id=page_id, is_deleted=False)
        return content_page.content_json or {}
    
    @staticmethod
    def get_available_components() -> List[Dict[str, Any]]:
        """
        Get available page builder components.
        """
        return [
            {
                'id': 'text',
                'name': 'Text Block',
                'category': 'content',
                'icon': 'text',
                'props': {
                    'content': {'type': 'string', 'default': 'Enter your text here...'},
                    'fontSize': {'type': 'number', 'default': 16},
                    'color': {'type': 'color', 'default': '#000000'},
                    'alignment': {'type': 'select', 'options': ['left', 'center', 'right'], 'default': 'left'}
                }
            },
            {
                'id': 'image',
                'name': 'Image',
                'category': 'media',
                'icon': 'image',
                'props': {
                    'src': {'type': 'string', 'default': ''},
                    'alt': {'type': 'string', 'default': ''},
                    'width': {'type': 'number', 'default': 100},
                    'height': {'type': 'number', 'default': 'auto'}
                }
            },
            {
                'id': 'button',
                'name': 'Button',
                'category': 'interactive',
                'icon': 'button',
                'props': {
                    'text': {'type': 'string', 'default': 'Click me'},
                    'url': {'type': 'string', 'default': '#'},
                    'style': {'type': 'select', 'options': ['primary', 'secondary', 'outline'], 'default': 'primary'},
                    'size': {'type': 'select', 'options': ['small', 'medium', 'large'], 'default': 'medium'}
                }
            },
            {
                'id': 'container',
                'name': 'Container',
                'category': 'layout',
                'icon': 'container',
                'props': {
                    'backgroundColor': {'type': 'color', 'default': 'transparent'},
                    'padding': {'type': 'number', 'default': 20},
                    'margin': {'type': 'number', 'default': 0},
                    'maxWidth': {'type': 'number', 'default': 1200}
                }
            },
            {
                'id': 'columns',
                'name': 'Columns',
                'category': 'layout',
                'icon': 'columns',
                'props': {
                    'columns': {'type': 'number', 'default': 2, 'min': 1, 'max': 6},
                    'gap': {'type': 'number', 'default': 20}
                }
            }
        ]


class ContentAnalyticsService:
    """
    Service for content analytics.
    """
    
    @staticmethod
    def get_page_analytics(page_id: int, date_from: Optional[str] = None, date_to: Optional[str] = None) -> Dict[str, Any]:
        """
        Get analytics for a specific content page.
        """
        content_page = AdvancedContentPage.objects.get(id=page_id, is_deleted=False)
        
        # This would typically integrate with analytics services like Google Analytics
        # For now, return mock data based on the page's stored metrics
        return {
            'page_id': page_id,
            'title': content_page.title,
            'views': content_page.view_count,
            'engagement_score': float(content_page.engagement_score),
            'conversion_rate': float(content_page.conversion_rate),
            'bounce_rate': float(content_page.bounce_rate),
            'avg_time_on_page': 120,  # Mock data
            'unique_visitors': int(content_page.view_count * 0.7),  # Mock calculation
            'returning_visitors': int(content_page.view_count * 0.3),  # Mock calculation
            'social_shares': 0,  # Would need social media integration
            'comments': 0,  # Would need comment system integration
            'downloads': 0,  # Would need download tracking
        }
    
    @staticmethod
    def get_comprehensive_analytics(date_from: Optional[str] = None, date_to: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive content analytics.
        """
        queryset = AdvancedContentPage.objects.filter(is_deleted=False)
        
        if content_type:
            queryset = queryset.filter(page_type=content_type)
        
        total_pages = queryset.count()
        total_views = queryset.aggregate(total=models.Sum('view_count'))['total'] or 0
        avg_engagement = queryset.aggregate(avg=models.Avg('engagement_score'))['avg'] or 0
        
        # Top performing pages
        top_pages = queryset.order_by('-view_count')[:10]
        top_pages_data = []
        
        for page in top_pages:
            top_pages_data.append({
                'page_id': page.id,
                'title': page.title,
                'page_type': page.page_type,
                'views': page.view_count,
                'engagement_score': float(page.engagement_score),
                'conversion_rate': float(page.conversion_rate),
                'bounce_rate': float(page.bounce_rate),
                'avg_time_on_page': 120,  # Mock data
                'social_shares': 0  # Mock data
            })
        
        return {
            'summary': {
                'total_pages': total_pages,
                'total_views': total_views,
                'avg_engagement_score': float(avg_engagement),
                'published_pages': queryset.filter(is_published=True).count(),
                'draft_pages': queryset.filter(status='draft').count(),
            },
            'top_performing_pages': top_pages_data,
            'content_types': {
                'page': queryset.filter(page_type='page').count(),
                'blog': queryset.filter(page_type='blog').count(),
                'landing': queryset.filter(page_type='landing').count(),
                'news': queryset.filter(page_type='news').count(),
            },
            'languages': {
                'en': queryset.filter(language='en').count(),
                'es': queryset.filter(language='es').count(),
                'fr': queryset.filter(language='fr').count(),
            }
        }