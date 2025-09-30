"""Test encoding issues with Dutch/French queries."""

import urllib.parse
from app.fiql import quote_value, build_incident_query, sanitize_fiql
from topdesk_mcp._utils import utils


def test_quote_value_with_unicode():
    """Test that quote_value properly handles Unicode characters."""
    test_cases = [
        ("café", "'café'"),  # French accent
        ("émails", "'émails'"),  # French accent 
        ("François", "'François'"),  # French cedilla
        ("naïef", "'naïef'"),  # Diaeresis
        ("Müller", "'Müller'"),  # German umlaut
        ("résumé", "'résumé'"),  # Multiple accents
        ("test's value", "'test\\'s value'"),  # Quote escaping with ASCII
        ("test's café", "'test\\'s café'"),  # Quote escaping with Unicode
    ]
    
    print("Testing quote_value with Unicode characters:")
    for input_val, expected in test_cases:
        result = quote_value(input_val)
        print(f"  '{input_val}' -> '{result}' (expected: '{expected}')")
        assert result == expected, f"Failed for '{input_val}': got '{result}', expected '{expected}'"
    print("✓ All quote_value tests passed")

def test_url_encoding_with_unicode():
    """Test that URL encoding properly handles Unicode characters."""
    test_queries = [
        "incidents about café",
        "tickets van sérieux", 
        "problemen met émails",
        "storingen bij François",
        "wijzigingen voor Müller",
        "beveiligingsincident naïef"
    ]
    
    print("\nTesting URL encoding with Unicode characters:")
    for query in test_queries:
        # Test that urllib.parse.quote_plus properly encodes
        encoded = urllib.parse.quote_plus(query)
        print(f"  '{query}' -> '{encoded}'")
        
        # Should not contain raw Unicode bytes
        try:
            encoded.encode('ascii')
        except UnicodeEncodeError:
            raise AssertionError(f"Query '{query}' was not properly encoded")
        
        # Test that it can be decoded back
        decoded = urllib.parse.unquote_plus(encoded)
        assert decoded == query, f"Round-trip failed for '{query}': got '{decoded}'"
    print("✓ All URL encoding tests passed")

def test_fiql_building_with_unicode():
    """Test FIQL query building with Unicode characters."""
    print("\nTesting FIQL building with Unicode characters:")
    
    # This should not raise an error
    query = build_incident_query(
        title_starts="problème avec café",
        operator_name="François Müller", 
        days_back=7
    )
    
    print(f"  Built query: {query}")
    
    # Query should contain the Unicode characters
    assert "problème avec café" in query
    assert "François Müller" in query
    print("✓ FIQL building test passed")

def test_sanitize_fiql_preserves_unicode():
    """Test that FIQL sanitization preserves Unicode characters."""
    print("\nTesting FIQL sanitization with Unicode characters:")
    
    test_query = "caller.name=='François' AND briefDescription=sw='problème avec café'"
    result = sanitize_fiql(test_query)
    
    print(f"  Original: {test_query}")
    print(f"  Sanitized: {result}")
    
    # Should preserve Unicode characters
    assert "François" in result
    assert "problème avec café" in result
    print("✓ FIQL sanitization test passed")

def test_utils_request_encoding():
    """Test that utils.request_topdesk properly encodes Unicode in query parameters."""
    print("\nTesting utils request encoding with Unicode characters:")
    
    # Create a utils instance (without real credentials)
    utils_instance = utils("https://test.topdesk.net", "fake_creds")
    
    # Test query with Unicode characters
    unicode_query = "caller.name=='François' AND briefDescription=sw='café'"
    
    # This would normally make a real HTTP request, but we can inspect the URL building
    # We'll mock the actual request to focus on URL encoding
    import unittest.mock
    
    with unittest.mock.patch('requests.get') as mock_get:
        mock_response = unittest.mock.Mock()
        mock_response.status_code = 200
        mock_response.text = '[]'
        mock_response.json.return_value = []
        mock_get.return_value = mock_response
        
        # Make the request
        utils_instance.request_topdesk("/tas/api/incidents/", query=unicode_query)
        
        # Check that the URL was properly encoded
        called_url = mock_get.call_args[0][0]
        print(f"  Generated URL: {called_url}")
        
        # URL should be properly encoded (no raw Unicode)
        if "François" in called_url:
            print("  ❌ Raw Unicode found in URL - this is the issue!")
            return False
        if "café" in called_url:
            print("  ❌ Raw Unicode found in URL - this is the issue!")
            return False
        
        print("✓ Utils request encoding test passed")
        return True


if __name__ == "__main__":
    try:
        test_quote_value_with_unicode()
        test_url_encoding_with_unicode()
        test_fiql_building_with_unicode()
        test_sanitize_fiql_preserves_unicode()
        passed = test_utils_request_encoding()
        
        if passed:
            print("\n🎉 All tests passed!")
        else:
            print("\n❌ Some tests failed - encoding issue confirmed")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()