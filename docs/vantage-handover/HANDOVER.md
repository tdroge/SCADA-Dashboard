# TGW Project Vantage technical handover

Prepared 10 November 2026 from the working SCADA dashboard and the separate Mission Ctrl Viewer.

## Scope and evidence

The original SCADA dashboard implements a user-authenticated Jira integration for PLC epics, linked work issues, subtasks, and a separately scoped support queue. Mission Ctrl Viewer supplies reusable searches, configurable dates, saved workspaces, and display panels. Neither application currently discovers every approved TGW project or maintains a versioned department checklist registry. Future-project discovery, TGW identity resolution, checklist applicability, and the Jira-to-GMR-to-Vantage path require additional implementation.

Evidence labels are **I** for implemented code, **T** for an executed automated test using simulated Jira, **L** for live read-only observation, **H** for historical browser evidence recorded in the build conversation, **P** for proposed design, and **GAP** for unconfirmed or unbuilt capability. A simulated test establishes client behavior under its fixture. It does not establish every production workflow, permission, or template.

The live observation covers **2026-11-10 19:25:25.378690 through 19:25:58.621576 UTC**, equivalent to **14:25:25 through 14:25:58 America/New_York**. Relevant project, epic, linked-issue and subtask reads were repeated and compared identically. This is a stable observation window. The collector does not freeze Jira or reconstruct historical state at a single instant.

Credentials, instance URL, user identities, customer/project names, and issue keys are replaced by placeholders or aliases in the examples and evidence. Technical field IDs and classification strings are retained for implementation reuse.

### Revisions and integrity

| Component | Revision and state | Evidence |
|---|---|---|
| Original SCADA application | Mission Ctrl 1.3.1, revision c8d6221318f7fd7917ec76cf92fe3c91638f668d in Zimlichg/Mission-Ctrl | All 27 deployed release files matched the available 1.3.1 release ZIP byte for byte. Inspected source matched committed content after line-ending normalization. |
| General Viewer | Mission Ctrl Viewer 1.2.1, revision 0193ab7abb80b3c90e5c42e9425c250bfe0b40c0 in Zimlichg/Mission-Ctrl-Viewer | Local worktree clean when provenance was recorded. |
| Original tests rerun for handover | 134 passed, runner reported 5.080 seconds | Simulated Jira and isolated test storage. No real Jira transition executed. |
| Viewer tests rerun for handover | 14 passed, runner reported 0.153 seconds | Simulated account, pagination, field, and query cases. |
| Live reconciliation | 223 matching epics across 14 returned Jira projects. PROJECT-A contained 16 matching assigned epics, 12 completed. | Selected PLC had one linked work source reporting 100%, with eight completed leaves out of eight. |
| Historical browser evidence | Workspaces/presets, both MS dates, dashboard layouts, completed filtering, saved-account reconnect, responsive display and refresh/error retention | H evidence. Previous scripts/screenshots exist in ignored local runtime folders. These browser runs were not all repeated for this handover. |

The accompanying source-and-test-evidence.json records revisions and deployed-source hashes. Nineteen text files differ bytewise from Git because of Windows line endings. There are no normalized source differences and no byte differences against the deployed ZIP.

