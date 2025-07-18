"""
URL patterns for the search app.
"""
from django.urls import path
from .views import (
    ProductSearchView, 
    SearchSuggestionsView, 
    FilterOptionsView,
    PopularSearchesView,
    RebuildIndexView,
    RelatedProductsView
)

urlpatterns = [
    path('products/', ProductSearchView.as_view(), name='product-search'),
    path('suggestions/', SearchSuggestionsView.as_view(), name='search-suggestions'),
    path('filters/', FilterOptionsView.as_view(), name='filter-options'),
    path('popular/', PopularSearchesView.as_view(), name='popular-searches'),
    path('related/', RelatedProductsView.as_view(), name='related-products'),
    path('rebuild-index/', RebuildIndexView.as_view(), name='rebuild-index'),
]