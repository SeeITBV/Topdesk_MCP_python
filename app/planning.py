"""Natural language query planning and intent detection."""

import re
import logging
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from .schemas import QueryPlan, PlanStep, ToolCall
from .fiql import (
    build_person_query, build_operator_query, build_incident_query,
    days_ago, and_join
)
from .validators import validate_incident_number, ValidationError


logger = logging.getLogger(__name__)


class QueryPlanner:
    """Plans execution for natural language queries."""
    
    def __init__(self):
        # Common patterns for intent detection
        self.person_patterns = [
            r'\b(?:tickets?|incidents?|issues?)\s+(?:of|from|by|for)\s+([A-Za-z][A-Za-z\s]+[A-Za-z])',
            r'\b([A-Za-z][A-Za-z\s]+[A-Za-z])\'s?\s+(?:tickets?|incidents?|issues?)',
            r'\b(?:user|person|caller)\s+([A-Za-z][A-Za-z\s]+[A-Za-z])',
        ]
        
        self.operator_patterns = [
            r'\b(?:assigned\s+to|operator|technician)\s+([A-Za-z\s]+)',
            r'\b([A-Za-z\s]+)\s+(?:is\s+)?(?:working\s+on|handling)',
        ]
        
        self.status_patterns = [
            r'\b(open|closed|resolved|pending|new)\s+(?:tickets?|incidents?)',
            r'\b(?:tickets?|incidents?)\s+(?:that\s+are\s+)?(open|closed|resolved|pending|new)',
            r'\bstatus\s*[=:]\s*(open|closed|resolved|pending|new)'
        ]
        
        self.priority_patterns = [
            r'\b(high|low|medium|critical|urgent)\s+priority',
            r'\bpriority\s*[=:]\s*(high|low|medium|critical|urgent)',
            r'\b(critical|urgent|high|medium|low)\s+(?:tickets?|incidents?)'
        ]
        
        self.category_patterns = [
            r'\b(change|rfc|request\s+for\s+change)s?\b',
            r'\bcategory\s*[=:]\s*([A-Za-z\s]+)',
        ]
        
        self.incident_id_patterns = [
            r'\b(I-\d{6}-\d{3})\b',  # TOPdesk incident format
            r'\bincident\s+(I-\d{6}-\d{3})\b',
            r'\bticket\s+(I-\d{6}-\d{3})\b'
        ]
        
        self.time_patterns = [
            r'\b(?:last|past|recent)\s+(\d+)\s+(days?|weeks?|months?)',
            r'\b(\d+)\s+(days?|weeks?|months?)\s+ago',
            r'\btoday\b',
            r'\byesterday\b',
            r'\bthis\s+(week|month)',
            r'\blast\s+(week|month)'
        ]
    
    def plan_query(self, query: str, max_results: int = 5) -> QueryPlan:
        """Plan execution for a natural language query.
        
        Args:
            query: Natural language query
            max_results: Maximum results to return
            
        Returns:
            QueryPlan with execution steps and tool calls
        """
        query = query.lower().strip()
        logger.debug(f"Planning query: {query}")
        
        # Detect various intents
        person_match = self._extract_person_name(query)
        operator_match = self._extract_operator_name(query)
        incident_id = self._extract_incident_id(query)
        status_filter = self._extract_status(query)
        priority_filter = self._extract_priority(query)
        category_filter = self._extract_category(query)
        time_filter = self._extract_time_constraint(query)
        
        # Check for complete incident overview request
        if incident_id and any(word in query for word in ['complete', 'full', 'overview', 'details', 'all']):
            return self._plan_complete_incident(incident_id, query)
        
        # Check for person-specific queries
        if person_match:
            return self._plan_person_query(person_match, status_filter, time_filter, max_results, query)
        
        # Check for operator-specific queries
        if operator_match:
            return self._plan_operator_query(operator_match, status_filter, time_filter, max_results, query)
        
        # Check for category-specific queries (e.g., changes/RFCs)
        if category_filter:
            return self._plan_category_query(category_filter, status_filter, priority_filter, time_filter, max_results, query)
        
        # Check for simple search queries
        if self._is_search_query(query):
            return self._plan_search_query(query, time_filter, max_results)
        
        # Check for FIQL-appropriate queries
        if any([status_filter, priority_filter, time_filter]) or len(query.split()) > 5:
            return self._plan_fiql_query(query, status_filter, priority_filter, time_filter, max_results)
        
        # Ambiguous query - ask for clarification
        return self._plan_clarification(query)
    
    def _extract_person_name(self, query: str) -> Optional[str]:
        """Extract person name from query."""
        for pattern in self.person_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Filter out common non-names and non-person terms
                excluded_terms = [
                    'user', 'person', 'caller', 'someone', 'tickets', 'incidents',
                    'changes', 'problems', 'issues', 'requests', 'email', 'password',
                    'network', 'system', 'server', 'application', 'last week', 'yesterday',
                    'recent', 'open', 'closed', 'high', 'low', 'medium', 'critical',
                    'priority', 'urgent'
                ]
                if name.lower() not in excluded_terms and len(name.split()) <= 3:
                    # Check if it looks like a name (contains letters, reasonable length)
                    if re.match(r'^[A-Za-z\s\-\'\.]+$', name) and 2 <= len(name) <= 50:
                        return name
        return None
    
    def _extract_operator_name(self, query: str) -> Optional[str]:
        """Extract operator name from query."""
        for pattern in self.operator_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if name.lower() not in ['operator', 'technician', 'support']:
                    return name
        return None
    
    def _extract_incident_id(self, query: str) -> Optional[str]:
        """Extract incident ID from query."""
        for pattern in self.incident_id_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_status(self, query: str) -> Optional[str]:
        """Extract status filter from query."""
        for pattern in self.status_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                status = match.group(1).lower()
                # Map common variations
                if status in ['open', 'new', 'pending']:
                    return 'open'
                elif status in ['closed', 'resolved']:
                    return 'closed'
                return status
        
        # Default to open if query mentions open-related terms
        if any(word in query for word in ['open', 'active', 'unresolved', 'pending']):
            return 'open'
        
        return None
    
    def _extract_priority(self, query: str) -> Optional[List[str]]:
        """Extract priority filter from query."""
        priorities = []
        
        for pattern in self.priority_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                priority = match.group(1).lower()
                # Map to standard priority names
                if priority in ['critical', 'urgent']:
                    priorities.append('Critical')
                elif priority == 'high':
                    priorities.append('High')
                elif priority == 'medium':
                    priorities.append('Medium')  
                elif priority == 'low':
                    priorities.append('Low')
        
        return priorities if priorities else None
    
    def _extract_category(self, query: str) -> Optional[str]:
        """Extract category filter from query."""
        for pattern in self.category_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                category = match.group(1).lower()
                if 'change' in category or 'rfc' in category:
                    return 'Change'
        return None
    
    def _extract_time_constraint(self, query: str) -> Optional[int]:
        """Extract time constraint in days from query."""
        for pattern in self.time_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                if 'today' in match.group(0).lower():
                    return 1
                elif 'yesterday' in match.group(0).lower():
                    return 2
                elif 'this week' in match.group(0).lower():
                    return 7
                elif 'last week' in match.group(0).lower():
                    return 14
                elif 'this month' in match.group(0).lower():
                    return 30
                elif 'last month' in match.group(0).lower():
                    return 60
                else:
                    try:
                        number = int(match.group(1))
                        unit = match.group(2).lower()
                        if 'day' in unit:
                            return number
                        elif 'week' in unit:
                            return number * 7
                        elif 'month' in unit:
                            return number * 30
                    except (ValueError, IndexError):
                        pass
        
        return None  # Default will be applied in query building
    
    def _is_search_query(self, query: str) -> bool:
        """Determine if query is better suited for search."""
        # Simple heuristics for search vs FIQL
        search_indicators = [
            len(query.split()) <= 3,  # Short queries
            any(word in query for word in ['find', 'search', 'look for']),
            not any(op in query for op in ['status', 'priority', 'assigned', 'operator', 'for', 'to']),
            # Technical terms that are better for search
            any(term in query.lower() for term in [
                'email', 'password', 'network', 'server', 'application', 'system',
                'login', 'access', 'error', 'problem', 'issue', 'bug', 'crash'
            ])
        ]
        return any(search_indicators)
    
    def _plan_person_query(self, person_name: str, status_filter: Optional[str], 
                          time_filter: Optional[int], max_results: int, original_query: str) -> QueryPlan:
        """Plan a person-specific query."""
        steps = []
        tool_calls = []
        warnings = []
        
        # Step 1: Look up person
        name_parts = person_name.split()
        if len(name_parts) >= 2:
            first_name, last_name = name_parts[0], name_parts[-1]
            person_fiql = build_person_query(first_name=first_name, last_name=last_name)
        else:
            # Try surname lookup first
            person_fiql = build_person_query(last_name=person_name)
        
        steps.append(PlanStep(
            step=1,
            action=f"Look up person: {person_name}",
            tool_name="topdesk_get_person_by_query",
            reasoning=f"Need to find person ID for '{person_name}' to search their incidents"
        ))
        
        tool_calls.append(ToolCall(
            name="topdesk_get_person_by_query",
            payload={"fiql_query": person_fiql}
        ))
        
        # Step 2: Get incidents for person
        time_days = time_filter or 30  # Default to 30 days
        
        # Build incident query (we'll use placeholder for caller_id)
        incident_filters = []
        if status_filter == 'open':
            incident_filters.append("status!=Closed")
        
        incident_filters.append(f"creationDate=ge={days_ago(time_days)}")
        
        incident_query = and_join(*incident_filters)  # Will prepend caller.id later
        
        steps.append(PlanStep(
            step=2,
            action=f"Get incidents for person (last {time_days} days)",
            tool_name="topdesk_get_incidents_by_fiql_query",
            reasoning=f"Retrieve incidents where caller is the found person, filtered by time and status"
        ))
        
        # Note: The actual caller.id will be filled in during execution
        tool_calls.append(ToolCall(
            name="topdesk_get_incidents_by_fiql_query",
            payload={
                "fiql_query": f"caller.id==PLACEHOLDER;{incident_query}",
                "page_size": max_results
            }
        ))
        
        if len(name_parts) < 2:
            warnings.append(f"Single name '{person_name}' may match multiple people")
        
        return QueryPlan(
            intent=f"Find incidents for person: {person_name}",
            steps=steps,
            tool_calls=tool_calls,
            warnings=warnings
        )
    
    def _plan_operator_query(self, operator_name: str, status_filter: Optional[str],
                           time_filter: Optional[int], max_results: int, original_query: str) -> QueryPlan:
        """Plan an operator-specific query."""
        steps = []
        tool_calls = []
        warnings = []
        
        # Step 1: Look up operator
        operator_fiql = build_operator_query(operator_name, exact=True)
        
        steps.append(PlanStep(
            step=1,
            action=f"Look up operator: {operator_name}",
            tool_name="topdesk_get_operators_by_fiql_query", 
            reasoning=f"Need to find operator ID for '{operator_name}' to search assigned incidents"
        ))
        
        tool_calls.append(ToolCall(
            name="topdesk_get_operators_by_fiql_query",
            payload={"fiql_query": operator_fiql}
        ))
        
        # Step 2: Get incidents for operator
        time_days = time_filter or 30
        
        incident_filters = []
        if status_filter == 'open':
            incident_filters.append("status!=Closed")
        
        incident_filters.append(f"creationDate=ge={days_ago(time_days)}")
        
        incident_query = and_join(*incident_filters)
        
        steps.append(PlanStep(
            step=2,
            action=f"Get incidents assigned to operator (last {time_days} days)",
            tool_name="topdesk_get_incidents_by_fiql_query",
            reasoning=f"Retrieve incidents assigned to the found operator"
        ))
        
        tool_calls.append(ToolCall(
            name="topdesk_get_incidents_by_fiql_query",
            payload={
                "fiql_query": f"operator.id==PLACEHOLDER;{incident_query}",
                "page_size": max_results
            }
        ))
        
        return QueryPlan(
            intent=f"Find incidents assigned to operator: {operator_name}",
            steps=steps,
            tool_calls=tool_calls,
            warnings=warnings
        )
    
    def _plan_category_query(self, category: str, status_filter: Optional[str],
                           priority_filter: Optional[List[str]], time_filter: Optional[int],
                           max_results: int, original_query: str) -> QueryPlan:
        """Plan a category-specific query."""
        time_days = time_filter or 60  # Default to 60 days for changes
        
        fiql_parts = [f"category.name=='{category}'"]
        
        if status_filter == 'open':
            fiql_parts.append("status!=Closed")
        
        if priority_filter:
            from .fiql import in_list
            fiql_parts.append(in_list("priority.name", priority_filter))
        
        fiql_parts.append(f"creationDate=ge={days_ago(time_days)}")
        
        fiql_query = and_join(*fiql_parts)
        
        steps = [PlanStep(
            step=1,
            action=f"Get {category} incidents (last {time_days} days)",
            tool_name="topdesk_get_incidents_by_fiql_query",
            reasoning=f"Search for incidents in {category} category with specified filters"
        )]
        
        tool_calls = [ToolCall(
            name="topdesk_get_incidents_by_fiql_query",
            payload={
                "fiql_query": fiql_query,
                "page_size": max_results
            }
        )]
        
        return QueryPlan(
            intent=f"Find {category} incidents",
            steps=steps,
            tool_calls=tool_calls
        )
    
    def _plan_search_query(self, query: str, time_filter: Optional[int], max_results: int) -> QueryPlan:
        """Plan a simple search query."""
        steps = [PlanStep(
            step=1,
            action=f"Search for: {query}",
            tool_name="search",
            reasoning="Simple text search across incident data"
        )]
        
        # Add time filter to search if available - note: search may not support this
        search_payload = {
            "query": query,
            "max_results": max_results
        }
        
        tool_calls = [ToolCall(
            name="search",
            payload=search_payload
        )]
        
        warnings = []
        if time_filter:
            warnings.append(f"Time filter of {time_filter} days may not be applied to search results")
        
        return QueryPlan(
            intent=f"Search for: {query}",
            steps=steps,
            tool_calls=tool_calls,
            warnings=warnings
        )
    
    def _plan_fiql_query(self, query: str, status_filter: Optional[str],
                        priority_filter: Optional[List[str]], time_filter: Optional[int],
                        max_results: int) -> QueryPlan:
        """Plan a FIQL-based query for complex filtering."""
        time_days = time_filter or 30
        
        fiql_parts = []
        
        if status_filter == 'open':
            fiql_parts.append("status!=Closed")
        
        if priority_filter:
            from .fiql import in_list
            fiql_parts.append(in_list("priority.name", priority_filter))
        
        # Always add time filter for FIQL queries
        fiql_parts.append(f"creationDate=ge={days_ago(time_days)}")
        
        fiql_query = and_join(*fiql_parts)
        
        steps = [PlanStep(
            step=1,
            action=f"Query incidents with filters (last {time_days} days)",
            tool_name="topdesk_get_incidents_by_fiql_query",
            reasoning="Use FIQL to filter incidents by status, priority, and time"
        )]
        
        tool_calls = [ToolCall(
            name="topdesk_get_incidents_by_fiql_query", 
            payload={
                "fiql_query": fiql_query,
                "page_size": max_results
            }
        )]
        
        return QueryPlan(
            intent="Find incidents matching filters",
            steps=steps,
            tool_calls=tool_calls
        )
    
    def _plan_complete_incident(self, incident_id: str, original_query: str) -> QueryPlan:
        """Plan complete incident overview query."""
        try:
            validate_incident_number(incident_id)
        except ValidationError as e:
            return QueryPlan(
                intent="Invalid incident ID",
                steps=[],
                tool_calls=[],
                clarify=f"Invalid incident number format: {incident_id}. Expected format: I-YYMMDD-NNN"
            )
        
        steps = [PlanStep(
            step=1,
            action=f"Get complete overview for incident {incident_id}",
            tool_name="topdesk_get_complete_incident_overview",
            reasoning=f"Retrieve full details for incident {incident_id}"
        )]
        
        tool_calls = [ToolCall(
            name="topdesk_get_complete_incident_overview",
            payload={"incident_id": incident_id}
        )]
        
        return QueryPlan(
            intent=f"Get complete details for incident {incident_id}",
            steps=steps,
            tool_calls=tool_calls
        )
    
    def _plan_clarification(self, query: str) -> QueryPlan:
        """Plan clarification request for ambiguous queries."""
        clarification_msg = "Your query is ambiguous. Please specify:\n"
        
        # Check what might be unclear
        if any(name in query.lower() for name in ['sander', 'john', 'jane']):
            clarification_msg += "- The full name of the person you're asking about\n"
        
        if 'ticket' in query.lower() or 'incident' in query.lower():
            clarification_msg += "- Whether you want open/closed incidents\n"
            clarification_msg += "- The time period you're interested in\n"
        
        clarification_msg += "- What specific information you need"
        
        return QueryPlan(
            intent="Clarification needed",
            steps=[],
            tool_calls=[],
            clarify=clarification_msg
        )