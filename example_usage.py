#!/usr/bin/env python3
"""
Example usage of the Natural Language → TOPdesk MCP Router

This script demonstrates how to interact with the router programmatically
without running the full FastAPI server.
"""

import asyncio
import json
from app.router import QueryRouter
from app.schemas import QueryRequest


async def demonstrate_router():
    """Demonstrate the router functionality with example queries."""
    
    router = QueryRouter()
    
    # Example queries to test
    example_queries = [
        {
            "query": "tickets for John Doe",
            "description": "Person-specific query (2-step lookup)"
        },
        {
            "query": "email problems", 
            "description": "Simple search query"
        },
        {
            "query": "high priority open incidents from last week",
            "description": "Complex FIQL query with filters"
        },
        {
            "query": "show complete details for incident I-240101-001",
            "description": "Complete incident overview"
        },
        {
            "query": "recent changes",
            "description": "Category-based query"
        },
        {
            "query": "tickets for Sander",
            "description": "Ambiguous query (should ask for clarification)"
        }
    ]
    
    print("=" * 60)
    print("Natural Language → TOPdesk MCP Router Demo")
    print("=" * 60)
    print()
    
    for i, example in enumerate(example_queries, 1):
        query_text = example["query"]
        description = example["description"]
        
        print(f"{i}. Query: \"{query_text}\"")
        print(f"   Type: {description}")
        print()
        
        # Create request
        request = QueryRequest(query=query_text, max_results=5)
        
        try:
            # Process query (this will fail without actual MCP server)
            # But we can still see the planning
            response = await router.process_query(request, "127.0.0.1")
            
            print(f"   Plan: {response.plan.intent}")
            print(f"   Steps: {len(response.plan.steps)}")
            print(f"   Tools: {[tc.name for tc in response.plan.tool_calls]}")
            
            if response.plan.clarify:
                print(f"   Clarification: {response.plan.clarify}")
            
            if response.plan.warnings:
                print(f"   Warnings: {response.plan.warnings}")
            
            print(f"   Summary: {response.summary}")
            
        except Exception as e:
            # Expected - no actual MCP server running
            print(f"   (Planning successful, MCP call would fail: {type(e).__name__})")
        
        print()
        print("-" * 60)
        print()


def demonstrate_planning_only():
    """Show just the planning without trying to execute."""
    
    from app.planning import QueryPlanner
    
    planner = QueryPlanner()
    
    print("=" * 60)
    print("Query Planning Examples (No MCP Server Required)")
    print("=" * 60)
    print()
    
    queries = [
        "tickets for John Doe",
        "open incidents assigned to Jane Smith",
        "email problems", 
        "recent changes",
        "high priority tickets from yesterday",
        "show complete details for incident I-240101-001",
        "tickets for Sander"  # Ambiguous
    ]
    
    for query in queries:
        plan = planner.plan_query(query, max_results=5)
        
        print(f"Query: \"{query}\"")
        print(f"  Intent: {plan.intent}")
        print(f"  Steps: {len(plan.steps)}")
        
        for i, step in enumerate(plan.steps, 1):
            print(f"    {i}. {step.action} ({step.tool_name})")
        
        if plan.clarify:
            print(f"  Clarification: {plan.clarify}")
        
        if plan.warnings:
            print(f"  Warnings: {plan.warnings}")
        
        print()


def demonstrate_fiql_building():
    """Show FIQL query building examples."""
    
    from app.fiql import (
        build_incident_query, build_person_query, build_operator_query,
        and_join, or_join, in_list, equals, days_ago
    )
    
    print("=" * 60)
    print("FIQL Query Building Examples")
    print("=" * 60)
    print()
    
    # Person query
    person_fiql = build_person_query(first_name="John", last_name="Doe")
    print(f"Person lookup: {person_fiql}")
    
    # Operator query
    operator_fiql = build_operator_query("Jane Smith", exact=True)
    print(f"Operator lookup: {operator_fiql}")
    
    # Complex incident query
    incident_fiql = build_incident_query(
        caller_id="person-123",
        status_exclude=["Closed"],
        priority_levels=["High", "Critical"],
        category="Change",
        days_back=30
    )
    print(f"Complex incident query: {incident_fiql}")
    
    # Manual FIQL building
    manual_fiql = and_join(
        equals("status", "Open"),
        in_list("priority.name", ["High", "Critical"]),
        f"creationDate=ge={days_ago(7)}"
    )
    print(f"Manual FIQL: {manual_fiql}")
    print()


if __name__ == "__main__":
    print("Choose demo mode:")
    print("1. Planning only (no MCP server needed)")
    print("2. FIQL building examples")
    print("3. Full router demo (will show MCP errors)")
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        demonstrate_planning_only()
    elif choice == "2":
        demonstrate_fiql_building()
    elif choice == "3":
        asyncio.run(demonstrate_router())
    else:
        print("Invalid choice. Running planning demo...")
        demonstrate_planning_only()