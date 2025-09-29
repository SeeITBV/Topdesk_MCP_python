# TOPdesk MCP Python - Comprehensive Tooling Guide

This guide provides detailed information on how to effectively use all 33 MCP tools available in the TOPdesk MCP Python server, with practical prompting examples and common usage patterns.

## Table of Contents
- [Getting Started](#getting-started)
- [Tool Categories Overview](#tool-categories-overview)
- [Discovery and Help Tools](#discovery-and-help-tools)
- [Incident Management Tools](#incident-management-tools)
- [Person Management Tools](#person-management-tools)
- [Operator Management Tools](#operator-management-tools)
- [Advanced Features](#advanced-features)
- [Common Usage Patterns](#common-usage-patterns)
- [Prompting Best Practices](#prompting-best-practices)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites
Before using these tools, ensure you have:
1. TOPdesk MCP Python server installed and configured
2. Valid TOPdesk credentials (URL, username, API token)
3. Your MCP client (like Claude Desktop) properly configured

### First Steps
Start by using these discovery tools to understand what's available:

```
What tools are available in this TOPdesk server?
```

```
Show me how to construct FIQL queries for searching incidents.
```

## Tool Categories Overview

The 33 MCP tools are organized into logical categories:

| Category | Count | Purpose |
|----------|-------|---------|
| **Discovery & Help** | 3 | Get help, list tools, view schemas |
| **Core Incident Management** | 8 | CRUD operations for incidents |
| **Incident Communication** | 4 | Actions, comments, requests |
| **Time & Escalation** | 6 | Time tracking and escalation management |
| **Attachments & Data** | 4 | File handling and comprehensive views |
| **Person Management** | 5 | User account operations |
| **Operator Management** | 3 | Operator and group management |

---

## Discovery and Help Tools

### 1. list_registered_tools
**Purpose**: Get a complete list of all available MCP tools
**Prompting Examples**:
```
"What tools are available?"
"List all functions I can use."
"Show me the complete tool inventory."
```

### 2. topdesk_get_fiql_query_howto
**Purpose**: Get comprehensive FIQL query syntax help and examples
**Prompting Examples**:
```
"How do I search for incidents using FIQL?"
"Show me FIQL query examples."
"What's the syntax for filtering incidents by date?"
```

### 3. topdesk_get_object_schemas
**Purpose**: Get complete object schemas for TOPdesk entities
**Prompting Examples**:
```
"What fields are available for incidents?"
"Show me the schema for TOPdesk incidents."
"What properties can I use when creating an incident?"
```

---

## Incident Management Tools

### Core Operations

#### 4. topdesk_get_incident
**Purpose**: Retrieve a specific incident by ID or number
**Parameters**:
- `incident_id` (string, required): UUID or incident number (I-xxxxxx-xxx)
- `concise` (boolean, optional): Return concise version (default: true)

**Prompting Examples**:
```
"Get incident I-240101-001"
"Show me the full details for incident 12345678-1234-1234-1234-123456789012"
"Retrieve incident I-240315-042 with all details"
```

#### 5. topdesk_get_incidents_by_fiql_query
**Purpose**: Search incidents using FIQL query language
**Parameters**:
- `query` (string, required): FIQL query string

**Prompting Examples**:
```
"Find all incidents created today"
"Show me high priority incidents assigned to the Network team"
"Get incidents where caller name contains 'John' and status is 'secondLine'"
```

**FIQL Query Examples**:
- Recent incidents: `creationDate=ge=2024-01-01T00:00:00Z`
- Specific caller: `caller.name=sw='John'`
- Multiple conditions: `status=secondLine;priority.name=High`

#### 6. search (Simple Search)
**Purpose**: Simple text search for incidents by title
**Parameters**:
- `query` (string, required): Search term for incident titles
- `max_results` (integer, optional): Maximum results (default: 5, max: 100)

**Prompting Examples**:
```
"Search for incidents about email problems"
"Find incidents with 'network' in the title, limit to 10 results"
"Look for printer-related incidents"
```

#### 7. fetch
**Purpose**: Alternative way to get incident data
**Parameters**: Similar to topdesk_get_incident

**Prompting Examples**:
```
"Fetch details for incident I-240101-001"
"Get the data for this incident number"
```

#### 8. topdesk_create_incident
**Purpose**: Create a new incident
**Parameters**:
- `caller_id` (string, required): ID of the person reporting the incident
- `incident_fields` (object, required): Dictionary with incident details

**Required fields in incident_fields**:
- `briefDescription`: Short summary
- `request`: Detailed description

**Prompting Examples**:
```
"Create an incident for user 12345 about email issues"
"Log a new incident for John Doe (ID: abc123) regarding printer problems"
```

**Detailed Example**:
```
Create an incident with these details:
- Caller ID: user-123
- Title: Cannot access shared folder
- Description: User reports inability to access \\server\shared since this morning
```

#### 9. topdesk_archive_incident
**Purpose**: Archive an incident
**Parameters**:
- `incident_id` (string, required): Incident UUID or number

**Prompting Examples**:
```
"Archive incident I-240101-001"
"Close and archive incident 12345"
```

#### 10. topdesk_unarchive_incident
**Purpose**: Unarchive an incident
**Parameters**: Same as archive

**Prompting Examples**:
```
"Unarchive incident I-240101-001"
"Reopen incident 12345"
```

### Communication & Requests

#### 11. topdesk_get_incident_user_requests
**Purpose**: Get all user requests/communications on an incident
**Prompting Examples**:
```
"Show me all user requests for incident I-240101-001"
"What communications are there on this incident?"
```

#### 12. topdesk_add_action_to_incident
**Purpose**: Add a comment or action to an incident
**Parameters**:
- `incident_id` (string, required): Target incident
- `action_text` (string, required): Comment text

**Prompting Examples**:
```
"Add comment to incident I-240101-001: 'Issue resolved by restarting service'"
"Post an update on incident 12345 saying the fix has been deployed"
```

#### 13. topdesk_get_incident_actions
**Purpose**: Get all actions/comments on an incident
**Prompting Examples**:
```
"Show me all comments on incident I-240101-001"
"Get the action history for this incident"
```

#### 14. topdesk_delete_incident_action
**Purpose**: Delete a specific action/comment
**Parameters**:
- `incident_id` (string, required): Target incident
- `action_id` (string, required): Specific action to delete

**Prompting Examples**:
```
"Delete action abc123 from incident I-240101-001"
"Remove the last comment from this incident"
```

### Time Tracking

#### 15. topdesk_get_timespent_on_incident
**Purpose**: Get all time entries for an incident
**Prompting Examples**:
```
"Show me time spent on incident I-240101-001"
"How much time has been logged on this incident?"
```

#### 16. topdesk_register_timespent_on_incident
**Purpose**: Log time spent on an incident
**Parameters**:
- `incident_id` (string, required): Target incident
- `time_spent` (number, required): Time in minutes
- `description` (string, optional): Description of work done

**Prompting Examples**:
```
"Log 30 minutes on incident I-240101-001 for troubleshooting"
"Register 2 hours of work on incident 12345 with description 'Applied patch and tested'"
```

### Escalation Management

#### 17. topdesk_escalate_incident
**Purpose**: Escalate an incident
**Parameters**:
- `incident_id` (string, required): Target incident
- `escalation_reason_id` (string, required): Reason for escalation

**Prompting Examples**:
```
"Escalate incident I-240101-001 due to complexity"
"Move incident 12345 to higher support tier"
```

#### 18. topdesk_get_available_escalation_reasons
**Purpose**: Get list of available escalation reasons
**Prompting Examples**:
```
"What escalation reasons are available?"
"Show me the escalation options"
```

#### 19. topdesk_get_available_deescalation_reasons
**Purpose**: Get list of de-escalation reasons
**Prompting Examples**:
```
"What de-escalation reasons can I use?"
"Show available options for de-escalating incidents"
```

#### 20. topdesk_deescalate_incident
**Purpose**: De-escalate an incident
**Parameters**:
- `incident_id` (string, required): Target incident
- `deescalation_reason_id` (string, required): Reason for de-escalation

**Prompting Examples**:
```
"De-escalate incident I-240101-001 back to first line"
"Lower the escalation level for incident 12345"
```

---

## Advanced Features

### Progress and Attachments

#### 21. topdesk_get_progress_trail
**Purpose**: Get detailed progress history of an incident
**Parameters**:
- `incident_id` (string, required): Target incident
- `inlineimages` (boolean, optional): Include inline images (default: true)
- `force_images_as_data` (boolean, optional): Convert images to base64 (default: true)

**Prompting Examples**:
```
"Show me the complete progress trail for incident I-240101-001"
"Get the history of changes for this incident with images"
```

#### 22. topdesk_get_incident_attachments
**Purpose**: Get all attachments as base64-encoded data
**Prompting Examples**:
```
"Get all attachments for incident I-240101-001"
"Show me files attached to this incident"
```

#### 23. topdesk_get_incident_attachments_as_markdown
**Purpose**: Convert incident attachments to readable markdown
**Parameters**:
- `incident_id` (string, required): Target incident

**Prompting Examples**:
```
"Convert all attachments for incident I-240101-001 to readable text"
"Get the contents of attached documents for this incident"
```

#### 24. topdesk_get_complete_incident_overview
**Purpose**: Get comprehensive incident view (details + progress + attachments)
**Prompting Examples**:
```
"Give me everything about incident I-240101-001"
"Show me the complete overview of incident 12345 including all files"
```

---

## Person Management Tools

#### 25. topdesk_get_person_by_query
**Purpose**: Search for persons using FIQL
**Parameters**:
- `query` (string, required): FIQL query for person search

**Prompting Examples**:
```
"Find persons with email containing '@company.com'"
"Search for users in the IT department"
"Get persons with surname 'Smith'"
```

**FIQL Examples**:
- Email search: `email=sw='@company.com'`
- Department: `department.name=='IT'`
- Name: `surname=sw='Smith'`

#### 26. topdesk_get_person
**Purpose**: Get specific person by ID
**Parameters**:
- `person_id` (string, required): Person UUID

**Prompting Examples**:
```
"Get details for person 12345678-1234-1234-1234-123456789012"
"Show me information about user abc123"
```

#### 27. topdesk_create_person
**Purpose**: Create a new person record
**Parameters**:
- `person_data` (object, required): Dictionary with person details

**Required fields**:
- `email`: Email address
- `firstName`: First name
- `surName`: Last name

**Prompting Examples**:
```
"Create a new user: John Smith, email john.smith@company.com"
"Add a new person with email jane@company.com, first name Jane, last name Doe"
```

#### 28. topdesk_update_person
**Purpose**: Update existing person
**Parameters**:
- `person_id` (string, required): Person UUID
- `person_data` (object, required): Fields to update

**Prompting Examples**:
```
"Update person 12345 with new email address"
"Change the department for user abc123"
```

#### 29. topdesk_archive_person
**Purpose**: Archive a person record
**Prompting Examples**:
```
"Archive person 12345"
"Deactivate user account for abc123"
```

#### 30. topdesk_unarchive_person
**Purpose**: Unarchive a person record
**Prompting Examples**:
```
"Unarchive person 12345"
"Reactivate user account for abc123"
```

---

## Operator Management Tools

#### 31. topdesk_get_operators_by_fiql_query
**Purpose**: Search operators using FIQL
**Prompting Examples**:
```
"Find operators in the Network support group"
"Get all operators with 'admin' in their username"
```

#### 32. topdesk_get_operator
**Purpose**: Get specific operator by ID
**Prompting Examples**:
```
"Get details for operator 12345"
"Show me information about operator abc123"
```

#### 33. topdesk_get_operatorgroups_of_operator
**Purpose**: Get operator groups for a specific operator
**Parameters**:
- `operator_id` (string, required): Operator UUID
- `query` (string, optional): FIQL filter for groups

**Prompting Examples**:
```
"What groups is operator 12345 a member of?"
"Show me the operator groups for user abc123"
```

---

## Common Usage Patterns

### Daily Support Operations

#### Morning Incident Review
```
"Show me all high priority incidents created yesterday"
"Get incidents assigned to my team that are still open"
"Find any escalated incidents that need attention"
```

#### Incident Investigation
```
"Get complete overview of incident I-240101-001"
"Show me all incidents from user john.doe@company.com in the last week" 
"Find similar incidents with 'email' in the title from this month"
```

#### Progress Updates
```
"Add comment to incident I-240101-001: 'Root cause identified, applying fix'"
"Log 45 minutes on incident 12345 for patch deployment and testing"
"Update status and add resolution details"
```

### Batch Operations

#### User Management
```
"Find all users in the Finance department"
"Get contact details for all users with email ending in '@contractor.com'"
"Archive all users who haven't logged in since 2023"
```

#### Reporting and Analysis
```
"Show me all incidents created by Network team this month"
"Get time spent on all incidents assigned to operator 12345"
"Find incidents that were escalated and later de-escalated"
```

### Complex Searches

#### Multi-criteria Incident Search
```
"Find incidents where:
- Created in the last 7 days
- Priority is High or Critical  
- Status is not Closed
- Assigned to Network or Server team"
```

Translated to FIQL:
```
creationDate=ge=2024-03-15T00:00:00Z;priority.name=in=(High,Critical);status!=Closed;operatorGroup.name=in=(Network,Server)
```

#### Attachment Analysis
```
"Get all incidents from last month that have attachments and convert them to readable format"
"Find incidents with PDF attachments containing the word 'error'"
```

---

## Prompting Best Practices

### 1. Be Specific with IDs
✅ Good: `"Get incident I-240101-001"`  
❌ Avoid: `"Get that incident"`

### 2. Use Clear Time References
✅ Good: `"Find incidents created after 2024-03-01"`  
❌ Avoid: `"Find recent incidents"`

### 3. Specify Result Limits
✅ Good: `"Search for email incidents, limit to 10 results"`  
❌ Avoid: `"Search for email incidents"` (may return too many)

### 4. Combine Operations Logically
✅ Good: `"Get complete overview of incident I-240101-001 then add comment 'Investigating'"`  
❌ Avoid: Multiple separate requests

### 5. Use Appropriate Tools for Tasks
- Use `search` for simple title-based searches
- Use `topdesk_get_incidents_by_fiql_query` for complex filtering
- Use `topdesk_get_complete_incident_overview` for comprehensive investigation

### 6. Provide Context for Actions
✅ Good: `"Log 30 minutes on incident I-240101-001 for 'Network configuration troubleshooting'"`  
❌ Avoid: `"Log 30 minutes on incident I-240101-001"`

### 7. Use Structured Requests for Creation
✅ Good:
```
"Create incident with:
- Caller: user-123
- Title: Printer offline in Building A
- Description: HP LaserJet in room 101 shows offline status, users cannot print"
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. "Incident ID must be provided and cannot be empty"
**Cause**: Empty or invalid incident ID  
**Solution**: Ensure you're using the correct format (UUID or I-xxxxxx-xxx)

#### 2. "FIQL query must be provided and cannot be empty"  
**Cause**: Empty FIQL query string  
**Solution**: Use the `topdesk_get_fiql_query_howto` tool for syntax help

#### 3. "Caller ID must be provided and cannot be empty"
**Cause**: Missing caller ID in incident creation  
**Solution**: First find the person using `topdesk_get_person_by_query`

#### 4. "Error reading FIQL query guide" or "Error reading object schemas"
**Cause**: Missing resource files  
**Solution**: Ensure the server is properly installed with all resource files

#### 5. Authentication Errors
**Cause**: Invalid credentials or expired tokens  
**Solution**: Check TOPDESK_URL, TOPDESK_USERNAME, and TOPDESK_PASSWORD environment variables

### Getting Help

1. **List Available Tools**: Start with `list_registered_tools`
2. **Query Syntax Help**: Use `topdesk_get_fiql_query_howto`
3. **Schema Reference**: Use `topdesk_get_object_schemas`
4. **Test with Simple Operations**: Try `search` before complex FIQL queries
5. **Check Existing Documentation**: Refer to DEVELOPER_GUIDE.md and CODEBASE_DOCUMENTATION.md

### Performance Tips

1. **Use Concise Mode**: Set `concise=true` for faster incident retrieval
2. **Limit Results**: Always specify reasonable `max_results` for searches
3. **Cache IDs**: Store frequently used person/operator IDs to avoid repeated lookups
4. **Batch Operations**: Group related operations together in your prompts

---

## Advanced Integration Examples

### Workflow Automation
```
"For incident I-240101-001:
1. Get complete overview
2. If priority is High, escalate with reason 'Complexity'
3. Add comment with current status
4. Log investigation time"
```

### Reporting Workflows
```
"Generate weekly report:
1. Find all incidents created this week
2. Group by operator assignment
3. Show resolution times and status distribution
4. Include any escalated incidents"
```

### User Onboarding
```
"Create new user workflow:
1. Create person record for John Smith (john.smith@company.com)
2. Add to IT department
3. Create welcome incident for account setup
4. Assign to onboarding team"
```

---

This guide covers all 33 MCP tools available in the TOPdesk MCP Python server. For technical implementation details, see the [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) and [CODEBASE_DOCUMENTATION.md](CODEBASE_DOCUMENTATION.md).

For additional support, refer to the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for setup and configuration help.