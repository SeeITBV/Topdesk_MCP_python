"""Tests for FIQL query building utilities."""

import pytest
from datetime import datetime, timedelta
from app.fiql import (
    quote_value, and_join, or_join, equals, not_equals, starts_with,
    greater_equal, in_list, build_person_query, build_operator_query,
    build_incident_query, validate_fiql, sanitize_fiql, days_ago
)


class TestQuoteValue:
    """Test FIQL value quoting and escaping."""
    
    def test_simple_string(self):
        assert quote_value("test") == "'test'"
    
    def test_empty_string(self):
        assert quote_value("") == "''"
    
    def test_string_with_quotes(self):
        assert quote_value("test'value") == "'test\\'value'"
    
    def test_string_with_backslash(self):
        assert quote_value("test\\value") == "'test\\\\value'"
    
    def test_complex_escaping(self):
        assert quote_value("test'\\value") == "'test\\'\\\\value'"


class TestQueryJoining:
    """Test FIQL query joining functions."""
    
    def test_and_join_simple(self):
        result = and_join("field1==value1", "field2==value2")
        assert result == "field1==value1;field2==value2"
    
    def test_and_join_with_empty(self):
        result = and_join("field1==value1", "", "field2==value2")
        assert result == "field1==value1;field2==value2"
    
    def test_or_join_simple(self):
        result = or_join("field1==value1", "field2==value2")
        assert result == "field1==value1,field2==value2"
    
    def test_or_join_with_empty(self):
        result = or_join("field1==value1", "", "field2==value2")
        assert result == "field1==value1,field2==value2"


class TestFIQLOperators:
    """Test individual FIQL operators."""
    
    def test_equals(self):
        assert equals("field", "value") == "field=='value'"
    
    def test_not_equals(self):
        assert not_equals("field", "value") == "field!='value'"
    
    def test_starts_with(self):
        assert starts_with("field", "value") == "field=sw='value'"
    
    def test_greater_equal_string(self):
        assert greater_equal("field", "2023-01-01") == "field=ge=2023-01-01"
    
    def test_greater_equal_datetime(self):
        dt = datetime(2023, 1, 1, 12, 0, 0)
        result = greater_equal("field", dt)
        assert "field=ge=" in result
        assert "2023-01-01T12:00:00Z" in result
    
    def test_in_list(self):
        values = ["High", "Critical"]
        result = in_list("priority.name", values)
        assert result == "priority.name=in=('High','Critical')"
    
    def test_in_list_empty(self):
        assert in_list("field", []) == ""


class TestQueryBuilding:
    """Test complete query building functions."""
    
    def test_build_person_query_full_name(self):
        result = build_person_query(first_name="John", last_name="Doe")
        assert "firstName=='John'" in result
        assert "surname=='Doe'" in result
        assert ";" in result
    
    def test_build_person_query_partial(self):
        result = build_person_query(last_name="Doe")
        assert result == "surname=='Doe'"
    
    def test_build_person_query_with_email(self):
        result = build_person_query(email="john@example.com")
        assert result == "email=='john@example.com'"
    
    def test_build_operator_query_exact(self):
        result = build_operator_query("Jane Smith", exact=True)
        assert result == "name=='Jane Smith'"
    
    def test_build_operator_query_starts_with(self):
        result = build_operator_query("Jane", exact=False)
        assert result == "name=sw='Jane'"
    
    def test_build_incident_query_simple(self):
        result = build_incident_query(caller_id="123-456-789")
        assert "caller.id=='123-456-789'" in result
    
    def test_build_incident_query_complex(self):
        result = build_incident_query(
            caller_id="123-456-789",
            status_exclude=["Closed"],
            priority_levels=["High", "Critical"],
            days_back=30
        )
        
        assert "caller.id=='123-456-789'" in result
        assert "status!='Closed'" in result
        assert "priority.name=in=('High','Critical')" in result
        assert "creationDate=ge=" in result
    
    def test_build_incident_query_category(self):
        result = build_incident_query(
            category="Change",
            days_back=60
        )
        
        assert "category.name=='Change'" in result
        assert "creationDate=ge=" in result


class TestValidation:
    """Test FIQL validation functions."""
    
    def test_validate_fiql_valid(self):
        assert validate_fiql("field=='value'") is True
        assert validate_fiql("field1=='value1';field2=ge=2023-01-01") is True
    
    def test_validate_fiql_invalid(self):
        assert validate_fiql("") is False
        assert validate_fiql("field='value") is False  # Unbalanced quotes
        assert validate_fiql("field(value") is False  # Unbalanced parens
        assert validate_fiql("field value") is False  # No operator
    
    def test_sanitize_fiql(self):
        dangerous = "field=='value'<script>alert('hack')</script>"
        result = sanitize_fiql(dangerous)
        assert "<script>" not in result
        assert "field=='value'" in result
    
    def test_sanitize_fiql_sql_injection(self):
        dangerous = "field=='value' DROP TABLE users"
        result = sanitize_fiql(dangerous)
        assert "DROP" not in result


class TestDateHandling:
    """Test date handling functions."""
    
    def test_days_ago(self):
        result = days_ago(7)
        # Should be ISO format
        assert "T" in result
        assert "Z" in result
        # Should be approximately 7 days ago
        expected_date = (datetime.utcnow() - timedelta(days=7)).date()
        assert expected_date.strftime("%Y-%m-%d") in result