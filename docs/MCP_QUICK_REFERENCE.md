# TOPdesk MCP Python - Quick Reference Guide

A concise reference for all 33 MCP tools with example prompts.

## 🔍 Discovery & Help (3 tools)

| Tool | Quick Prompt Example |
|------|---------------------|
| `list_registered_tools` | *"What tools are available?"* |
| `topdesk_get_fiql_query_howto` | *"Show me FIQL query syntax"* |
| `topdesk_get_object_schemas` | *"What fields can I use for incidents?"* |

## 🎫 Core Incident Management (8 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_incident` | `incident_id`, `concise=true` | *"Get incident I-240101-001"* |
| `topdesk_get_incidents_by_fiql_query` | `query` | *"Find high priority incidents from this week"* |
| `search` | `query`, `max_results=5` | *"Search for email problems"* |
| `fetch` | `incident_id` | *"Fetch details for incident 12345"* |
| `topdesk_create_incident` | `caller_id`, `incident_fields` | *"Create incident for user 123 about printer issues"* |
| `topdesk_archive_incident` | `incident_id` | *"Archive incident I-240101-001"* |
| `topdesk_unarchive_incident` | `incident_id` | *"Reopen incident I-240101-001"* |

## 💬 Communication & Requests (4 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_incident_user_requests` | `incident_id` | *"Show user requests for incident I-240101-001"* |
| `topdesk_add_action_to_incident` | `incident_id`, `action_text` | *"Add comment: 'Issue resolved'"* |
| `topdesk_get_incident_actions` | `incident_id` | *"Show all comments on this incident"* |
| `topdesk_delete_incident_action` | `incident_id`, `action_id` | *"Delete comment abc123 from incident"* |

## ⏱️ Time Tracking (2 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_timespent_on_incident` | `incident_id` | *"How much time was spent on incident I-240101-001?"* |
| `topdesk_register_timespent_on_incident` | `incident_id`, `time_spent`, `description` | *"Log 30 minutes for troubleshooting"* |

## 📈 Escalation Management (4 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_escalate_incident` | `incident_id`, `escalation_reason_id` | *"Escalate incident I-240101-001"* |
| `topdesk_deescalate_incident` | `incident_id`, `deescalation_reason_id` | *"De-escalate incident I-240101-001"* |
| `topdesk_get_available_escalation_reasons` | none | *"What escalation reasons are available?"* |
| `topdesk_get_available_deescalation_reasons` | none | *"Show de-escalation options"* |

## 📎 Attachments & Comprehensive Data (4 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_progress_trail` | `incident_id`, `inlineimages=true` | *"Show progress history with images"* |
| `topdesk_get_incident_attachments` | `incident_id` | *"Get all files for incident I-240101-001"* |
| `topdesk_get_incident_attachments_as_markdown` | `incident_id` | *"Convert attachments to readable text"* |
| `topdesk_get_complete_incident_overview` | `incident_id` | *"Give me everything about incident I-240101-001"* |

## 👥 Person Management (5 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_person_by_query` | `query` | *"Find users with email containing '@company.com'"* |
| `topdesk_get_person` | `person_id` | *"Get details for person 12345"* |
| `topdesk_create_person` | `person_data` | *"Create user John Smith with email john@company.com"* |
| `topdesk_update_person` | `person_id`, `person_data` | *"Update person 12345 with new email"* |
| `topdesk_archive_person` | `person_id` | *"Archive person 12345"* |
| `topdesk_unarchive_person` | `person_id` | *"Reactivate person 12345"* |

## 👨‍💼 Operator Management (3 tools)

| Tool | Parameters | Quick Prompt Example |
|------|------------|---------------------|
| `topdesk_get_operators_by_fiql_query` | `query` | *"Find operators in Network support group"* |
| `topdesk_get_operator` | `operator_id` | *"Get operator 12345 details"* |
| `topdesk_get_operatorgroups_of_operator` | `operator_id`, `query` | *"What groups is operator 12345 in?"* |

## 🚀 Common FIQL Query Patterns

| Use Case | FIQL Example | Natural Language Prompt |
|----------|--------------|-------------------------|
| **Recent incidents** | `creationDate=ge=2024-03-01T00:00:00Z` | *"Find incidents created after March 1st, 2024"* |
| **Specific caller** | `caller.email=='john@company.com'` | *"Get all incidents from john@company.com"* |
| **Priority filter** | `priority.name=in=(High,Critical)` | *"Show high and critical priority incidents"* |
| **Status filter** | `status!=Closed` | *"Find all open incidents"* |
| **Multiple conditions** | `status=secondLine;priority.name=High` | *"Find second line incidents with high priority"* |
| **Date range** | `creationDate=ge=2024-03-01T00:00:00Z;creationDate=le=2024-03-31T23:59:59Z` | *"Find incidents created in March 2024"* |
| **Text search** | `briefDescription=sw='Email'` | *"Find incidents with titles starting with 'Email'"* |
| **Operator filter** | `operator.name=='Jane Smith'` | *"Show incidents assigned to Jane Smith"* |
| **Group filter** | `operatorGroup.name=in=(IT,Network)` | *"Find incidents assigned to IT or Network teams"* |

## 💡 Quick Tips

### Getting Started
1. **Start with discovery**: `"What tools are available?"`
2. **Learn FIQL**: `"Show me FIQL query syntax"`
3. **Test simple search**: `"Search for email problems"`

### Common Workflows
- **Investigation**: `"Get complete overview of incident I-240101-001"`
- **Update**: `"Add comment and log 30 minutes on incident I-240101-001"`
- **Search**: `"Find high priority incidents from this week assigned to Network team"`

### Best Practices
- Always specify incident IDs clearly (I-xxxxxx-xxx or UUID)
- Use `max_results` parameter to limit search results
- Combine related operations in single requests
- Use `concise=true` for faster incident retrieval

### Error Prevention
- Check incident ID format before querying
- Use simple searches before complex FIQL queries
- Verify person/operator IDs exist before creating incidents
- Test FIQL queries with small date ranges first

## 🆘 Quick Troubleshooting

| Error | Quick Fix |
|-------|-----------|
| *"Incident ID must be provided"* | Use format I-240101-001 or full UUID |
| *"FIQL query must be provided"* | Check query syntax with `topdesk_get_fiql_query_howto` |
| *"Caller ID must be provided"* | Find person ID first with `topdesk_get_person_by_query` |
| *No results returned* | Broaden search criteria or check date formats |

---

📖 **For detailed explanations and advanced examples, see the complete [MCP_TOOLING_GUIDE.md](MCP_TOOLING_GUIDE.md)**