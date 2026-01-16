#!/usr/bin/env python3
"""
Storage Health Test Script
Tests Backblaze B2 S3 storage integration for the Meesho Image Optimizer API.

Usage:
    python test_storage.py [BASE_URL]

Examples:
    python test_storage.py                                    # Uses default localhost
    python test_storage.py https://meeship-app.yourdomain.com # Tests production
"""

import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path


def run_curl(url, method="GET", data=None, files=None, headers=None):
    """Execute curl command and return response."""
    cmd = ["curl", "-X", method, "-s", "-w", "\\n%{http_code}"]
    
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    
    if files:
        for key, filepath in files.items():
            cmd.extend(["-F", f"{key}=@{filepath}"])
    
    if data:
        cmd.extend(["-d", data])
    
    cmd.append(url)
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse response and status code
    output_lines = result.stdout.strip().split('\n')
    status_code = output_lines[-1] if output_lines else "000"
    response_body = '\n'.join(output_lines[:-1]) if len(output_lines) > 1 else ""
    
    return status_code, response_body


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_storage_health(base_url):
    """Test 1: Storage health check endpoint."""
    print_section("Test 1: Storage Health Check")
    
    url = f"{base_url}/storage-health"
    print(f"GET {url}")
    
    status, response = run_curl(url)
    
    print(f"\nStatus Code: {status}")
    print(f"Response:\n{response}")
    
    if status == "200":
        try:
            data = json.loads(response)
            if data.get("status") == "healthy":
                print("\n✓ Storage health check PASSED")
                return True, data
            else:
                print(f"\n✗ Storage health check FAILED: {data.get('message', 'Unknown error')}")
                return False, data
        except json.JSONDecodeError:
            print("\n✗ Invalid JSON response")
            return False, None
    else:
        print(f"\n✗ Storage health check FAILED with status {status}")
        return False, None


def test_image_upload(base_url):
    """Test 2: Upload test image."""
    print_section("Test 2: Image Upload")
    
    # Create a test image file if it doesn't exist
    test_file = Path("test_image.jpg")
    if not test_file.exists():
        print("Creating test image file...")
        # Create a simple 1x1 pixel JPEG (minimal valid JPEG)
        jpeg_bytes = bytes([
            0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01,
            0x01, 0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
            0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08, 0x07, 0x07, 0x07, 0x09,
            0x09, 0x08, 0x0A, 0x0C, 0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
            0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D, 0x1A, 0x1C, 0x1C, 0x20,
            0x24, 0x2E, 0x27, 0x20, 0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
            0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27, 0x39, 0x3D, 0x38, 0x32,
            0x3C, 0x2E, 0x33, 0x34, 0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
            0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4, 0x00, 0x14, 0x00, 0x01,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x03, 0xFF, 0xC4, 0x00, 0x14, 0x10, 0x01, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0xFF, 0xDA, 0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
            0x37, 0xFF, 0xD9
        ])
        test_file.write_bytes(jpeg_bytes)
        print(f"✓ Created {test_file}")
    
    url = f"{base_url}/api/images/optimize"
    print(f"POST {url}")
    print(f"File: {test_file}")
    
    # Note: This requires authentication, so it might fail
    # In production, you'd need to pass auth headers
    status, response = run_curl(url, method="POST", files={"file": str(test_file)})
    
    print(f"\nStatus Code: {status}")
    print(f"Response:\n{response}")
    
    if status == "200":
        print("\n✓ Image upload PASSED")
        try:
            return True, json.loads(response)
        except json.JSONDecodeError:
            return True, None
    else:
        print(f"\n✗ Image upload returned status {status}")
        print("Note: This might be expected if authentication is required")
        return False, None


def test_signed_url(base_url, object_key=None):
    """Test 3: Generate presigned URL."""
    print_section("Test 3: Presigned URL Generation")
    
    if not object_key:
        object_key = "health_check_test.txt"
        print(f"Using default object key: {object_key}")
    
    url = f"{base_url}/api/images/signed-url/{object_key}"
    print(f"GET {url}")
    
    status, response = run_curl(url)
    
    print(f"\nStatus Code: {status}")
    print(f"Response:\n{response}")
    
    if status == "200":
        try:
            data = json.loads(response)
            signed_url = data.get("signed_url")
            if signed_url:
                print("\n✓ Presigned URL generation PASSED")
                print(f"Signed URL: {signed_url[:80]}...")
                print(f"Expires at: {data.get('expires_at')}")
                return True, signed_url
            else:
                print("\n✗ No signed_url in response")
                return False, None
        except json.JSONDecodeError:
            print("\n✗ Invalid JSON response")
            return False, None
    else:
        print(f"\n✗ Presigned URL generation FAILED with status {status}")
        return False, None


def test_signed_url_access(signed_url):
    """Test 4: Access file via presigned URL."""
    print_section("Test 4: Access File via Presigned URL")
    
    print(f"GET {signed_url[:80]}...")
    
    status, response = run_curl(signed_url)
    
    print(f"\nStatus Code: {status}")
    
    if status == "200":
        print(f"Response length: {len(response)} bytes")
        print(f"Response preview: {response[:200]}")
        print("\n✓ Signed URL access PASSED")
        return True
    else:
        print(f"\n✗ Signed URL access FAILED with status {status}")
        return False


def main():
    """Run all storage tests."""
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    print("\n" + "=" * 60)
    print("  Meesho Image Optimizer - Storage Integration Tests")
    print("=" * 60)
    print(f"Base URL: {base_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    # Test 1: Storage health check
    success, health_data = test_storage_health(base_url)
    results["tests"].append(("Storage Health", success))
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: Generate presigned URL (using health check object if available)
    object_key = None
    if health_data and "test_object_key" in health_data:
        object_key = health_data["test_object_key"]
    
    success, signed_url = test_signed_url(base_url, object_key)
    results["tests"].append(("Presigned URL Generation", success))
    if success:
        results["passed"] += 1
        
        # Test 4: Access via presigned URL
        success = test_signed_url_access(signed_url)
        results["tests"].append(("Presigned URL Access", success))
        if success:
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        results["failed"] += 1
    
    # Print summary
    print_section("Test Summary")
    for test_name, passed in results["tests"]:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {results['passed']} passed, {results['failed']} failed")
    
    if results["failed"] == 0:
        print("\n✓ All tests PASSED! Storage integration is working correctly.")
        return 0
    else:
        print(f"\n✗ {results['failed']} test(s) FAILED. Please check the logs above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
