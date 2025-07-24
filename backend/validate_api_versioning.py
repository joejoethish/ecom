"""
Validation script for API versioning implementation.

This script tests the API versioning functionality by making requests to both v1 and v2
endpoints and comparing the responses.
"""
import os
import sys
import json
import requests
from urllib.parse import urljoin
from pprint import pprint
from colorama import init, Fore, Style

# Initialize colorama
init()

# Base URL for API
BASE_URL = "http://localhost:8000"


def print_header(text):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}" + "=" * 80)
    print(f" {text}")
    print("=" * 80 + f"{Style.RESET_ALL}\n")


def print_success(text):
    """Print a success message."""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")


def print_error(text):
    """Print an error message."""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")


def print_info(text):
    """Print an info message."""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")


def print_warning(text):
    """Print a warning message."""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")


def print_json(data):
    """Print formatted JSON data."""
    print(f"{Fore.MAGENTA}")
    print(json.dumps(data, indent=2))
    print(f"{Style.RESET_ALL}")


def test_url_path_versioning():
    """Test URL path versioning."""
    print_header("Testing URL Path Versioning")
    
    # Test endpoints in both v1 and v2
    endpoints = [
        "products/",
        "auth/login/",
        "customers/",
    ]
    
    for endpoint in endpoints:
        print_info(f"Testing endpoint: {endpoint}")
        
        # Test v1
        v1_url = urljoin(BASE_URL, f"api/v1/{endpoint}")
        try:
            v1_response = requests.get(v1_url)
            print_success(f"V1 endpoint accessible: {v1_url} - Status: {v1_response.status_code}")
            print_info(f"V1 Headers: X-API-Version: {v1_response.headers.get('X-API-Version', 'Not found')}")
        except Exception as e:
            print_error(f"Error accessing V1 endpoint: {str(e)}")
        
        # Test v2
        v2_url = urljoin(BASE_URL, f"api/v2/{endpoint}")
        try:
            v2_response = requests.get(v2_url)
            print_success(f"V2 endpoint accessible: {v2_url} - Status: {v2_response.status_code}")
            print_info(f"V2 Headers: X-API-Version: {v2_response.headers.get('X-API-Version', 'Not found')}")
        except Exception as e:
            print_error(f"Error accessing V2 endpoint: {str(e)}")
        
        print()


def test_header_versioning():
    """Test header-based versioning."""
    print_header("Testing Header-Based Versioning")
    
    # Test endpoint
    endpoint = "api/v1/products/"
    url = urljoin(BASE_URL, endpoint)
    
    # Test with Accept header versioning
    headers = {
        "Accept": "application/json; version=v2"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.headers.get('X-API-Version') == 'v2':
            print_success(f"Accept header versioning works: {response.headers.get('X-API-Version')}")
        else:
            print_error(f"Accept header versioning failed: {response.headers.get('X-API-Version', 'Not found')}")
    except Exception as e:
        print_error(f"Error testing Accept header versioning: {str(e)}")
    
    # Test with vendor media type
    headers = {
        "Accept": "application/vnd.ecommerce.v2+json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.headers.get('X-API-Version') == 'v2':
            print_success(f"Vendor media type versioning works: {response.headers.get('X-API-Version')}")
        else:
            print_error(f"Vendor media type versioning failed: {response.headers.get('X-API-Version', 'Not found')}")
    except Exception as e:
        print_error(f"Error testing vendor media type versioning: {str(e)}")
    
    # Test with custom header
    headers = {
        "X-API-Version": "v2"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.headers.get('X-API-Version') == 'v2':
            print_success(f"Custom header versioning works: {response.headers.get('X-API-Version')}")
        else:
            print_error(f"Custom header versioning failed: {response.headers.get('X-API-Version', 'Not found')}")
    except Exception as e:
        print_error(f"Error testing custom header versioning: {str(e)}")


def test_version_specific_endpoints():
    """Test version-specific endpoints."""
    print_header("Testing Version-Specific Endpoints")
    
    # Test v2-only endpoints
    v2_only_endpoints = [
        "products/trending/",
        "products/recommendations/",
        "products/bulk-availability/",
    ]
    
    for endpoint in v2_only_endpoints:
        # Test in v2 (should work)
        v2_url = urljoin(BASE_URL, f"api/v2/{endpoint}")
        try:
            v2_response = requests.get(v2_url)
            if v2_response.status_code != 404:
                print_success(f"V2 endpoint accessible: {v2_url} - Status: {v2_response.status_code}")
            else:
                print_error(f"V2 endpoint not found: {v2_url}")
        except Exception as e:
            print_error(f"Error accessing V2 endpoint: {str(e)}")
        
        # Test in v1 (should not work)
        v1_url = urljoin(BASE_URL, f"api/v1/{endpoint}")
        try:
            v1_response = requests.get(v1_url)
            if v1_response.status_code == 404:
                print_success(f"V1 endpoint correctly not found: {v1_url}")
            else:
                print_error(f"V1 endpoint unexpectedly accessible: {v1_url} - Status: {v1_response.status_code}")
        except Exception as e:
            print_error(f"Error testing V1 endpoint: {str(e)}")
        
        print()


def test_response_differences():
    """Test differences in responses between v1 and v2."""
    print_header("Testing Response Differences Between Versions")
    
    # Test product detail endpoint
    endpoint = "products/"
    
    # Get v1 response
    v1_url = urljoin(BASE_URL, f"api/v1/{endpoint}")
    try:
        v1_response = requests.get(v1_url)
        v1_data = v1_response.json()
    except Exception as e:
        print_error(f"Error accessing V1 endpoint: {str(e)}")
        return
    
    # Get v2 response
    v2_url = urljoin(BASE_URL, f"api/v2/{endpoint}")
    try:
        v2_response = requests.get(v2_url)
        v2_data = v2_response.json()
    except Exception as e:
        print_error(f"Error accessing V2 endpoint: {str(e)}")
        return
    
    # Compare responses
    if 'results' in v1_data and 'results' in v2_data and v1_data['results'] and v2_data['results']:
        v1_product = v1_data['results'][0]
        v2_product = v2_data['results'][0]
        
        # Check for v2-specific fields
        v2_specific_fields = []
        for field in v2_product:
            if field not in v1_product:
                v2_specific_fields.append(field)
        
        if v2_specific_fields:
            print_success(f"V2 has additional fields: {', '.join(v2_specific_fields)}")
        else:
            print_warning("No additional fields found in V2 response")
        
        # Print sample of both responses
        print_info("V1 Response Sample:")
        print_json({k: v for k, v in v1_product.items() if k in ['id', 'name', 'price']})
        
        print_info("V2 Response Sample:")
        print_json({k: v for k, v in v2_product.items() if k in ['id', 'name', 'price'] + v2_specific_fields})
    else:
        print_error("Could not compare responses - no results found")


def main():
    """Main function to run all tests."""
    print_header("API Versioning Validation")
    
    # Run tests
    test_url_path_versioning()
    test_header_versioning()
    test_version_specific_endpoints()
    test_response_differences()
    
    print_header("Validation Complete")


if __name__ == "__main__":
    main()