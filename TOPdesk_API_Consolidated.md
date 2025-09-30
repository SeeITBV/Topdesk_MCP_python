# TOPdesk API — General, Incident & Change (Consolidated)
_Last updated: 2025-09-30_

> **Scope**: This document consolidates the official TOPdesk API information for the **General**, **Incident Management**, and **Change Management** APIs. It provides: base URLs, authentication & headers, versioning, pagination & sorting, endpoint overviews, key request/response fields, and concrete request examples. For full machine‑readable specs, see the official Swagger/OpenAPI files referenced inline.

---

## 1) Getting Started

### 1.1 Base URL & Format
- **Base**: `https://<YOUR_TOPDESK_URL>/tas/api/`  
- **Protocol**: HTTPS, REST, JSON
- **Content Types**: `application/json` (most), file endpoints may need `multipart/form-data`

### 1.2 Authentication
- Typically **Bearer token** or **API Key** via the `Authorization` or `Api-Key` header.
- Example: `Authorization: Bearer <token>`

### 1.3 Required Headers
- `Accept: application/json`
- `Content-Type: application/json`
- Some endpoints require **specific `Accept` headers** to opt‑in to newer versions (see “Supporting Files” notes).

### 1.4 Versioning & Docs
- Public documentation & interactive explorer: `https://developers.topdesk.com/explorer/`  
- Machine‑readable OpenAPI/Swagger specs (examples):
  - **General**: `.../swagger/general_specification_1.1.0.yaml`
  - **Incident**: `.../swagger/incident_specification_3.9.0.yaml` (also 3.8.x, 3.7.x available)
  - **Change**: `.../swagger/change_specification_1.24.0.yaml`

> URLs above are examples; use the latest available version in production.

---

## 2) Common Patterns

### 2.1 Pagination
Many list endpoints implement pagination via query params (commonly `pageSize`, `pageStart`, or `{limit, offset}`). Default and maximum values depend on the endpoint/spec version.

### 2.2 Sorting
- Many “list” endpoints support `sort=` on one or multiple fields.
- Incidents: for best performance, sort by **one** of: `callDate`, `creationDate`, `modificationDate`, `targetDate`, `closedDate`, or `id`.
- Syntax examples:
  - `sort=creationDate:desc`
  - `sort=parent.name:asc,name:desc` (multi-column sort where supported)

### 2.3 Filtering
- Endpoints may support FIQL‑style filters (e.g., assets & operations), or standard field filters as query params (e.g., status, priority). Check each path in its spec.

### 2.4 Attachments
- Attachment endpoints usually use a dedicated subresource, with `GET` (list/download) and `POST` (upload). Uploads typically require `multipart/form-data` with file payload.

### 2.5 Rate Limiting & Performance
- Prefer server‑indexed fields for sorting and filtering (see Incident sorting advice above).
- Fetch only needed fields where endpoints support sparse fieldsets or projections.

---

## 3) General API

**Spec (example):** `general_specification_1.1.0.yaml`  
**Explorer page:** “General”

### 3.1 Typical Capabilities
- Version/status & service windows
- Reference/metadata lookups (statuses, categories, priorities, etc.)
- Mail endpoint(s): e.g., get details of email by id (for incidents, changes, activities)

> Consult the spec for concrete paths. Below is a representative pattern; actual paths and exact names depend on the running version of TOPdesk and the selected spec revision.

#### Endpoint Patterns (non‑exhaustive)
- `GET /version` — API version / build info
- `GET /serviceWindows` — list service windows (supports `name`, `archived`, paging/sort where available)
- `GET /mail/{id}` — retrieve a mail object by ID (where provided)
- `GET /.../metadata` — reference lists (categories, statuses, etc.)

---

## 4) Incident Management API

**Spec (examples):** `incident_specification_3.9.0.yaml` (also 3.8.x/3.7.x)  
**Explorer page:** “Incident Management”

### 4.1 Core Resources & Paths (typical)
- **Incidents**
  - `GET /incidents` — list/search incidents (supports pagination, `sort`, filters)
  - `POST /incidents` — create incident
  - `GET /incidents/{id}` — retrieve incident by ID
  - `PATCH /incidents/{id}` — partial update
  - `PUT /incidents/{id}` — full update (if supported)
  - `DELETE /incidents/{id}` — delete/archive (if supported)

- **Notes & Worklogs**
  - `GET /incidents/{id}/notes`
  - `POST /incidents/{id}/notes`

- **Attachments**
  - `GET /incidents/{id}/attachments`
  - `POST /incidents/{id}/attachments` (multipart upload)

- **Relationships / Additional**
  - `GET /incidents/number/{callNumber}` — fetch by human‑readable number (if available)
  - `GET /incidents/{id}/links` — related objects (problems/changes/assets), depending on spec
  - `POST /incidents/{id}/operator` — assign operator (where provided)
  - Category/priority/status dictionaries are usually provided via general or incident‑specific endpoints

> **Sorting (performance)**: Prefer a single field and use indexed date fields like `creationDate` or `modificationDate` for large result sets.

### 4.2 Key Fields (typical incident object)
- Identification: `id`, `number`, `externalNumber`
- People: `caller` / `requester`, `operator`, `branch`, `department`, `budgetHolder`
- Classification: `category`, `subcategory`, `impact`, `urgency`, `priority`
- Status & Lifecycle: `status/state`, `creationDate`, `callDate`, `modificationDate`, `targetDate`, `closedDate`
- Content: `briefDescription` / `title`, `request` / `description`, `action`, `workNotes`
- Links: `attachments`, `assets`, `relatedProblems`, `relatedChanges`

