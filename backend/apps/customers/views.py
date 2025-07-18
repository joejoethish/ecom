"""
Customer views for the ecommerce platform.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class CustomerProfileView(APIView):
    """
    View for customer profile management.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'message': 'Customer profile endpoint',
            'success': True
        })


class AddressListView(APIView):
    """
    View for customer addresses.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'message': 'Customer addresses endpoint',
            'success': True
        })