Pinned repositories require repository access. The approved workspace holds scada-plc-dashboard, its Mission-Ctrl-publish publishing clone, and the separate Mission-Ctrl-Viewer folder. [SCADA revision](https://github.com/Zimlichg/Mission-Ctrl/tree/c8d6221318f7fd7917ec76cf92fe3c91638f668d), [Viewer revision](https://github.com/Zimlichg/Mission-Ctrl-Viewer/tree/0193ab7abb80b3c90e5c42e9425c250bfe0b40c0)

## 1. Setup and working integration

### Short setup guide

1. Obtain the approved release ZIP and extract it into a permanent folder.
2. Install Python 3.10 or newer on Windows. Both current applications use the Python standard library. The requests, pygame, and pillow dependencies belonged to an earlier watcher.
3. Use a current Edge or Chrome browser. Viewer uses modern features including native dialogs, Object.hasOwn, local storage, and SVG.
4. Run Start Dashboard.cmd for SCADA on 127.0.0.1:8765, or Start Viewer.cmd for Viewer on 127.0.0.1:8766.
5. Connect with the intended user's Jira personal access token. Use the placeholder JIRA_PAT in documents. Keep real credentials out of presets, repositories, command arguments, and evidence.
6. For SCADA, config.local.json overrides config.default.json. Configuration is loaded when the server starts. Reopening a browser page or reusing a running launch process does not reload it.
7. In Viewer, create/import a workspace and preview the search. Configure main/end and start dates, save the workspace, then add it to the Dashboard. Search and display settings can be applied through the UI.
8. Verify the reader's project and issue visibility before interpreting zero matches as complete coverage.

Original credentials use Windows current-user encryption under %LOCALAPPDATA%/JiraStinks/account.dat. Viewer uses a separate %LOCALAPPDATA%/MissionCtrlViewer/account.dat. Original personal notes/taskbars also live under its local profile. Viewer workspace and dashboard settings live in browser local storage, scoped by origin. Exported presets carry filter and display configuration.

Both apps are local processes with one Jira account per app/Windows profile. They do not provide a hosted multi-user service or central observation store. Viewer prevents a second server binding to the same port. Original process-start behavior needs review before reuse as a service. [Original account storage](https://github.com/Zimlichg/Mission-Ctrl/blob/c8d6221318f7fd7917ec76cf92fe3c91638f668d/account_store.py), [original launcher](https://github.com/Zimlichg/Mission-Ctrl/blob/c8d6221318f7fd7917ec76cf92fe3c91638f668d/start_dashboard.py), [Viewer account/server](https://github.com/Zimlichg/Mission-Ctrl-Viewer/blob/0193ab7abb80b3c90e5c42e9425c250bfe0b40c0/server.py)

### Instance and read permissions

The live ServerInfo probe reported **deploymentType Server** and **Jira version 10.3.26**. The apps target a self-hosted Jira REST v2 origin using bearer PAT authentication. Licensing/cluster topology was not audited, so Data Center edition and load-balancer topology must be confirmed with the Jira owner. A Cloud deployment would need independent authentication, API and field validation.

The approved integration reader needs application access, Browse Projects coverage for all approved projects, and visibility of relevant secured issues, custom fields, linked work issues, and subtasks. Jira enumeration is permission-filtered. The supplied principal successfully read the sampled records, but its complete permission scheme and least-privilege status were not audited. A future project's permission scheme must include the integration reader. Project listing is proposed discovery behavior and is absent from both current collectors. [Jira Data Center project API](https://developer.atlassian.com/server/jira/platform/rest/v10004/api-group-project/)

The original app can execute workflow writes. Vantage should reuse read helpers through an explicit read allowlist and an approved read identity. Application endpoint selection does not reduce a token's underlying permissions.

### Endpoints actually used

All source paths are relative to the approved JIRA_BASE_URL followed by /rest/api/2/.

| Method and endpoint | Original SCADA use | Viewer use |
|---|---|---|
| GET myself | Validate account and obtain identity | Validate account |
| GET field | Discover Epic Link schema, Flagged field and optional MS End field | Discover custom date fields |
| GET priority | Support priority ordering | Generic priority ordering |
| POST search | Main epics, linked work issues, batched subtasks, scope checks and support | Workspace preview/apply and dashboard searches |
| GET issue/{key} | Hierarchy, direct subtasks and workflow verification | Cards open the Jira UI. Collector does not use this endpoint. |
| GET issue/{key}/transitions?expand=transitions.fields | Discover available transitions and required fields | Absent |
| POST issue/{key}/transitions | User-confirmed complete/reopen/To Do/In Progress actions | Absent |
| GET serverInfo | Handover collector only | Handover collector only |

POST search is a read operation. Neither application implements an Agile board/sprint collector, checklist-plugin API reader, LMS connector, GMR connector, or Vantage connector.

The browser calls local APIs. Original /api/state and /api/epic/{key} expose collected data and details. Original /api/plan and /api/execute drive explicit writes. Viewer uses /api/session, /api/connect, /api/search, /api/dates and /api/priorities. Its POST handlers require loopback Host, matching Origin, JSON content type and a custom header. Original write operations also require a CSRF token. These local controls do not replace enterprise service authentication.

### Existing configured scope

The original configuration has **14 literal project keys and four literal assignee identifiers**, plus unassigned work. Deployment values remain in config.default.json and its optional local override. Their sanitized form is shown below.

~~~jql
project in (<PROJECT_KEY_01>, ..., <PROJECT_KEY_14>)
AND issuetype = Epic
AND (text ~ "*SAV*" OR text ~ "*SCADA*")
AND (
  assignee = "<JIRA_USER_A>"
  OR assignee = "<JIRA_USER_B>"
  OR assignee = "<JIRA_USER_C>"
  OR assignee = "<JIRA_USER_D>"
  OR assignee is EMPTY
)
~~~

Original Jira.search adds ORDER BY key ASC when sorting is absent. Support uses one configured support_epic with a hardcoded default key. Its sanitized query is "Epic Link" = "SUPPORT_EPIC_KEY". No default main-query label clause exists. SCADA_Project_Task is used later as a child-source fallback. NA_SWEC-STS appeared in a supplied Jira screenshot, but is not a default scope or template-version rule.

Viewer builds JQL from projects, issue types, statuses, assignees, a summary keyword and completion settings, or accepts Advanced JQL. Explicit project lists remain explicit. Panel-wide completed exclusion wraps the workspace condition and adds statusCategory != Done before sorting.

### Sanitized request-to-display trace

The following represents the observed shape and values with alias IDs. It is illustrative, not a directly runnable production request.

~~~json
{
  "endpoint": "POST <JIRA_BASE_URL>/rest/api/2/search",
  "headers": {"Authorization": "Bearer <JIRA_PAT>"},
  "body": {
    "jql": "(<APPROVED_SCADA_SCOPE>) AND project = \"PROJECT_A\" ORDER BY key ASC",
    "fields": ["summary", "status", "resolution", "assignee", "project",
               "updated", "duedate", "customfield_10210",
               "customfield_10101", "issuetype", "customfield_14701"],
    "startAt": 0,
    "maxResults": 100
  }
}
~~~

Original normalize(issue, ms_end_field) converts the epic into dashboard state. In the sampled epic, status.name was Done, statusCategory.key was done, and a resolution was present. The legacy done() predicate returned true. MS End-Date was 2026-05-08.

A subsequent Epic Link search returned one selected SCADA work issue. Its numeric customfield_10210 value was 100. attach_completion() set jiraProgress to 100, progressState to reported, and retained its source in progressSources. jiraPercentChip() displays 100% with source provenance in its tooltip. The running collector separately stamps progressLastSync after a successful lookup.

Dashboard.tree() reads linked work issues and referenced subtasks. The sampled hierarchy contained eight completed leaves out of eight, producing a separate displayed leaf ratio of 100%. The project contained 12 completed epics out of 16, producing a delivery ratio of 75%. Agreement between two 100% values does not prove the Jira scripted-field formula.

~~~mermaid
flowchart LR
    J[Jira source records] --> R[Read API and pagination]
    R --> E[Epic normalization]
    R --> W[Linked work source selection]
    W --> P[Reported percentage]
    R --> S[Subtask hierarchy and leaf count]
    E --> UI[SCADA dashboard]
    P --> UI
    S --> UI
    R --> V[Viewer issue cards and panels]
~~~

### Reusable code references

| Behavior | File and functions at pinned revision | Evidence |
|---|---|---|
| HTTP, authentication and errors | Original server.py, Jira.request, lines 235–261 | I, T, L |
| Original complete pagination | Original server.py, Jira.search, lines 263–283 | I, T, L |
| Completion predicate and normalization | Original server.py, done, schedule_date, normalize, lines 297 and 386–409 | I, T, L |
| Percentage source selection | Original server.py, completion_value, attach_completion, lines 412–424 | I, T, L |
| Metadata and collection | Original server.py, Dashboard.setup, refresh, load_completion, lines 455–590 | I, T, L |
| Hierarchy and item counts | Original server.py, scope_check, tree, lines 772–818 | I, T, L for equivalent sampled traversal |
| Support classification | Original server.py, refresh_support, lines 592–623 | I, T |
| Planned writes and partial results | Original server.py, plan, execute, run_job, lines 820–984 | I, T, historical live trials |
| State and polling | Original server.py, bootstrap, poll, Handler | I, T |
| Displayed ratios and dates | Original public/app.js, jiraPercent, plcInProgress, scope, deadlineGroup, renderOverview, renderDetail | I, T/H according to behavior |
| TV refresh/carousel/staleness | Original public/tv.js, syncLabel and timer | I, H |
| General paging/exclusion | Viewer server.py, ordered_search, open_issues_query, search_issues, search_pages | I, T, H/L from previous live use |
| Configurable date payload | Viewer server.py, issue_card, jira_metadata, Handler.do_POST | I, T, H |
| Saved scope and display | Viewer public/app.js, normalizeWorkspace, jqlFor, search, compareIssues, restoreSession | I, T/H |
| Shared panel queries and stale data | Viewer public/dashboard.js, sourceKey, refresh, panelCard, peopleLayout | I, H |
| Encrypted credentials | Each account_store.py, protect, CredentialStore | I, T/H |

The approved source folders hold the latest inspected code. Pinned repository links are portable references. [Original server](https://github.com/Zimlichg/Mission-Ctrl/blob/c8d6221318f7fd7917ec76cf92fe3c91638f668d/server.py), [original UI](https://github.com/Zimlichg/Mission-Ctrl/blob/c8d6221318f7fd7917ec76cf92fe3c91638f668d/public/app.js), [Viewer server](https://github.com/Zimlichg/Mission-Ctrl-Viewer/blob/0193ab7abb80b3c90e5c42e9425c250bfe0b40c0/server.py), [Viewer dashboard](https://github.com/Zimlichg/Mission-Ctrl-Viewer/blob/0193ab7abb80b3c90e5c42e9425c250bfe0b40c0/public/dashboard.js)

## 2. Project identity and discovery

### Current identifiers and coverage

Jira returns project.id/key/name and issue id/key. Current normalizers retain project key/name and issue key, discarding numeric IDs. Jira key/display-name patterns resemble TGW project numbering, but the code implements no TGW ID parser, approved-project join, or uniqueness validation.

Many PLC epics can belong to one Jira project. Each epic can have several linked issues with subtasks. This supports the known SCADA structure. There is no registry determining other departments' checklist ownership, expected instances, phases, or template versions.

A shared Jira project containing several TGW projects requires an issue-level TGW reference or an approved root-level crosswalk. Descendants can inherit it only through validated parent relationships. Jira project identity alone does not distinguish those TGW projects.

| Existing fixed dependency | Consequence |
|---|---|
| Four assignees and 14 project keys | Newly created projects outside the list are not discovered by the original application. Other assignees are excluded unless unassigned. |
| Main Epic type and SAV/SCADA text condition | Other department types/markers require scope changes. |
| SCADA child-source heuristic | Department/template recognition is not generalized. |
| Fixed percentage and Epic Status IDs | IDs need validation on another Jira instance. |
| Epic Link fallback | Metadata discovery reduces the dependency, but does not prove compatibility with every Jira hierarchy. |
| Default support epic | No automatic per-TGW-project support partition exists. |
| Viewer fixed Jira origin | Other teams on this instance can configure workspaces. Another Jira site requires adaptation and validation. |
| Browser-local workspaces | Presets can be shared, but there is no central governed rule registry. |
| Viewer cap of 300 loaded issues | Large panels can show a subset and cannot prove complete approved-project coverage. |

There are no hardcoded Agile board IDs. A genuinely dynamic saved query could match future projects if an approved searchable criterion exists. Neither app establishes or validates that criterion.

### Proposed reusable future-project rule

**P, requires build and owner approval.** An authoritative approved-project inventory must supply the approved TGW ID, a validated association to Jira IDs, project class/phase, and applicable departments. A governed Jira project category could supply part of this signal if its meaning is confirmed. Visibility alone is insufficient proof of approval.

1. Read the approved inventory periodically and enumerate visible Jira projects through the approved reader.
2. Join approved tgw_project_id to jira_site_id plus project.id. Retain key/name as reference attributes.
3. For shared Jira projects, validate an explicit TGW reference on each checklist root.
4. Match class, phase and department to versioned template rules.
5. Read expected checklist roots/items through the configured adapter.
6. Publish observations with source IDs, rule version, instance identity and timestamps. Route missing, ambiguous, unversioned and unmapped instances to review.

When a newly approved project record matches an existing rule, discovery selects the same template without editing a project-key array or writing a project-specific branch. The approval record remains a governed data change. Missing identities or department/version markers require onboarding review.

Vantage can generate expected-checklist entries in its read model and mark missing source records. Creating/cloning Jira tasks would require a separately approved write workflow. The proposed discovery path reads existing records.

The supplied simulation places two TGW projects inside the same Jira project ID and distinguishes roots through tgw_ref. The simulated property names are conceptual contract fields, not verified Jira or GMR fields.

## 3. Department checklist inventory

| Checklist/source | Where it lives and how identified | Template/version and applicability | Item reading and limits |
|---|---|---|---|
| SCADA PLC work | Matching Epic, linked work issue, then subtasks | Live clone reference present. No immutable version or approved phase rule implemented. Limited by current SCADA scope. | tree() reads individual issues/subtasks. Live sample has one work source and eight leaves. Required/optional/exclusion policy is absent. |
| SCADA support | Issues linked to the configured support epic, all assignees | Operational ticket stream. No verified project checklist template/version. | Priority, blocked hint and closed state are computed per issue. |
| Smart Checklist widget | Appears in user-supplied Jira screens | No plugin API/field parser/version contract in the collector. | Widget lines/items are not demonstrated as source records. |
| Network, Tech Leads, other departments | No actual template inventory or approved sample search supplied | GAP. Need representative root/item records, working search, owner/version, phase/applicability and state semantics. | Generic cards can display matching issues. Departmental checklist interpretation is unverified. |
| NETWORK-DEMO-V2 | Invented roots/items in rule-examples.json | Simulation uses version 2 and invented marker/class/phase. | Demonstrates a different checklist and counting policy only. |

### Current item and completion semantics

- Legacy done means status category done and a nonempty resolution. The read predicate accepts any resolution, including a cancellation-style resolution if Jira supplies one.
- Each returned leaf contributes one denominator item. A work issue with subtasks contributes its subtasks. A work issue without subtasks contributes itself.
- Requiredness and optionality are not read. Skipped and not-applicable roles receive no denominator exclusion.
- An open blocked item remains incomplete. Generic checklist blocked counting is absent. Support has a separate Flagged/status heuristic.
- Multiple selected percentage sources produce Multi with source details. They are not averaged.
- For zero detail leaves, the original UI falls back to 100% if the epic is done and 0% otherwise. That fallback does not establish a valid checklist denominator.
- Original frontend state.phase is a local status-display filter, not a TGW lifecycle phase.

### Proposed department and template onboarding

A configuration record needs department ID, immutable template ID/version, source selector, item adapter, project-class/phase applicability, expected instance cardinality, requiredness policy, state mapping and exclusion policy. A clone-source link can help establish origin, but it does not prove a historical template version.

Define instance identity using TGW project, department, checklist type, instance ID, template version and phase. Keep each PLC instance distinct. Roll up only through an approved calculation.

Unknown selectors, multiple roots when one is expected, unknown versions, missing TGW references, or missing item-role/exclusion evidence should produce a review state and null completion. Current apps do not provide this enterprise review queue.

The **proposed** required-applicable ratio is completed required applicable items divided by all required applicable items. Optional work is separate. Approved skip/N/A dispositions are excluded only under a versioned policy with evidence. Unapproved dispositions produce review. Zero applicable denominator produces null with a no-applicable-items reason. This is a simulated policy awaiting TGW approval.

## 4. Reusable field and tag mapping

**mapping.csv is the complete 31-row mapping table.** Each row includes decision, department, checklist, field ID, record level, source/join key, calculation, numerator, denominator, exclusions, timestamp, validation and candidate GMR association.

| Rows | Input group | Source fields or gaps | Interpretation |
|---|---|---|---|
| M01–M03 | Project/record identity | project.id/key/name, issue id/key/issuetype, missing approved TGW crosswalk | Numeric IDs available in raw data are not retained in normalized payloads. |
| M04–M06 | Hierarchy and department | customfield_10100, subtasks, parent, summary, labels | Existing SCADA heuristic and traversal. No enterprise registry. |
| M07–M09 | Template/applicability | customfield_11501, customfield_11400, missing version/phase source | Clone metadata observed. Version/application enforcement requires build. |
| M10–M13 | Display and workflow | summary, description, assignee, status, resolution | Legacy and Viewer completion predicates differ. |
| M14–M18 | Completion | customfield_10210, customfield_10218, leaf counts and epic counts | Reported percentage, counted item ratio, and delivery ratio stay separate. |
| M19–M22 | Schedule/sort | customfield_14700, customfield_14701, duedate, created, updated | MS date-only fields are not source activity timestamps. |
| M23–M25 | Priority/blockers/support | priority, configured order, discovered Flagged, support Epic Link | Separate support logic is not a generic checklist model. |
| M26–M28 | Quality/scope | Collector timestamps, errors, filters, completed exclusion | Retain source scope and freshness with every observation. |
| M29 | Requiredness/exclusions | No explicit current item-role mapping | Policy and source evidence must be supplied. |
| M30 | LMS candidates | customfield_15704 LMS Creation Date, customfield_15303 LMS Completion Date | Metadata exists in Jira. LMS semantics, coverage and read path remain unconfirmed. |
| M31 | GMR/Vantage lineage | No connector or target schema | Candidate contract only. |

Live metadata identifies customfield_10210, % of completion, as a numeric **ScriptRunner scripted field**. customfield_10218, Progress Calculation, is an option field. A historical screenshot showed Subtask completion, but the actual script/configuration was not retrieved. The field's numerator, denominator, weighting, exclusions and evaluation timing remain unknown to the client.

### Candidate Jira-to-GMR-to-Vantage mapping

**P, no connector/schema is implemented.** After the GMR owner confirms its interface and ingestion/read responsibilities, associate source observations with an approved GMR representation. Vantage can then read that representation with the same identity and policy lineage.

~~~json
{
  "source_system": "jira",
  "source_site_id": "<APPROVED_SITE_ID>",
  "source_project_id": "<JIRA_PROJECT_ID>",
  "source_issue_id": "<JIRA_ISSUE_ID>",
  "source_issue_key": "<CURRENT_JIRA_KEY>",
  "tgw_project_id": "<APPROVED_TGW_ID>",
  "department_id": "<DEPARTMENT_ID>",
  "checklist_instance_id": "<STABLE_INSTANCE_ID>",
  "template_id": "<APPROVED_TEMPLATE>",
  "template_version": "<APPROVED_VERSION>",
  "phase": "<APPROVED_PHASE>",
  "measure": "leaf_count_ratio",
  "numerator": 8,
  "denominator": 8,
  "exclusions": [],
  "policy_version": "<COUNT_POLICY_VERSION>",
  "source_updated_at": "<SOURCE_TIMESTAMP_OR_NULL>",
  "collected_at": "<UTC_TIMESTAMP>",
  "quality": "verified_for_observation_window"
}
~~~

These are conceptual attributes, not asserted GMR tables/endpoints or approved policies. Jira-reported percentage needs a separate measure and explicit unresolved-formula provenance.

## 5. Execution and recovery

| Behavior | Original SCADA | Viewer |
|---|---|---|
| Collection cadence | poll() waits at least 15 seconds, normally configured 30 seconds, after each cycle finishes. Collection time adds to the interval. | Issue board searches are manually applied. Dashboard supports Off/30/60/120 seconds, default 60, with visibility/busy guards. |
| Browser refresh | State poll every 30 seconds and initial retry after 2.5 seconds. | Saved account restored on refresh. Selected workspace/panels can be loaded again. |
| Pagination | maxResults 100, offset pages until total, no application-wide result cap. Stable default key sort, overlap and changing-total checks. | Preview 8, applied 300. Also checks returned offset. Reported total can exceed loaded subset. |
| Batch reads | Percentage groups of 75 roots, maximum 3 concurrent workers. Detail subtasks in groups of 60. | Flat issues. No inherited SCADA source-percentage or hierarchy reader. |
| Retries | Failed percentage batches retry once. Main search retried on later poll. No automatic write replay. | One full-search retry for inconsistent/409 results. Cookie-aware opener keeps affinity cookies between pages within an attempt. |
| Request timeout | 30 seconds | 25 seconds |
| Cache | Main/progress/support in memory. Detail TTL 20 seconds. Lost on process restart. | Panel data in browser memory. Last good data retained on refresh error. Lost on page reload. |
| Independent failures | Parent list publishes before percentages finish. Support and percentage errors are separate. | Per-source panel error. Same filter/date/exclusion combination shared across panels during refresh. Two workers handle distinct sources. |
| Writes | Planned, user-confirmed and verified. Earlier successes remain saved after later failure. Uncertain writes are verified before retry decisions. | Read-only source collection and local display settings. |

For 223 epics, a normal original cycle has a conditional lower bound of three parent searches, three child-batch searches and one support search when each child batch/support queue fits one page. This is **at least seven search requests under those conditions**, not an observed normal-cycle count. Extra pages, retries, details and metadata increase it.

The handover reconciliation made **13 actual requests in 33.244 seconds**. The longest request took **8.630 seconds**. The mix was one ServerInfo, one identity, one metadata, eight search requests and two issue reads. These include repeated evidence reads and are not an ordinary-poll performance benchmark.

Stable sorting does not freeze result membership. Atlassian documents duplicate pages caused by changing results and by requests reaching different cluster nodes. Viewer preserves cookies across pages to support affinity and retains integrity checks. Actual index/load-balancer health remains an operations concern. [Atlassian pagination guidance](https://support.atlassian.com/jira/kb/inconsistent-paginated-api-search-result-while-using-jql/)

### Distinguishing result quality

| Condition | Current application signal | Vantage treatment needed |
|---|---|---|
| Valid reported zero | Finite numeric 0 accepted and displayed | Valid zero plus source/collection provenance |
| Missing percentage | Null, missing state, displayed dash | Missing-value reason |
| Multiple sources | Multi plus source list | Cardinality review, no silent averaging |
| First failed percentage read | Pending and delayed message | Unavailable with error class |
| Later failed percentage read | Prior value, Older badge and last successful lookup | Stale result with freshness metadata |
| No matched epics | Empty search or selected owner/project view | Distinguish valid empty scope, inaccessible source, missing expected checklist and unmapped project |
| No leaves | Legacy UI fallback 0% or 100% according to epic done | Approved no-applicable/missing semantics and null denominator |
| Unknown project/template | No enterprise review queue | Explicit identity/template review states |
| Done category without resolution | Legacy incomplete, Viewer completed exclusion removes it | Reconcile the two definitions under department policy |
| Authentication failure | Reconnect/error prompt | Unavailable authentication, separate from valid zero |

The original TV shows updates paused after errors or sufficiently old sync, with a minimum stale age of 90 seconds. Main-list freshness and percentage freshness differ. Viewer panels retain a last-success time and error when showing old data. Neither app provides a durable source cache, complete change history or enterprise freshness SLA.

Scale testing must include large/multi-page projects, missing/security-filtered records, metadata drift, moved/deleted items, source changes during paging, timeouts, concurrent consumers and long-running sessions. Vantage needs complete/partitioned collection instead of silently adopting a 300-result display limit.

## 6. Repeatable proof

### Live SCADA reconciliation

live-evidence.json contains the alias-based result. verify_scada_readonly.py reuses original Jira, normalize, done and attach_completion helpers. It reads the Viewer's own Windows credential, permits only identity/metadata/search/issue-read calls, and writes sanitized evidence. It does not start the dashboard poller or invoke transitions.

~~~powershell
py -B .\verify_scada_readonly.py --scada-root "<SCADA_SOURCE_FOLDER>" --project-key "<EXISTING_PROJECT_KEY>" --output .\new-live-evidence.json
~~~

Without project-key, the script chooses the returned project with the most matching epics. Selection can vary with current data. The helper operates within the existing original scope. Future onboarding is demonstrated separately through simulation.

| Level | Captured result | Reconciliation check |
|---|---|---|
| Main scope | 223 epics in 14 returned projects | Run effective original JQL under the same identity and restore all pages. |
| PROJECT-A | 16 matching assigned epics, 12 completed | Original assigned/project headline is 12/16, or 75%. |
| EPIC-A | Done with resolution | Verify both category and resolution. |
| WORK-A-1 | One selected work source, reported 100 | Verify source selection, Epic Link and numeric customfield_10210. Clone presence is not version proof. |
| ITEM-A-01 to ITEM-A-08 | Eight leaves, all Done with resolutions | Match each item's parent and workflow state. Alias details included in evidence. |
| Detail ratio | 8/8, displayed 100% | Recompute existing leaf rule. Keep reported percentage separate. |
| Timing | Repeated relevant reads identical | If records change, repeat or obtain an approved snapshot/history mechanism. |

For a browser comparison, capture selected owner/project/status filters, main lastSync, progressLastSync, source keys privately, and the evidence interval. The original dropdown lists any returned project, while Team overview includes assigned epics. A project can therefore be listed while an assigned-only view is empty.

### Existing regression proof

Run each command from its pinned source folder.

~~~powershell
# Original SCADA, simulated Jira
py -B -m unittest test_notes test_taskbar test_updates test_server test_reopen test_support test_progress test_accounts_completion test_partial_progress -q

# Viewer, simulated Jira
py -B -m unittest test_server -v

# Proposed discovery and item policy, simulation only
py -B .\verify_rule_examples.py
~~~

Original coverage includes paging, hierarchy validation, missing subtasks, child-first completion, partial success, required fields, ambiguous transitions, reopen comments, uncertain-write verification, MS End handling, source-percent ambiguity, zero/missing/stale distinctions, accounts and personal storage. Viewer coverage includes ordering, cookie-opener reuse, overlap/wrong offsets, both MS fields, pre-pagination exclusion and saved-account behavior.

### Previously unseen project and second department

**SIMULATION ONLY.** rule-examples.json contains invented class/phase/project/marker values. verify_rule_examples.py runs an illustrative approval join, template selection, cardinality checks and required-applicable counting. It has no Jira or GMR client.

| Case | Expected result |
|---|---|
| Existing approved TGW-A, SCADA-DEMO-V1 | 1/3, 33.333333%. One optional item is separate, two approved skip/N/A items excluded, one required item blocked. |
| Approved TGW-FUTURE-B with unchanged SCADA rule | Same rule automatically matches. 2/3, 66.666667%. No project-specific branch or rule edit. |
| TGW-FUTURE-B, NETWORK-DEMO-V2 | Different department/template/item set. 2/3, 66.666667%. Optional work separate. |
| Same Jira project ID for TGW-A and TGW-FUTURE-B | Explicit root tgw_ref prevents mixing. |
| Unapproved TGW-OUTSIDE | Excluded from expected-checklist discovery. |
| Missing or duplicate expected root | missing or ambiguous |
| Unknown marker or missing TGW reference | template_review or identity_review |
| Unknown version or unapproved skip/N/A | version_review or item_review |
| Zero applicable denominator | Null percentage |

The proof asserts that adding an approved project record leaves mapping rules unchanged. Production registry adapters, actual markers/fields, cardinality policy, review handling and departmental approval are still required.

### Jira-to-GMR-to-Vantage acceptance check

This path remains **unproven**. After GMR confirms the schema and approved read path, reconcile the same checklist observation across all three stages.

1. Capture Jira site/project/issue IDs, template/version, item IDs, timestamps and distinct measures.
2. Confirm source-to-GMR ingestion responsibility and permitted reader. Obtain record keys, lineage, receipt watermark, exclusion evidence and policy version.
3. Retrieve the corresponding GMR record through the approved path and match identity, observation/version, numerator, denominator, exclusions, state and timestamps.
4. Retrieve Vantage's result for that instance and declared cutoff. Verify the same GMR observation and policy, including missing/review/stale states.
5. Confirm deduplication across repeated collection and one intended result per observation/instance.
6. Repeat with a real newly approved project, a second department, and two TGW projects sharing one Jira project.

If GMR/Vantage cannot select the same observation or historical cutoff, label the result a bounded-window comparison with limitations.

## 7. Gaps, access needs and decisions before expansion

1. **Approved inventory and identity.** Name the authoritative source, TGW identifier, shared-project reference and source-ID crosswalk. Define how newly approved records trigger discovery.
2. **Future permission coverage.** Approve a reader and permission-scheme process that exposes all in-scope future projects and secured items. Add completeness/canary checks against the approval inventory.
3. **Department inventory.** Supply working queries and representative roots/items for every department, including owners, phases, cardinality and item roles.
4. **Versioned templates.** Establish immutable version evidence, drift/migration policy and review ownership. Current clone links and text are insufficient.
5. **Completion policy.** Approve required/optional, cancelled/skipped/N/A, blocked, weighting, roll-up and empty-denominator semantics. Obtain the ScriptRunner formula behind customfield_10210.
6. **Source contracts.** Validate field IDs/contexts, Epic Link, account identities, dates/timezones, issue security and any checklist-plugin API. Confirm PM-maintained schedules.
7. **LMS.** Identify decisions needing LMS data, its owner and approved read interface. Jira fields with LMS names do not establish complete LMS integration.
8. **GMR and Vantage.** Approve ingestion responsibility, target identities/schema, read endpoints/views, service access, provenance and reconciliation cutoff. No working connector currently exists.
9. **Enterprise collection/recovery.** Build dynamic discovery, complete collection, durable observations, retained IDs, mapping review, freshness policy, rate controls and capacity monitoring.
10. **Acceptance.** Assign sign-off owners and thresholds. Execute real future-project onboarding, second-department checklist validation and full Jira/GMR/Vantage reconciliation. Current proof covers one live SCADA project, client regression suites and labelled simulations.