### 4.3 Examples

**Create an incident**
```http
POST /tas/api/incidents
Content-Type: application/json
Authorization: Bearer <token>

{
  "briefDescription": "User cannot print from workstation 42",
  "request": "Print spooler error 0x00000bc4 when printing PDF",
  "caller": { "id": "<personId>" },
  "category": { "name": "Hardware" },
  "subcategory": { "name": "Printer" },
  "impact": { "name": "Low" },
  "urgency": { "name": "Medium" },
  "priority": { "name": "3" }
}
```

**List incidents (recent, paged, sorted)**
```http
GET /tas/api/incidents?pageSize=100&pageStart=0&sort=modificationDate:desc
Accept: application/json
Authorization: Bearer <token>
```

**Add note**
```http
POST /tas/api/incidents/{id}/notes
Content-Type: application/json

{ "note": "Restarted print spooler service; monitoring." }
```

**Upload attachment**
```http
POST /tas/api/incidents/{id}/attachments
Content-Type: multipart/form-data; boundary=----X

------X
Content-Disposition: form-data; name="file"; filename="screenshot.png"
Content-Type: image/png

...binary...
------X--
```

---

## 5) Change Management API

**Spec (example):** `change_specification_1.24.0.yaml`  
**Explorer page:** “Change Management”

### 5.1 Core Resources & Paths (typical)
- **End‑user (Self‑Service) changes**
  - `GET /changes` — list/filter visible changes for the user (visibility depends on permissions/module settings)
  - `GET /changes/{id}` — details of a change by ID (requester/manager visibility rules apply)
  - `POST /changes` — create change (may require a **template** and optional activities)

- **Operator changes**
  - `GET /operatorChanges`
  - `GET /operatorChanges/{id}`
  - `POST /operatorChanges` — create a change as operator (commonly used for integrations)
  - `PATCH /operatorChanges/{id}` — update operator change
  - `DELETE /operatorChanges/{id}` — cancel/remove

- **Activities / Tasks**
  - `GET /changes/{id}/activities` or `/tasks` (name varies by spec section)
  - `POST /changes/{id}/activities` — add tasks/activities (optionally based on template options)
  - `PATCH /changes/{changeId}/activities/{activityId}` — update
  - `POST /changes/{id}/approvals` — approval steps (where applicable)

- **Attachments**
  - `GET /changes/{id}/attachments`
  - `POST /changes/{id}/attachments`

> **Visibility & Permissions**: Detailed access rules (e.g., visible to requester, manager, same branch/department/budget holder) influence which `GET` endpoints return data for the current user.

### 5.2 Key Fields (typical change object)
- Identification: `id`, `number`
- Core: `briefDescription` / `title`, `request` / `description`
- People: `requester`, `changeManager`, `budgetHolder`, `branch`, `department`
- Planning: `plannedStart`, `plannedEnd`, `actualStart`, `actualEnd`
- Classification: `category`, `type`, `priority`, `impact`
- Lifecycle: `status/state`, `creationDate`, `modificationDate`, `closedDate`
- Structure: `template`, `activities` (tasks), `approvals`
- Links: `attachments`, related incidents/problems/assets

### 5.3 Examples

**Create operator change from template with optional activities**
```http
POST /tas/api/operatorChanges
Content-Type: application/json

{
  "template": { "id": "<templateId>" },
  "briefDescription": "Upgrade print server to v2025.3",
  "request": "Planned upgrade incl. driver package and test prints",
  "plannedStart": "2025-10-10T20:00:00Z",
  "plannedEnd": "2025-10-10T22:00:00Z",
  "activities": [
    { "name": "Pre‑checks", "description": "Check backups & free disk space" },
    { "name": "Install", "description": "Apply update packages" },
    { "name": "Verification", "description": "Test pages from 3 clients" }
  ]
}
```

**List operator changes (paged, sorted)**
```http
GET /tas/api/operatorChanges?pageSize=100&pageStart=0&sort=modificationDate:desc
Accept: application/json
Authorization: Bearer <token>
```

**Add approval step**
```http
POST /tas/api/changes/{id}/approvals
Content-Type: application/json

{ "decision": "APPROVE", "comment": "Go ahead during Friday maintenance window." }
```

---

## 6) Headers for Newer Endpoint Versions
Some components (e.g., “Supporting Files”, “Operations”) require a **specific `Accept` header** to use the newest version of endpoints. If you omit it, an older version may be used by default. Always check the explorer/spec for the component you’re using and include the `Accept` it lists.

Example:
```
Accept: application/json; version=1
```

---

## 7) Practical Tips & Conventions
- Use the **latest spec** versions compatible with your environment.
- Prefer **indexed date fields** for sorting large datasets (incidents).
- Keep payloads minimal; only send/expect necessary fields.
- For **file uploads**, ensure `multipart/form-data` and correct form part name (`file`).
- Respect **visibility rules** (end‑user vs operator endpoints) for changes.
- Be mindful of upcoming spec changes (e.g., mandatory fields in future releases).

---

## 8) References (Official)
- API Explorer (component pages): General, Incident Management, Change Management
- Swagger/OpenAPI specs (examples):
  - `.../swagger/general_specification_1.1.0.yaml`
  - `.../swagger/incident_specification_3.9.0.yaml`
  - `.../swagger/change_specification_1.24.0.yaml`
- TOPdesk docs on API access, working with API, URL & headers, and example sequences.

> This document is a consolidated quick‑reference. For authoritative parameter/field lists and response schemas, consult the referenced Swagger files for your exact version.
