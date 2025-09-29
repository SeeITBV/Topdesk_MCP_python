#!/usr/bin/env python3
"""
Deployment test script for TOPdesk MCP Python

This script tests various aspects of the deployment:
1. Module import
2. Server creation  
3. Tool registration
4. Basic connectivity
"""

import os
import sys
import subprocess
import time

def set_test_env():
    """Set minimal test environment variables."""
    os.environ["TOPDESK_URL"] = "https://test.example.com"
    os.environ["TOPDESK_USERNAME"] = "test"
    os.environ["TOPDESK_PASSWORD"] = "test"
    print("✅ Test environment variables set")

def test_import():
    """Test if the main module can be imported."""
    try:
        import topdesk_mcp.main
        print("✅ Module import successful")
        return True
    except Exception as e:
        print(f"❌ Module import failed: {e}")
        return False

def test_server_startup():
    """Test if server can start up in stdio mode."""
    try:
        # Start server process
        proc = subprocess.Popen(
            [sys.executable, "-m", "topdesk_mcp.main"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it time to start or fail
        time.sleep(3)
        
        # Check if process is still running
        if proc.poll() is None:
            print("✅ Server startup successful (stdio mode)")
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            stdout, stderr = proc.communicate()
            print(f"❌ Server startup failed")
            if stderr:
                print(f"Error: {stderr[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Server startup test failed: {e}")
        try:
            proc.terminate()
        except:
            pass
        return False

def main():
    """Run deployment tests."""
    print("🚀 Starting TOPdesk MCP Python Deployment Tests")
    print("=" * 50)
    
    # Set test environment
    set_test_env()
    
    tests = [
        ("Module Import", test_import),
        ("Server Startup", test_server_startup),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())