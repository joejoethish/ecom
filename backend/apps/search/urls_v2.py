"""
Search URL patterns for API v2.
"""
from django.urls import path
from . import views

# For now, v2 uses the same views as v1
urlpatterns = [
    path('', views.SearchView.as_view(), name='search_v2'),
    path('suggestions/', views.SearchSuggestionsView.as_view(), name='search_suggestions_v2'),
    path('autocomplete/', views.AutocompleteView.as_view(), name='autocomplete_v2'),
]