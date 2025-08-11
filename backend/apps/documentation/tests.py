from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import (
    DocumentationCategory, DocumentationTemplate, Documentation,
    DocumentationTag, DocumentationVersion, DocumentationComment,
    DocumentationFeedback, DocumentationBookmark
)

User = get_user_model()


class DocumentationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentationCategory.objects.create(
            name='Test Category',
            description='Test category description'
        )

    def test_documentation_creation(self):
        """Test creating a documentation instance"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='This is test content',
            category=self.category,
            author=self.user
        )
        
        self.assertEqual(doc.title, 'Test Document')
        self.assertEqual(doc.status, 'draft')
        self.assertEqual(doc.visibility, 'internal')
        self.assertEqual(doc.version, '1.0')
        self.assertTrue(doc.slug)

    def test_documentation_slug_generation(self):
        """Test automatic slug generation"""
        doc = Documentation.objects.create(
            title='Test Document with Spaces',
            content='Content',
            category=self.category,
            author=self.user
        )
        
        self.assertEqual(doc.slug, 'test-document-with-spaces')

    def test_category_hierarchy(self):
        """Test category parent-child relationships"""
        parent_category = DocumentationCategory.objects.create(
            name='Parent Category'
        )
        child_category = DocumentationCategory.objects.create(
            name='Child Category',
            parent=parent_category
        )
        
        self.assertEqual(child_category.parent, parent_category)
        self.assertIn(child_category, parent_category.children.all())

    def test_documentation_version_creation(self):
        """Test version history creation"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Original content',
            category=self.category,
            author=self.user
        )
        
        version = DocumentationVersion.objects.create(
            documentation=doc,
            version_number='1.1',
            title=doc.title,
            content='Updated content',
            created_by=self.user
        )
        
        self.assertEqual(version.documentation, doc)
        self.assertEqual(version.version_number, '1.1')


class DocumentationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            is_staff=True
        )
        self.category = DocumentationCategory.objects.create(
            name='Test Category'
        )
        self.tag = DocumentationTag.objects.create(
            name='Test Tag'
        )

    def test_documentation_list_authentication_required(self):
        """Test that authentication is required for documentation list"""
        url = reverse('documentation:documentation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_documentation_list_authenticated(self):
        """Test documentation list with authentication"""
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_documentation_create(self):
        """Test creating documentation via API"""
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-list')
        
        data = {
            'title': 'Test API Document',
            'content': 'This is test content',
            'category': self.category.id,
            'tags': [self.tag.id],
            'status': 'draft',
            'visibility': 'internal'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        doc = Documentation.objects.get(title='Test API Document')
        self.assertEqual(doc.author, self.user)
        self.assertEqual(doc.category, self.category)

    def test_documentation_update(self):
        """Test updating documentation via API"""
        doc = Documentation.objects.create(
            title='Original Title',
            content='Original content',
            category=self.category,
            author=self.user
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-detail', kwargs={'pk': doc.id})
        
        data = {
            'title': 'Updated Title',
            'content': 'Updated content',
            'category': self.category.id,
            'status': 'published'
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        doc.refresh_from_db()
        self.assertEqual(doc.title, 'Updated Title')
        self.assertEqual(doc.status, 'published')

    def test_documentation_permissions(self):
        """Test documentation permissions"""
        # Create a private document
        doc = Documentation.objects.create(
            title='Private Document',
            content='Private content',
            category=self.category,
            author=self.user,
            visibility='private'
        )
        
        # Another user should not be able to access it
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        self.client.force_authenticate(user=other_user)
        url = reverse('documentation:documentation-detail', kwargs={'pk': doc.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Author should be able to access it
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_documentation_like(self):
        """Test liking documentation"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Content',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-like', kwargs={'pk': doc.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        doc.refresh_from_db()
        self.assertEqual(doc.like_count, 1)

    def test_documentation_bookmark(self):
        """Test bookmarking documentation"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Content',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-bookmark', kwargs={'pk': doc.id})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check bookmark was created
        bookmark = DocumentationBookmark.objects.filter(
            user=self.user,
            documentation=doc
        ).first()
        self.assertIsNotNone(bookmark)

    def test_documentation_comment(self):
        """Test adding comments to documentation"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Content',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-add-comment', kwargs={'pk': doc.id})
        
        data = {'content': 'This is a test comment'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        comment = DocumentationComment.objects.filter(
            documentation=doc,
            author=self.user
        ).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.content, 'This is a test comment')

    def test_documentation_feedback(self):
        """Test submitting feedback for documentation"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Content',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-submit-feedback', kwargs={'pk': doc.id})
        
        data = {
            'rating': 5,
            'comment': 'Great documentation!',
            'is_helpful': True
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        feedback = DocumentationFeedback.objects.filter(
            documentation=doc,
            user=self.user
        ).first()
        self.assertIsNotNone(feedback)
        self.assertEqual(feedback.rating, 5)

    def test_documentation_search(self):
        """Test documentation search functionality"""
        # Create test documents
        doc1 = Documentation.objects.create(
            title='Python Programming Guide',
            content='Learn Python programming basics',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        doc2 = Documentation.objects.create(
            title='JavaScript Tutorial',
            content='JavaScript fundamentals and advanced concepts',
            category=self.category,
            author=self.user,
            status='published',
            visibility='public'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentation-search')
        
        # Search for Python
        response = self.client.get(url, {'q': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        results = response.json()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Programming Guide')

    def test_category_tree(self):
        """Test category tree endpoint"""
        parent = DocumentationCategory.objects.create(name='Parent')
        child = DocumentationCategory.objects.create(name='Child', parent=parent)
        
        self.client.force_authenticate(user=self.user)
        url = reverse('documentation:documentationcategory-tree')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertEqual(len(data), 2)  # Test category + Parent
        
        # Find parent category in response
        parent_data = next((cat for cat in data if cat['name'] == 'Parent'), None)
        self.assertIsNotNone(parent_data)
        self.assertEqual(len(parent_data['children']), 1)
        self.assertEqual(parent_data['children'][0]['name'], 'Child')


class DocumentationSignalTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = DocumentationCategory.objects.create(
            name='Test Category'
        )

    def test_initial_version_creation(self):
        """Test that initial version is created when document is saved"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Initial content',
            category=self.category,
            author=self.user
        )
        
        # Check that initial version was created
        version = DocumentationVersion.objects.filter(
            documentation=doc,
            version_number='1.0'
        ).first()
        
        self.assertIsNotNone(version)
        self.assertEqual(version.title, doc.title)
        self.assertEqual(version.content, doc.content)
        self.assertEqual(version.created_by, self.user)

    def test_published_date_update(self):
        """Test that published_at is set when status changes to published"""
        doc = Documentation.objects.create(
            title='Test Document',
            content='Content',
            category=self.category,
            author=self.user,
            status='draft'
        )
        
        self.assertIsNone(doc.published_at)
        
        # Change status to published
        doc.status = 'published'
        doc.save()
        
        doc.refresh_from_db()
        self.assertIsNotNone(doc.published_at)