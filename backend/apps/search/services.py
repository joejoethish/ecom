"""
Search services for the ecommerce platform.
"""
from elasticsearch_dsl import Q, Search, A
from .documents import ProductDocument
from django.conf import settings
import logging
from elasticsearch.exceptions import ConnectionError, RequestError, TransportError
from typing import Dict, List, Any, Optional, Union, Tuple

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for handling product search and filtering.
    """
    
    @staticmethod
    def search_products(
        query: Optional[str] = None, 
        filters: Optional[Dict[str, Any]] = None, 
        sort_by: Optional[str] = None, 
        page: int = 1, 
        page_size: int = 20,
        highlight: bool = True
    ) -> Dict[str, Any]:
        """
        Search for products with filtering, sorting, and pagination.
        
        Args:
            query: Search query string
            filters: Dictionary of filters to apply
            sort_by: Field to sort by (e.g., 'price', '-created_at')
            page: Page number
            page_size: Number of results per page
            highlight: Whether to highlight matching terms
            
        Returns:
            dict: Search results with pagination info
        """
        try:
            # Start with an empty search
            search = ProductDocument.search()
            
            # Apply text search if query provided
            if query:
                # Use a combined query approach for better relevance
                should_queries = [
                    # Exact match on name with high boost
                    Q('match_phrase', name={"query": query, "boost": 10}),
                    
                    # Multi-match query across multiple fields with different weights
                    Q('multi_match', 
                      query=query,
                      fields=[
                          'name^4',  # Boost name matches
                          'name.ngram^3',  # Ngram analysis for partial matches
                          'name.edge_ngram^2.5',  # Edge ngram for prefix matches
                          'search_keywords^3',  # Combined field for better matching
                          'short_description^2',  # Boost short description
                          'description^1.5',
                          'brand^3',
                          'category.name^2.5',
                          'category.name.ngram^2',
                          'tags^2',
                          'sku^4',  # High boost for SKU matches
                      ],
                      type="best_fields",
                      fuzziness='AUTO',  # Handle typos
                      minimum_should_match="70%"  # Require most terms to match
                    ),
                    
                    # Fuzzy match on name for typo tolerance
                    Q('fuzzy', name={
                        "value": query,
                        "fuzziness": "AUTO",
                        "boost": 1.5
                    }),
                ]
                
                # Combine queries with should (OR) relationship
                search = search.query(Q('bool', should=should_queries))
                
                # Add highlighting if requested
                if highlight:
                    search = search.highlight('name', 
                                             'short_description', 
                                             'description',
                                             fragment_size=150,
                                             number_of_fragments=3,
                                             pre_tags=['<strong>'],
                                             post_tags=['</strong>'])
            else:
                # If no query, match all documents
                search = search.query('match_all')
            
            # Apply filters
            if filters:
                for field, value in filters.items():
                    if field == 'price_range' and isinstance(value, list) and len(value) == 2:
                        # Price range filter - use effective_price for discounted products
                        min_price, max_price = value
                        if min_price is not None:
                            search = search.filter('range', effective_price={'gte': min_price})
                        if max_price is not None:
                            search = search.filter('range', effective_price={'lte': max_price})
                    
                    elif field == 'category' and value:
                        # Category filter (can be a list of category slugs)
                        if isinstance(value, list):
                            search = search.filter('terms', **{'category.slug': value})
                        else:
                            search = search.filter('term', **{'category.slug': value})
                    
                    elif field == 'brand' and value:
                        # Brand filter (can be a list of brands)
                        if isinstance(value, list):
                            search = search.filter('terms', **{'brand.raw': value})
                        else:
                            search = search.filter('term', **{'brand.raw': value})
                    
                    elif field == 'tags' and value:
                        # Tags filter (always a list)
                        if isinstance(value, list):
                            search = search.filter('terms', tags=value)
                        else:
                            search = search.filter('term', tags=value)
                    
                    elif field == 'is_featured' and value is not None:
                        # Featured products filter
                        search = search.filter('term', is_featured=value)
                    
                    elif field == 'discount_only' and value:
                        # Only show products with discount
                        search = search.filter('range', discount_percentage={'gt': 0})
                    
                    elif field == 'min_rating' and value is not None:
                        # Filter by minimum rating
                        search = search.filter('range', average_rating={'gte': value})
                    
                    elif field == 'dimensions' and isinstance(value, dict):
                        # Filter by dimensions
                        for dim_field, dim_value in value.items():
                            if dim_field in ['length', 'width', 'height'] and isinstance(dim_value, list) and len(dim_value) == 2:
                                min_val, max_val = dim_value
                                field_name = f'dimensions_{dim_field}'
                                
                                if min_val is not None:
                                    search = search.filter('range', **{field_name: {'gte': min_val}})
                                if max_val is not None:
                                    search = search.filter('range', **{field_name: {'lte': max_val}})
            
            # Apply sorting
            if sort_by:
                # Handle special sort options
                if sort_by == 'price_asc':
                    search = search.sort('effective_price')
                elif sort_by == 'price_desc':
                    search = search.sort('-effective_price')
                elif sort_by == 'discount':
                    search = search.sort('-discount_percentage')
                elif sort_by == 'relevance' and query:
                    # Already sorted by relevance when query is provided
                    pass
                else:
                    # Handle descending sort (fields prefixed with '-')
                    if sort_by.startswith('-'):
                        search = search.sort({sort_by[1:]: {"order": "desc"}})
                    else:
                        search = search.sort(sort_by)
            else:
                # Default sorting by relevance (if query provided) or newest
                if not query:
                    search = search.sort('-created_at')
            
            # Calculate pagination
            start = (page - 1) * page_size
            end = start + page_size
            
            # Add aggregations for faceted search
            search.aggs.bucket('brands', 'terms', field='brand.raw', size=50)
            search.aggs.bucket('categories', 'terms', field='category.name.raw', size=50)
            search.aggs.bucket('tags', 'terms', field='tags', size=50)
            search.aggs.bucket('price_ranges', 'range', field='effective_price', ranges=[
                {'to': 100},
                {'from': 100, 'to': 500},
                {'from': 500, 'to': 1000},
                {'from': 1000}
            ])
            
            # Execute search
            response = search[start:end].execute()
            
            # Process results
            results = []
            for hit in response:
                result = hit.to_dict()
                
                # Add highlighting if available
                if hasattr(hit, 'meta') and hasattr(hit.meta, 'highlight'):
                    result['highlight'] = {}
                    for field, fragments in hit.meta.highlight.to_dict().items():
                        result['highlight'][field] = fragments
                
                results.append(result)
            
            # Process aggregations for faceted search
            facets = {}
            if hasattr(response, 'aggregations'):
                aggs = response.aggregations
                
                # Extract brands
                if hasattr(aggs, 'brands'):
                    facets['brands'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.brands.buckets
                    ]
                
                # Extract categories
                if hasattr(aggs, 'categories'):
                    facets['categories'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.categories.buckets
                    ]
                
                # Extract tags
                if hasattr(aggs, 'tags'):
                    facets['tags'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.tags.buckets
                    ]
                
                # Extract price ranges
                if hasattr(aggs, 'price_ranges'):
                    facets['price_ranges'] = [
                        {
                            'from': bucket.get('from'),
                            'to': bucket.get('to'),
                            'count': bucket.doc_count
                        }
                        for bucket in aggs.price_ranges.buckets
                    ]
            
            # Prepare final response
            search_results = {
                'count': response.hits.total.value,
                'results': results,
                'page': page,
                'page_size': page_size,
                'num_pages': (response.hits.total.value + page_size - 1) // page_size,
                'facets': facets,
                'query': query,
                'filters': filters,
                'sort_by': sort_by,
            }
            
            return search_results
            
        except (ConnectionError, RequestError, TransportError) as e:
            logger.error(f"Elasticsearch error: {str(e)}")
            # Return empty results on error
            return {
                'count': 0,
                'results': [],
                'page': page,
                'page_size': page_size,
                'num_pages': 0,
                'facets': {},
                'query': query,
                'filters': filters,
                'sort_by': sort_by,
                'error': 'Search service temporarily unavailable'
            }
    
    @staticmethod
    def get_suggestions(
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get autocomplete suggestions for search with context-aware filtering.
        
        Args:
            query: Partial query to get suggestions for
            context: Optional context filters (e.g., category)
            limit: Maximum number of suggestions to return
            
        Returns:
            dict: Dictionary with suggestions and metadata
        """
        if not query or len(query) < 2:
            return {'suggestions': [], 'products': []}
        
        try:
            # Use completion suggester for fast autocomplete
            suggest = {
                'name_suggest': {
                    'prefix': query,
                    'completion': {
                        'field': 'name_suggest',
                        'size': limit,
                        'fuzzy': {
                            'fuzziness': 'AUTO',
                            'min_length': 3
                        }
                    }
                }
            }
            
            # Create search for suggestions
            search = ProductDocument.search()
            search = search.suggest(**suggest)
            
            # Add context filters if provided
            if context:
                for field, value in context.items():
                    if field == 'category' and value:
                        search = search.filter('term', **{'category.slug': value})
                    elif field == 'brand' and value:
                        search = search.filter('term', **{'brand.raw': value})
            
            # Execute suggestion search
            suggest_response = search.execute()
            
            # Extract suggestions
            suggestions = []
            if hasattr(suggest_response, 'suggest') and 'name_suggest' in suggest_response.suggest:
                for suggestion_result in suggest_response.suggest.name_suggest:
                    for option in suggestion_result.options:
                        if option.text not in suggestions:
                            suggestions.append(option.text)
            
            # Also get top matching products for rich autocomplete
            product_search = ProductDocument.search()
            product_search = product_search.query(
                Q('multi_match',
                  query=query,
                  fields=['name^3', 'name.edge_ngram^2', 'brand^2', 'sku^3'],
                  type="best_fields",
                  fuzziness='AUTO'
                )
            )
            
            # Add context filters if provided
            if context:
                for field, value in context.items():
                    if field == 'category' and value:
                        product_search = product_search.filter('term', **{'category.slug': value})
                    elif field == 'brand' and value:
                        product_search = product_search.filter('term', **{'brand.raw': value})
            
            # Get top 3 products
            product_search = product_search[:3]
            product_response = product_search.execute()
            
            # Extract product suggestions
            products = []
            for hit in product_response:
                products.append({
                    'id': hit.id,
                    'name': hit.name,
                    'slug': hit.slug,
                    'price': hit.price,
                    'image': hit.primary_image_url,
                    'category': hit.category.name if hasattr(hit, 'category') and hit.category else None
                })
            
            return {
                'suggestions': suggestions,
                'products': products,
                'query': query
            }
            
        except (ConnectionError, RequestError, TransportError) as e:
            logger.error(f"Elasticsearch suggestion error: {str(e)}")
            return {'suggestions': [], 'products': [], 'query': query, 'error': 'Suggestion service temporarily unavailable'}
    
    @staticmethod
    def get_popular_searches(limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get popular search terms.
        
        Args:
            limit: Maximum number of popular searches to return
            
        Returns:
            list: List of popular search terms with metadata
        """
        # This would typically be implemented with a separate analytics system
        # For now, return a static list of popular searches as an example
        popular_searches = [
            {'term': 'smartphone', 'count': 1245},
            {'term': 'laptop', 'count': 987},
            {'term': 'headphones', 'count': 876},
            {'term': 'camera', 'count': 654},
            {'term': 'smartwatch', 'count': 543},
            {'term': 'gaming console', 'count': 432},
            {'term': 'bluetooth speaker', 'count': 321},
            {'term': 'tablet', 'count': 210},
        ]
        
        return popular_searches[:limit]
    
    @staticmethod
    def get_filter_options() -> Dict[str, List[Dict[str, Any]]]:
        """
        Get available filter options for the search interface.
        
        Returns:
            dict: Dictionary of filter options
        """
        try:
            # Create aggregation search
            search = ProductDocument.search()
            
            # Add aggregations for all filter options
            search.aggs.bucket('brands', 'terms', field='brand.raw', size=100)
            search.aggs.bucket('categories', 'terms', field='category.name.raw', size=100)
            search.aggs.bucket('tags', 'terms', field='tags', size=100)
            
            # Price range aggregation
            search.aggs.bucket('price_ranges', 'range', field='effective_price', ranges=[
                {'to': 100},
                {'from': 100, 'to': 500},
                {'from': 500, 'to': 1000},
                {'from': 1000, 'to': 5000},
                {'from': 5000}
            ])
            
            # Discount aggregation
            search.aggs.bucket('discount_ranges', 'range', field='discount_percentage', ranges=[
                {'from': 5, 'to': 20},
                {'from': 20, 'to': 50},
                {'from': 50}
            ])
            
            # Execute with size 0 to only get aggregations
            search = search[:0]
            response = search.execute()
            
            # Extract aggregation results
            filter_options = {}
            
            if hasattr(response, 'aggregations'):
                aggs = response.aggregations
                
                # Extract brands
                if hasattr(aggs, 'brands'):
                    filter_options['brands'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.brands.buckets
                    ]
                
                # Extract categories
                if hasattr(aggs, 'categories'):
                    filter_options['categories'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.categories.buckets
                    ]
                
                # Extract tags
                if hasattr(aggs, 'tags'):
                    filter_options['tags'] = [
                        {'name': bucket.key, 'count': bucket.doc_count}
                        for bucket in aggs.tags.buckets
                    ]
                
                # Extract price ranges
                if hasattr(aggs, 'price_ranges'):
                    filter_options['price_ranges'] = [
                        {
                            'from': bucket.get('from'),
                            'to': bucket.get('to'),
                            'count': bucket.doc_count,
                            'label': SearchService._format_price_range(bucket.get('from'), bucket.get('to'))
                        }
                        for bucket in aggs.price_ranges.buckets
                    ]
                
                # Extract discount ranges
                if hasattr(aggs, 'discount_ranges'):
                    filter_options['discount_ranges'] = [
                        {
                            'from': bucket.get('from'),
                            'to': bucket.get('to'),
                            'count': bucket.doc_count,
                            'label': SearchService._format_discount_range(bucket.get('from'), bucket.get('to'))
                        }
                        for bucket in aggs.discount_ranges.buckets
                    ]
            
            return filter_options
            
        except (ConnectionError, RequestError, TransportError) as e:
            logger.error(f"Elasticsearch filter options error: {str(e)}")
            return {}
    
    @staticmethod
    def _format_price_range(from_price, to_price):
        """Format price range for display."""
        if from_price is None and to_price is not None:
            return f"Under ${to_price}"
        elif from_price is not None and to_price is None:
            return f"${from_price}+"
        else:
            return f"${from_price} - ${to_price}"
    
    @staticmethod
    def _format_discount_range(from_discount, to_discount):
        """Format discount range for display."""
        if from_discount is None and to_discount is not None:
            return f"Up to {to_discount}% off"
        elif from_discount is not None and to_discount is None:
            return f"{from_discount}%+ off"
        else:
            return f"{from_discount}% - {to_discount}% off"
    
    @staticmethod
    def rebuild_index():
        """
        Rebuild the Elasticsearch index for products.
        """
        try:
            ProductDocument._index.delete(ignore=404)
            ProductDocument.init()
            
            # This will trigger indexing of all products
            from django_elasticsearch_dsl.management.commands.search_index import Command
            cmd = Command()
            cmd.handle(action='rebuild', models=['products.Product'], force=True)
            
            return {'status': 'success', 'message': 'Product index rebuilt successfully'}
        except Exception as e:
            logger.error(f"Error rebuilding index: {str(e)}")
            return {'status': 'error', 'message': f'Error rebuilding index: {str(e)}'}
    
    @staticmethod
    def get_related_products(product_id, limit=6):
        """
        Get related products based on category, tags, and other attributes.
        
        Args:
            product_id: ID of the product to find related items for
            limit: Maximum number of related products to return
            
        Returns:
            list: List of related products
        """
        try:
            # First get the product
            product_search = ProductDocument.search().filter('term', id=product_id)
            product_response = product_search.execute()
            
            if not product_response.hits or len(product_response.hits) == 0:
                return []
            
            product = product_response.hits[0]
            
            # Build a query for related products
            related_search = ProductDocument.search()
            
            # Must not be the same product
            related_search = related_search.filter('bool', must_not=[Q('term', id=product_id)])
            
            # Should match category
            should_queries = []
            if hasattr(product, 'category') and product.category:
                should_queries.append(Q('term', **{'category.id': product.category.id}))
            
            # Should match some tags
            if hasattr(product, 'tags') and product.tags:
                should_queries.append(Q('terms', tags=product.tags))
            
            # Should match brand
            if hasattr(product, 'brand') and product.brand:
                should_queries.append(Q('term', **{'brand.raw': product.brand}))
            
            # Add the should queries with minimum_should_match=1
            if should_queries:
                related_search = related_search.query('bool', should=should_queries, minimum_should_match=1)
            
            # Sort by relevance and limit results
            related_search = related_search[:limit]
            related_response = related_search.execute()
            
            # Extract related products
            related_products = []
            for hit in related_response:
                related_products.append(hit.to_dict())
            
            return related_products
            
        except Exception as e:
            logger.error(f"Error getting related products: {str(e)}")
            return []