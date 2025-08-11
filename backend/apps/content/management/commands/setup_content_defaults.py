"""
Management command to set up default content templates and workflows.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.content.models import (
    ContentTemplate, ContentWorkflow, ContentCategory, ContentTag
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up default content templates, workflows, categories, and tags'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default content management data...')
        
        # Create default admin user if needed
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        # Create default content categories
        self.create_default_categories()
        
        # Create default content tags
        self.create_default_tags()
        
        # Create default content templates
        self.create_default_templates(admin_user)
        
        # Create default workflows
        self.create_default_workflows()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up default content management data')
        )

    def create_default_categories(self):
        """Create default content categories."""
        categories = [
            {'name': 'General', 'slug': 'general', 'description': 'General content'},
            {'name': 'Marketing', 'slug': 'marketing', 'description': 'Marketing content'},
            {'name': 'Legal', 'slug': 'legal', 'description': 'Legal documents'},
            {'name': 'Help', 'slug': 'help', 'description': 'Help and support content'},
            {'name': 'News', 'slug': 'news', 'description': 'News and announcements'},
        ]
        
        for cat_data in categories:
            category, created = ContentCategory.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_default_tags(self):
        """Create default content tags."""
        tags = [
            {'name': 'Important', 'slug': 'important', 'color': '#ff0000', 'is_featured': True},
            {'name': 'Featured', 'slug': 'featured', 'color': '#00ff00', 'is_featured': True},
            {'name': 'New', 'slug': 'new', 'color': '#0000ff'},
            {'name': 'Updated', 'slug': 'updated', 'color': '#ff9900'},
            {'name': 'Draft', 'slug': 'draft', 'color': '#999999'},
        ]
        
        for tag_data in tags:
            tag, created = ContentTag.objects.get_or_create(
                slug=tag_data['slug'],
                defaults=tag_data
            )
            if created:
                self.stdout.write(f'Created tag: {tag.name}')

    def create_default_templates(self, admin_user):
        """Create default content templates."""
        templates = [
            {
                'name': 'Basic Page',
                'template_type': 'page',
                'description': 'Basic page template with header, content, and footer',
                'structure': {
                    'components': [
                        {
                            'id': 'header',
                            'type': 'container',
                            'props': {'backgroundColor': '#f8f9fa', 'padding': 20},
                            'children': [
                                {
                                    'id': 'title',
                                    'type': 'text',
                                    'props': {'content': 'Page Title', 'fontSize': 32, 'alignment': 'center'}
                                }
                            ]
                        },
                        {
                            'id': 'content',
                            'type': 'container',
                            'props': {'padding': 40},
                            'children': [
                                {
                                    'id': 'main-text',
                                    'type': 'text',
                                    'props': {'content': 'Main content goes here...', 'fontSize': 16}
                                }
                            ]
                        }
                    ]
                },
                'is_system_template': True,
                'required_fields': ['title', 'content'],
                'optional_fields': ['excerpt', 'meta_description']
            },
            {
                'name': 'Landing Page',
                'template_type': 'landing',
                'description': 'Landing page template with hero section and call-to-action',
                'structure': {
                    'components': [
                        {
                            'id': 'hero',
                            'type': 'container',
                            'props': {'backgroundColor': '#007bff', 'padding': 60},
                            'children': [
                                {
                                    'id': 'hero-title',
                                    'type': 'text',
                                    'props': {'content': 'Hero Title', 'fontSize': 48, 'color': '#ffffff', 'alignment': 'center'}
                                },
                                {
                                    'id': 'hero-subtitle',
                                    'type': 'text',
                                    'props': {'content': 'Hero subtitle', 'fontSize': 20, 'color': '#ffffff', 'alignment': 'center'}
                                },
                                {
                                    'id': 'cta-button',
                                    'type': 'button',
                                    'props': {'text': 'Get Started', 'style': 'primary', 'size': 'large'}
                                }
                            ]
                        }
                    ]
                },
                'is_system_template': True,
                'required_fields': ['title', 'hero_title', 'cta_text'],
                'optional_fields': ['hero_subtitle', 'hero_image']
            },
            {
                'name': 'Blog Post',
                'template_type': 'blog',
                'description': 'Blog post template with author info and social sharing',
                'structure': {
                    'components': [
                        {
                            'id': 'article-header',
                            'type': 'container',
                            'props': {'padding': 20},
                            'children': [
                                {
                                    'id': 'article-title',
                                    'type': 'text',
                                    'props': {'content': 'Article Title', 'fontSize': 36}
                                },
                                {
                                    'id': 'article-meta',
                                    'type': 'text',
                                    'props': {'content': 'By Author | Date', 'fontSize': 14, 'color': '#666666'}
                                }
                            ]
                        },
                        {
                            'id': 'article-content',
                            'type': 'container',
                            'props': {'padding': 20},
                            'children': [
                                {
                                    'id': 'article-text',
                                    'type': 'text',
                                    'props': {'content': 'Article content...', 'fontSize': 16}
                                }
                            ]
                        }
                    ]
                },
                'is_system_template': True,
                'required_fields': ['title', 'content', 'author'],
                'optional_fields': ['excerpt', 'featured_image', 'tags']
            }
        ]
        
        for template_data in templates:
            template, created = ContentTemplate.objects.get_or_create(
                name=template_data['name'],
                template_type=template_data['template_type'],
                defaults={**template_data, 'created_by': admin_user}
            )
            if created:
                self.stdout.write(f'Created template: {template.name}')

    def create_default_workflows(self):
        """Create default content workflows."""
        workflows = [
            {
                'name': 'Simple Approval',
                'workflow_type': 'simple',
                'description': 'Simple one-step approval workflow',
                'is_default': True,
                'auto_publish': True,
                'steps': [
                    {
                        'step_id': 'review',
                        'name': 'Content Review',
                        'description': 'Review content for approval',
                        'assignee_role': 'editor',
                        'required_permissions': ['content.change_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 24
                    }
                ],
                'notification_settings': {
                    'notify_on_submit': True,
                    'notify_on_approve': True,
                    'notify_on_reject': True
                },
                'applicable_content_types': ['page', 'blog', 'news']
            },
            {
                'name': 'Multi-Level Review',
                'workflow_type': 'multi_level',
                'description': 'Multi-level approval workflow with editor and manager review',
                'auto_publish': False,
                'steps': [
                    {
                        'step_id': 'editor_review',
                        'name': 'Editor Review',
                        'description': 'Initial review by content editor',
                        'assignee_role': 'editor',
                        'required_permissions': ['content.change_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 24
                    },
                    {
                        'step_id': 'manager_review',
                        'name': 'Manager Review',
                        'description': 'Final review by content manager',
                        'assignee_role': 'manager',
                        'required_permissions': ['content.publish_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 48
                    }
                ],
                'notification_settings': {
                    'notify_on_submit': True,
                    'notify_on_approve': True,
                    'notify_on_reject': True,
                    'notify_on_timeout': True
                },
                'applicable_content_types': ['page', 'blog', 'news', 'landing']
            },
            {
                'name': 'Legal Review',
                'workflow_type': 'legal_review',
                'description': 'Legal review workflow for sensitive content',
                'auto_publish': False,
                'steps': [
                    {
                        'step_id': 'content_review',
                        'name': 'Content Review',
                        'description': 'Initial content review',
                        'assignee_role': 'editor',
                        'required_permissions': ['content.change_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 24
                    },
                    {
                        'step_id': 'legal_review',
                        'name': 'Legal Review',
                        'description': 'Legal compliance review',
                        'assignee_role': 'legal',
                        'required_permissions': ['content.legal_review_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 72
                    },
                    {
                        'step_id': 'final_approval',
                        'name': 'Final Approval',
                        'description': 'Final approval for publication',
                        'assignee_role': 'manager',
                        'required_permissions': ['content.publish_advancedcontentpage'],
                        'auto_approve': False,
                        'timeout_hours': 24
                    }
                ],
                'notification_settings': {
                    'notify_on_submit': True,
                    'notify_on_approve': True,
                    'notify_on_reject': True,
                    'notify_on_timeout': True,
                    'escalate_on_timeout': True
                },
                'applicable_content_types': ['legal']
            }
        ]
        
        for workflow_data in workflows:
            workflow, created = ContentWorkflow.objects.get_or_create(
                name=workflow_data['name'],
                defaults=workflow_data
            )
            if created:
                self.stdout.write(f'Created workflow: {workflow.name}')