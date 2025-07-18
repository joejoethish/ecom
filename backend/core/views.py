"""
Core views and mixins for the ecommerce platform.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from .utils import create_response_data
from .exceptions import EcommerceException


class BaseAPIView(APIView):
    """
    Base API view with common functionality.
    """
    
    def handle_exception(self, exc):
        """
        Handle exceptions and return consistent error responses.
        """
        if isinstance(exc, EcommerceException):
            return Response(
                create_response_data(
                    success=False,
                    message=exc.message,
                    errors={'code': exc.code}
                ),
                status=exc.status_code
            )
        
        return super().handle_exception(exc)


class BaseModelViewSet(ModelViewSet):
    """
    Base model viewset with common functionality.
    """
    
    def create(self, request, *args, **kwargs):
        """
        Create a new instance with standardized response.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        return Response(
            create_response_data(
                success=True,
                data=serializer.data,
                message=f"{self.get_serializer_class().Meta.model.__name__} created successfully"
            ),
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """
        Update an instance with standardized response.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            create_response_data(
                success=True,
                data=serializer.data,
                message=f"{self.get_serializer_class().Meta.model.__name__} updated successfully"
            )
        )
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete an instance with standardized response.
        """
        instance = self.get_object()
        instance.delete()
        
        return Response(
            create_response_data(
                success=True,
                message=f"{self.get_serializer_class().Meta.model.__name__} deleted successfully"
            ),
            status=status.HTTP_204_NO_CONTENT
        )
    
    def list(self, request, *args, **kwargs):
        """
        List instances with pagination.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            create_response_data(
                success=True,
                data=serializer.data
            )
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a single instance.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        
        return Response(
            create_response_data(
                success=True,
                data=serializer.data
            )
        )


class HealthCheckView(APIView):
    """
    Simple health check endpoint.
    """
    permission_classes = []
    authentication_classes = []
    
    def get(self, request):
        """
        Return system health status.
        """
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'version': getattr(settings, 'API_VERSION', 'v1')
        })


