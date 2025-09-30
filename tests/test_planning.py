"""Tests for natural language query planning."""

import pytest
from app.planning import QueryPlanner
from app.schemas import QueryPlan


class TestQueryPlanner:
    """Test the QueryPlanner class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.planner = QueryPlanner()
    
    def test_person_query_full_name(self):
        """Test planning for person query with full name."""
        plan = self.planner.plan_query("tickets for John Doe", max_results=5)
        
        assert plan.intent == "Find incidents for person: john doe"
        assert len(plan.steps) == 2
        assert len(plan.tool_calls) == 2
        
        # First step should be person lookup
        assert plan.steps[0].tool_name == "topdesk_get_person_by_query"
        assert plan.tool_calls[0].name == "topdesk_get_person_by_query"
        
        # Second step should be incident lookup
        assert plan.steps[1].tool_name == "topdesk_get_incidents_by_fiql_query"
        assert plan.tool_calls[1].name == "topdesk_get_incidents_by_fiql_query"
        assert "PLACEHOLDER" in plan.tool_calls[1].payload["query"]
    
    def test_person_query_single_name(self):
        """Test planning for person query with single name."""
        plan = self.planner.plan_query("Sander's tickets", max_results=5)
        
        assert plan.intent == "Find incidents for person: sander"
        assert len(plan.steps) == 2
        assert len(plan.warnings) >= 1
        assert "Single name" in plan.warnings[0]
    
    def test_operator_query(self):
        """Test planning for operator query."""
        plan = self.planner.plan_query("incidents assigned to Jane Smith", max_results=5)
        
        assert plan.intent == "Find incidents assigned to operator: jane smith"
        assert len(plan.steps) == 2
        assert plan.steps[0].tool_name == "topdesk_get_operators_by_fiql_query"
        assert plan.steps[1].tool_name == "topdesk_get_incidents_by_fiql_query"
    
    def test_complete_incident_query(self):
        """Test planning for complete incident overview."""
        plan = self.planner.plan_query("show complete details for incident I-240101-001")
        
        assert plan.intent == "Get complete details for incident I-240101-001"
        assert len(plan.steps) == 1
        assert plan.tool_calls[0].name == "topdesk_get_complete_incident_overview"
        assert plan.tool_calls[0].payload["incident_id"] == "I-240101-001"
    
    def test_invalid_incident_id(self):
        """Test planning with invalid incident ID."""
        plan = self.planner.plan_query("show complete details for incident INVALID")
        
        assert plan.clarify is not None
        assert "Invalid incident number format" in plan.clarify
        assert len(plan.tool_calls) == 0
    
    def test_category_query_changes(self):
        """Test planning for change/RFC queries."""
        plan = self.planner.plan_query("show me recent changes", max_results=5)
        
        assert plan.intent == "Find Change incidents"
        assert len(plan.steps) == 1
        assert plan.tool_calls[0].name == "topdesk_get_incidents_by_fiql_query"
        assert "category.name=='Change'" in plan.tool_calls[0].payload["query"]
    
    def test_status_filter_open(self):
        """Test planning with open status filter."""
        plan = self.planner.plan_query("open tickets for John Doe")
        
        assert "status!=Closed" in plan.tool_calls[1].payload["query"]
    
    def test_priority_filter(self):
        """Test planning with priority filter."""
        plan = self.planner.plan_query("high priority incidents last week")
        
        # Should use FIQL query with priority filter
        fiql_query = plan.tool_calls[0].payload["query"]
        assert "priority.name=in=('High')" in fiql_query or "High" in fiql_query
    
    def test_time_constraint_extraction(self):
        """Test extraction of time constraints."""
        # Test "last 7 days"
        assert self.planner._extract_time_constraint("tickets from last 7 days") == 7
        
        # Test "this week"  
        assert self.planner._extract_time_constraint("incidents this week") == 7
        
        # Test "yesterday"
        assert self.planner._extract_time_constraint("tickets from yesterday") == 2
        
        # Test "3 weeks ago"
        assert self.planner._extract_time_constraint("incidents 3 weeks ago") == 21
    
    def test_search_query(self):
        """Test planning for simple search queries."""
        plan = self.planner.plan_query("email problem", max_results=5)
        
        assert plan.intent == "Search for: email problem"
        assert len(plan.steps) == 1
        assert plan.tool_calls[0].name == "search"
        assert plan.tool_calls[0].payload["query"] == "email problem"
    
    def test_clarification_needed(self):
        """Test planning when clarification is needed."""
        plan = self.planner.plan_query("tickets for Sander")
        
        assert plan.clarify is not None
        assert len(plan.tool_calls) == 0
        assert "ambiguous" in plan.clarify.lower() or "specify" in plan.clarify.lower()
    
    def test_fiql_query_complex(self):
        """Test planning for complex FIQL queries."""
        plan = self.planner.plan_query("high priority open incidents from last month")
        
        assert plan.intent == "Find incidents matching filters"
        assert len(plan.steps) == 1
        fiql_query = plan.tool_calls[0].payload["query"]
        
        # Should include priority, status, and time filters
        assert "priority.name" in fiql_query
        assert "status!=" in fiql_query
        assert "creationDate=ge=" in fiql_query


class TestIntentDetection:
    """Test intent detection methods."""
    
    def setup_method(self):
        self.planner = QueryPlanner()
    
    def test_extract_person_name(self):
        """Test person name extraction."""
        assert self.planner._extract_person_name("tickets for John Doe") == "John Doe"
        assert self.planner._extract_person_name("John Smith's incidents") == "John Smith"
        assert self.planner._extract_person_name("user Jane incidents") == "Jane"
        assert self.planner._extract_person_name("no person here") is None
    
    def test_extract_operator_name(self):
        """Test operator name extraction."""
        assert self.planner._extract_operator_name("assigned to John Doe") == "John Doe"
        assert self.planner._extract_operator_name("operator Jane Smith") == "Jane Smith"
        assert self.planner._extract_operator_name("no operator here") is None
    
    def test_extract_incident_id(self):
        """Test incident ID extraction."""
        assert self.planner._extract_incident_id("incident I-240101-001") == "I-240101-001"
        assert self.planner._extract_incident_id("ticket I-231225-042") == "I-231225-042"
        assert self.planner._extract_incident_id("show I-240315-123 details") == "I-240315-123"
        assert self.planner._extract_incident_id("no incident here") is None
    
    def test_extract_status(self):
        """Test status extraction."""
        assert self.planner._extract_status("open tickets") == "open"
        assert self.planner._extract_status("closed incidents") == "closed"
        assert self.planner._extract_status("resolved issues") == "closed"
        assert self.planner._extract_status("pending requests") == "open"
        assert self.planner._extract_status("no status here") is None
    
    def test_extract_priority(self):
        """Test priority extraction."""
        assert self.planner._extract_priority("high priority tickets") == ["High"]
        assert self.planner._extract_priority("critical incidents") == ["Critical"]
        assert self.planner._extract_priority("urgent issues") == ["Critical"]
        assert self.planner._extract_priority("medium priority") == ["Medium"]
        assert self.planner._extract_priority("no priority here") is None
    
    def test_extract_category(self):
        """Test category extraction."""
        assert self.planner._extract_category("change requests") == "Change"
        assert self.planner._extract_category("RFC tickets") == "Change"
        assert self.planner._extract_category("request for change") == "Change"
        assert self.planner._extract_category("regular tickets") is None
    
    def test_is_search_query(self):
        """Test search query detection."""
        assert self.planner._is_search_query("email problem") is True
        assert self.planner._is_search_query("find password") is True
        assert self.planner._is_search_query("network") is True
        assert self.planner._is_search_query("assigned to John Doe high priority") is False