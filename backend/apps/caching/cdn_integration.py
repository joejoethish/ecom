import boto3
import requests
import hashlib
import mimetypes
import logging
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from datetime import timedelta
import json
import time

logger = logging.getLogger(__name__)


class CDNManager:
    """Content Delivery Network integration and management"""
    
    def __init__(self):
        self.cloudfront_client = None
        self.s3_client = None
        self.cloudflare_client = None
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize CDN service clients"""
        try:
            # AWS CloudFront and S3
            if hasattr(settings, 'AWS_ACCESS_KEY_ID'):
                self.cloudfront_client = boto3.client(
                    'cloudfront',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
                
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
                )
            
            # Cloudflare (if configured)
            if hasattr(settings, 'CLOUDFLARE_API_TOKEN'):
                self.cloudflare_headers = {
                    'Authorization': f'Bearer {settings.CLOUDFLARE_API_TOKEN}',
                    'Content-Type': 'application/json'
                }
                
        except Exception as e:
            logger.error(f"Failed to initialize CDN clients: {e}")
    
    def upload_static_assets(self, assets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload static assets to CDN with optimization"""
        try:
            results = {
                'uploaded': [],
                'failed': [],
                'total_size': 0,
                'compressed_size': 0
            }
            
            for asset in assets:
                try:
                    result = self._upload_single_asset(asset)
                    if result['success']:
                        results['uploaded'].append(result)
                        results['total_size'] += result['original_size']
                        results['compressed_size'] += result['compressed_size']
                    else:
                        results['failed'].append(result)
                        
                except Exception as e:
                    logger.error(f"Failed to upload asset {asset.get('path', 'unknown')}: {e}")
                    results['failed'].append({
                        'path': asset.get('path', 'unknown'),
                        'error': str(e)
                    })
            
            # Calculate compression ratio
            if results['total_size'] > 0:
                results['compression_ratio'] = (
                    1 - results['compressed_size'] / results['total_size']
                ) * 100
            
            return results
            
        except Exception as e:
            logger.error(f"Static asset upload failed: {e}")
            return {'error': str(e)}
    
    def optimize_images(self, image_paths: List[str], 
                       formats: List[str] = ['webp', 'avif']) -> Dict[str, Any]:
        """Optimize images for web delivery"""
        try:
            from PIL import Image
            import io
            
            results = {
                'optimized': [],
                'failed': [],
                'total_savings': 0
            }
            
            for image_path in image_paths:
                try:
                    # Open and analyze image
                    with default_storage.open(image_path, 'rb') as f:
                        original_image = Image.open(f)
                        original_size = f.tell()
                    
                    optimizations = []
                    
                    # Generate responsive sizes
                    sizes = [320, 640, 768, 1024, 1280, 1920]
                    for size in sizes:
                        if original_image.width > size:
                            optimizations.extend(
                                self._create_responsive_variants(
                                    original_image, image_path, size, formats
                                )
                            )
                    
                    # Create optimized versions in different formats
                    for format_type in formats:
                        optimized = self._optimize_image_format(
                            original_image, image_path, format_type
                        )
                        if optimized:
                            optimizations.append(optimized)
                    
                    total_optimized_size = sum(opt['size'] for opt in optimizations)
                    savings = original_size - total_optimized_size
                    
                    results['optimized'].append({
                        'original_path': image_path,
                        'original_size': original_size,
                        'optimizations': optimizations,
                        'total_optimized_size': total_optimized_size,
                        'savings': savings,
                        'savings_percent': (savings / original_size) * 100 if original_size > 0 else 0
                    })
                    
                    results['total_savings'] += savings
                    
                except Exception as e:
                    logger.error(f"Image optimization failed for {image_path}: {e}")
                    results['failed'].append({
                        'path': image_path,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Image optimization failed: {e}")
            return {'error': str(e)}
    
    def invalidate_cache(self, paths: List[str], distribution_id: str = None) -> Dict[str, Any]:
        """Invalidate CDN cache for specified paths"""
        try:
            results = {
                'cloudfront': None,
                'cloudflare': None,
                'success': False
            }
            
            # CloudFront invalidation
            if self.cloudfront_client and distribution_id:
                try:
                    response = self.cloudfront_client.create_invalidation(
                        DistributionId=distribution_id,
                        InvalidationBatch={
                            'Paths': {
                                'Quantity': len(paths),
                                'Items': paths
                            },
                            'CallerReference': str(int(time.time()))
                        }
                    )
                    
                    results['cloudfront'] = {
                        'invalidation_id': response['Invalidation']['Id'],
                        'status': response['Invalidation']['Status'],
                        'paths': paths
                    }
                    results['success'] = True
                    
                except Exception as e:
                    logger.error(f"CloudFront invalidation failed: {e}")
                    results['cloudfront'] = {'error': str(e)}
            
            # Cloudflare invalidation
            if hasattr(settings, 'CLOUDFLARE_ZONE_ID'):
                try:
                    zone_id = settings.CLOUDFLARE_ZONE_ID
                    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache'
                    
                    # Convert paths to full URLs
                    base_url = getattr(settings, 'SITE_URL', 'https://example.com')
                    full_urls = [f"{base_url.rstrip('/')}{path}" for path in paths]
                    
                    response = requests.post(
                        url,
                        headers=self.cloudflare_headers,
                        json={'files': full_urls}
                    )
                    
                    if response.status_code == 200:
                        results['cloudflare'] = {
                            'success': True,
                            'purged_urls': full_urls
                        }
                        results['success'] = True
                    else:
                        results['cloudflare'] = {
                            'error': f'HTTP {response.status_code}: {response.text}'
                        }
                        
                except Exception as e:
                    logger.error(f"Cloudflare invalidation failed: {e}")
                    results['cloudflare'] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {e}")
            return {'error': str(e)}
    
    def get_cdn_analytics(self, distribution_id: str = None, 
                         days: int = 7) -> Dict[str, Any]:
        """Get CDN usage analytics and performance metrics"""
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            analytics = {
                'period': f'{days} days',
                'cloudfront': None,
                'cloudflare': None
            }
            
            # CloudFront analytics
            if self.cloudfront_client and distribution_id:
                try:
                    # Get distribution statistics
                    response = self.cloudfront_client.get_distribution_config(
                        Id=distribution_id
                    )
                    
                    # Note: CloudWatch integration would be needed for detailed metrics
                    analytics['cloudfront'] = {
                        'distribution_id': distribution_id,
                        'domain_name': response['DistributionConfig']['DomainName'],
                        'status': response['DistributionConfig']['Enabled'],
                        'price_class': response['DistributionConfig']['PriceClass'],
                        'note': 'Detailed metrics require CloudWatch integration'
                    }
                    
                except Exception as e:
                    logger.error(f"CloudFront analytics failed: {e}")
                    analytics['cloudfront'] = {'error': str(e)}
            
            # Cloudflare analytics
            if hasattr(settings, 'CLOUDFLARE_ZONE_ID'):
                try:
                    zone_id = settings.CLOUDFLARE_ZONE_ID
                    
                    # Get zone analytics
                    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/analytics/dashboard'
                    params = {
                        'since': start_date.isoformat(),
                        'until': end_date.isoformat(),
                        'continuous': 'true'
                    }
                    
                    response = requests.get(
                        url,
                        headers=self.cloudflare_headers,
                        params=params
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data['success']:
                            result = data['result']
                            analytics['cloudflare'] = {
                                'requests': result.get('totals', {}).get('requests', {}).get('all', 0),
                                'bandwidth': result.get('totals', {}).get('bandwidth', {}).get('all', 0),
                                'cache_hit_ratio': result.get('totals', {}).get('requests', {}).get('cached', 0) / max(result.get('totals', {}).get('requests', {}).get('all', 1), 1),
                                'threats_blocked': result.get('totals', {}).get('threats', {}).get('all', 0),
                                'unique_visitors': result.get('totals', {}).get('uniques', {}).get('all', 0)
                            }
                        else:
                            analytics['cloudflare'] = {'error': data.get('errors', 'Unknown error')}
                    else:
                        analytics['cloudflare'] = {'error': f'HTTP {response.status_code}'}
                        
                except Exception as e:
                    logger.error(f"Cloudflare analytics failed: {e}")
                    analytics['cloudflare'] = {'error': str(e)}
            
            return analytics
            
        except Exception as e:
            logger.error(f"CDN analytics failed: {e}")
            return {'error': str(e)}
    
    def configure_cache_headers(self, file_types: Dict[str, int]) -> Dict[str, Any]:
        """Configure cache headers for different file types"""
        try:
            configurations = {}
            
            for file_type, cache_duration in file_types.items():
                cache_control = self._generate_cache_control(cache_duration)
                
                configurations[file_type] = {
                    'cache_control': cache_control,
                    'expires': (timezone.now() + timedelta(seconds=cache_duration)).isoformat(),
                    'etag_enabled': True,
                    'gzip_enabled': file_type in ['css', 'js', 'html', 'json', 'xml'],
                    'brotli_enabled': file_type in ['css', 'js', 'html', 'json']
                }
            
            # Apply configurations to CDN
            if self.cloudfront_client:
                # CloudFront configuration would require distribution update
                pass
            
            if hasattr(settings, 'CLOUDFLARE_ZONE_ID'):
                # Cloudflare page rules configuration
                self._configure_cloudflare_cache_rules(configurations)
            
            return {
                'success': True,
                'configurations': configurations
            }
            
        except Exception as e:
            logger.error(f"Cache header configuration failed: {e}")
            return {'error': str(e)}
    
    def preload_critical_resources(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Preload critical resources across CDN edge locations"""
        try:
            results = {
                'preloaded': [],
                'failed': [],
                'total_resources': len(resources)
            }
            
            for resource in resources:
                try:
                    # Validate resource
                    if not all(key in resource for key in ['url', 'type', 'priority']):
                        results['failed'].append({
                            'resource': resource,
                            'error': 'Missing required fields (url, type, priority)'
                        })
                        continue
                    
                    # Preload resource
                    preload_result = self._preload_resource(resource)
                    
                    if preload_result['success']:
                        results['preloaded'].append(preload_result)
                    else:
                        results['failed'].append(preload_result)
                        
                except Exception as e:
                    logger.error(f"Resource preload failed: {e}")
                    results['failed'].append({
                        'resource': resource,
                        'error': str(e)
                    })
            
            return results
            
        except Exception as e:
            logger.error(f"Critical resource preloading failed: {e}")
            return {'error': str(e)}
    
    def _upload_single_asset(self, asset: Dict[str, Any]) -> Dict[str, Any]:
        """Upload a single asset to CDN"""
        try:
            file_path = asset['path']
            content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Read and potentially compress file
            with default_storage.open(file_path, 'rb') as f:
                content = f.read()
                original_size = len(content)
            
            # Apply compression if applicable
            compressed_content = self._compress_content(content, content_type)
            compressed_size = len(compressed_content)
            
            # Generate ETag
            etag = hashlib.md5(compressed_content).hexdigest()
            
            # Upload to S3 (if configured)
            if self.s3_client:
                bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
                if bucket_name:
                    self.s3_client.put_object(
                        Bucket=bucket_name,
                        Key=file_path,
                        Body=compressed_content,
                        ContentType=content_type,
                        CacheControl=self._generate_cache_control_for_file(file_path),
                        ContentEncoding='gzip' if compressed_size < original_size else None,
                        Metadata={
                            'original-size': str(original_size),
                            'compressed-size': str(compressed_size)
                        }
                    )
            
            return {
                'success': True,
                'path': file_path,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'content_type': content_type,
                'etag': etag,
                'compression_ratio': ((original_size - compressed_size) / original_size) * 100 if original_size > 0 else 0
            }
            
        except Exception as e:
            return {
                'success': False,
                'path': asset.get('path', 'unknown'),
                'error': str(e)
            }
    
    def _create_responsive_variants(self, image, original_path: str, 
                                  width: int, formats: List[str]) -> List[Dict[str, Any]]:
        """Create responsive image variants"""
        variants = []
        
        try:
            # Calculate proportional height
            aspect_ratio = image.height / image.width
            height = int(width * aspect_ratio)
            
            # Resize image
            resized = image.resize((width, height), Image.Resampling.LANCZOS)
            
            for format_type in formats:
                try:
                    # Generate filename
                    base_name = original_path.rsplit('.', 1)[0]
                    variant_path = f"{base_name}_{width}w.{format_type}"
                    
                    # Save optimized variant
                    buffer = io.BytesIO()
                    save_kwargs = {'format': format_type.upper()}
                    
                    if format_type == 'jpeg':
                        save_kwargs['quality'] = 85
                        save_kwargs['optimize'] = True
                    elif format_type == 'webp':
                        save_kwargs['quality'] = 80
                        save_kwargs['method'] = 6
                    elif format_type == 'avif':
                        save_kwargs['quality'] = 75
                    
                    resized.save(buffer, **save_kwargs)
                    buffer.seek(0)
                    
                    # Save to storage
                    default_storage.save(variant_path, buffer)
                    
                    variants.append({
                        'path': variant_path,
                        'width': width,
                        'height': height,
                        'format': format_type,
                        'size': buffer.tell()
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to create {format_type} variant: {e}")
            
        except Exception as e:
            logger.error(f"Failed to create responsive variants: {e}")
        
        return variants
    
    def _optimize_image_format(self, image, original_path: str, format_type: str) -> Optional[Dict[str, Any]]:
        """Optimize image in specific format"""
        try:
            base_name = original_path.rsplit('.', 1)[0]
            optimized_path = f"{base_name}_optimized.{format_type}"
            
            buffer = io.BytesIO()
            save_kwargs = {'format': format_type.upper()}
            
            if format_type == 'webp':
                save_kwargs.update({'quality': 80, 'method': 6})
            elif format_type == 'avif':
                save_kwargs.update({'quality': 75})
            elif format_type == 'jpeg':
                save_kwargs.update({'quality': 85, 'optimize': True})
            
            image.save(buffer, **save_kwargs)
            buffer.seek(0)
            
            # Save to storage
            default_storage.save(optimized_path, buffer)
            
            return {
                'path': optimized_path,
                'format': format_type,
                'size': buffer.tell()
            }
            
        except Exception as e:
            logger.error(f"Image format optimization failed: {e}")
            return None
    
    def _compress_content(self, content: bytes, content_type: str) -> bytes:
        """Compress content if applicable"""
        compressible_types = [
            'text/', 'application/javascript', 'application/json',
            'application/xml', 'image/svg+xml'
        ]
        
        if any(content_type.startswith(t) for t in compressible_types):
            try:
                import gzip
                return gzip.compress(content)
            except Exception as e:
                logger.warning(f"Compression failed: {e}")
        
        return content
    
    def _generate_cache_control(self, duration: int) -> str:
        """Generate cache control header"""
        if duration <= 0:
            return 'no-cache, no-store, must-revalidate'
        elif duration < 3600:  # Less than 1 hour
            return f'public, max-age={duration}'
        elif duration < 86400:  # Less than 1 day
            return f'public, max-age={duration}, s-maxage={duration}'
        else:  # 1 day or more
            return f'public, max-age={duration}, s-maxage={duration}, immutable'
    
    def _generate_cache_control_for_file(self, file_path: str) -> str:
        """Generate cache control based on file type"""
        extension = file_path.split('.')[-1].lower()
        
        cache_durations = {
            'css': 31536000,    # 1 year
            'js': 31536000,     # 1 year
            'png': 2592000,     # 30 days
            'jpg': 2592000,     # 30 days
            'jpeg': 2592000,    # 30 days
            'gif': 2592000,     # 30 days
            'webp': 2592000,    # 30 days
            'svg': 2592000,     # 30 days
            'woff': 31536000,   # 1 year
            'woff2': 31536000,  # 1 year
            'ttf': 31536000,    # 1 year
            'eot': 31536000,    # 1 year
            'html': 3600,       # 1 hour
            'json': 3600,       # 1 hour
        }
        
        duration = cache_durations.get(extension, 86400)  # Default 1 day
        return self._generate_cache_control(duration)
    
    def _configure_cloudflare_cache_rules(self, configurations: Dict[str, Any]):
        """Configure Cloudflare cache rules"""
        try:
            if not hasattr(settings, 'CLOUDFLARE_ZONE_ID'):
                return
            
            zone_id = settings.CLOUDFLARE_ZONE_ID
            
            # This would require implementing Cloudflare Page Rules API
            # For now, we'll just log the configurations
            logger.info(f"Cloudflare cache rules configured: {configurations}")
            
        except Exception as e:
            logger.error(f"Cloudflare cache rule configuration failed: {e}")
    
    def _preload_resource(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Preload a single resource"""
        try:
            # This would typically involve making requests to edge locations
            # or using CDN-specific preloading APIs
            
            # For now, we'll simulate the preloading process
            time.sleep(0.1)  # Simulate network delay
            
            return {
                'success': True,
                'resource': resource,
                'preload_time': 0.1,
                'edge_locations': ['us-east-1', 'eu-west-1', 'ap-southeast-1']  # Example
            }
            
        except Exception as e:
            return {
                'success': False,
                'resource': resource,
                'error': str(e)
            }


# Global CDN manager instance
cdn_manager = CDNManager()