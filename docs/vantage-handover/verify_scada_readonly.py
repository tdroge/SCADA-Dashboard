"""Reconcile one SCADA project's current records using the existing read helpers.

Uses the Viewer's saved Windows credential. Writes a sanitized evidence file only.
It cannot call Jira transition endpoints or create/change Jira records.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlsplit


def stamp():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scada-root", type=Path, required=True)
    parser.add_argument("--project-key", help="An existing project key already inside the SCADA filter.")
    parser.add_argument("--output", type=Path, default=Path("live-evidence.json"))
    args = parser.parse_args()
    root = args.scada_root.resolve()
    sys.path.insert(0, str(root))
    from server import Jira, attach_completion, done, load_config, normalize
    from account_store import CredentialStore

    started = stamp()
    timer = time.monotonic()
    calls = Counter()
    durations = []

    class ReadOnlyJira(Jira):
        def request(self, path, data=None):
            allowed = path in {"myself", "field", "serverInfo"} and data is None
            allowed = allowed or (path == "search" and isinstance(data, dict))
            allowed = allowed or (re.fullmatch(r"issue/[A-Z][A-Z0-9_]*-\d+", path) and data is None)
            if not allowed:
                raise RuntimeError("The evidence collector permits read operations only.")
            label = "issue/{key}" if path.startswith("issue/") else path
            calls[label] += 1
            begin = time.monotonic()
            try:
                return super().request(path, data)
            finally:
                durations.append(time.monotonic() - begin)

    credential_file = Path(os.environ["LOCALAPPDATA"]) / "MissionCtrlViewer" / "account.dat"
    record = CredentialStore(credential_file).load()
    if not record:
        raise SystemExit("Connect the Viewer to Jira once before running this collector.")
    config = load_config()
    if urlsplit(config["jira_url"]).scheme != "https":
        raise SystemExit("Use the approved HTTPS Jira origin before collecting evidence.")
    config["jira_token"] = record["token"]
    jira = ReadOnlyJira(config)
    instance = jira.request("serverInfo")
    jira.request("myself")
    fields = jira.request("field")
    epic_link = next(
        (field["id"] for field in fields if (field.get("schema") or {}).get("custom", "").endswith(":gh-epic-link")),
        "customfield_10100",
    )
    interesting = [
        {"id": field["id"], "name": field["name"], "schema": field.get("schema")}
        for field in fields
        if field["id"] in {epic_link, "customfield_10210", "customfield_10101", "customfield_14700", "customfield_14701"}
        or any(term in field["name"].lower() for term in ("clone template", "progress calculation", "lms creation", "lms completion"))
    ]
    template_fields = [field["id"] for field in fields if "clone template" in field["name"].lower()]
    main_fields = ["summary", "status", "resolution", "assignee", "project", "updated", "duedate",
                   "customfield_10210", "customfield_10101", "customfield_14701", "issuetype"]
    all_epics = jira.search(config["epic_jql"], main_fields)
    project_counts = Counter(issue["fields"]["project"]["key"] for issue in all_epics)
    if not project_counts:
        raise SystemExit("No project passed the currently configured SCADA filter.")
    project = args.project_key or project_counts.most_common(1)[0][0]
    if project not in project_counts:
        raise SystemExit("The selected project is outside the configured SCADA scope.")
    keys = [issue["key"] for issue in all_epics if issue["fields"]["project"]["key"] == project]
    child_fields = ["summary", "status", "resolution", "labels", "subtasks", "parent", "updated", epic_link, "customfield_10210"] + template_fields
    child_query = '"Epic Link" in (' + ",".join(json.dumps(key) for key in keys) + ")"
    linked = jira.search(child_query, child_fields)

    def link(issue):
        value = issue["fields"].get(epic_link)
        return value.get("key") if isinstance(value, dict) else value

    by_epic = {key: [item for item in linked if link(item) == key] for key in keys}
    candidates = []
    for key, children in by_epic.items():
        progress = {}
        attach_completion(progress, children)
        if progress["progressState"] == "reported":
            has_subtasks = any(item["fields"].get("subtasks") for item in children)
            candidates.append((has_subtasks, 0 < progress["jiraProgress"] < 100, key))
    if not candidates:
        raise SystemExit("No single reported SCADA completion source exists in that project. Choose another project.")
    chosen = sorted(candidates, reverse=True)[0][2]
    raw_epic = jira.issue(chosen)
    children = list(by_epic[chosen])
    child_keys = {item["key"] for item in children}
    for item in raw_epic["fields"].get("subtasks", []):
        if item["key"] not in child_keys:
            children.append(jira.issue(item["key"]))
    subkeys = list(dict.fromkeys(item["key"] for child in children for item in child["fields"].get("subtasks", [])))
    sub_fields = ["summary", "status", "resolution", "parent", "updated", "issuetype"]

    def read_subtasks():
        found = []
        for start in range(0, len(subkeys), 60):
            found.extend(jira.search("key in (" + ",".join(subkeys[start:start + 60]) + ")", sub_fields))
        if {item["key"] for item in found} != set(subkeys):
            raise RuntimeError("A requested subtask was missing. Permission or hierarchy coverage needs review.")
        return {item["key"]: item for item in found}

    subs = read_subtasks()
    leaves = []
    for child in children:
        refs = child["fields"].get("subtasks", [])
        for ref in refs:
            if (subs[ref["key"]]["fields"].get("parent") or {}).get("key") != child["key"]:
                raise RuntimeError("The issue hierarchy changed during collection.")
        leaves.extend([subs[ref["key"]] for ref in refs] if refs else [child])
    normalized = normalize(raw_epic, config.get("ms_end_field") or "customfield_14701")
    attach_completion(normalized, children)

    def signature(items):
        return json.dumps(sorted(items, key=lambda item: item["key"]), sort_keys=True, default=str)

    scope = config["epic_jql"]
    unquoted = re.sub(r""""(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'""", lambda match: " " * len(match[0]), scope)
    order = re.search(r"\border\s+by\b", unquoted, re.IGNORECASE)
    condition = scope[:order.start()] if order else scope
    sort = " " + scope[order.start():] if order else ""
    repeated_project = jira.search("(" + condition.strip() + ") AND project = " + json.dumps(project) + sort, main_fields)
    initial_project = [item for item in all_epics if item["key"] in keys]
    repeated_children = jira.search(child_query, child_fields)
    repeated_epic = jira.issue(chosen)
    repeated_subs = read_subtasks()
    stable = (
        signature(initial_project) == signature(repeated_project)
        and signature(linked) == signature(repeated_children)
        and signature([raw_epic]) == signature([repeated_epic])
        and signature(list(subs.values())) == signature(list(repeated_subs.values()))
    )
    selected_project = [normalize(item) for item in initial_project]
    assigned = [item for item in selected_project if item["ownerId"]]
    completed = sum(done(item) for item in leaves)
    count = len(leaves)
    evidence = {
        "classification": "LIVE READ-ONLY OBSERVATION; identifiers and titles replaced by aliases",
        "collection_started_at": started,
        "collection_ended_at": stamp(),
        "duration_seconds": round(time.monotonic() - timer, 3),
        "repeat_reads_identical": stable,
        "cutoff_limitation": "Stable repeated reads are an observation window, not a transactionally frozen or historical Jira snapshot.",
        "instance": {"deploymentType": instance.get("deploymentType"), "version": instance.get("version"), "baseUrl": "<JIRA_BASE_URL>"},
        "scope": {"matched_project_count": len(project_counts), "matched_epics_all_projects": len(all_epics), "project_alias": "PROJECT-A"},
        "project_summary": {
            "matching_epics": len(selected_project), "assigned_epics": len(assigned),
            "unassigned_epics": len(selected_project) - len(assigned),
            "assigned_done_epics": sum(item["done"] for item in assigned),
            "all_done_epics": sum(item["done"] for item in selected_project),
        },
        "epic_example": {
            "key": "EPIC-A", "summary": "<PLC-A>", "status": normalized["status"],
            "done": normalized["done"], "resolution": normalized["resolution"],
            "ms_end": normalized["msEnd"], "jira_percent": normalized["jiraProgress"],
            "progress_state": normalized["progressState"],
            "linked_issue_count": len(children),
            "sources": [
                {"key": "WORK-A-" + str(index + 1), "summary": "<SCADA work issue>", "percent": source["percent"]}
                for index, source in enumerate(normalized["progressSources"])
            ],
            "template_reference_present": any(item["fields"].get(field) for item in children for field in template_fields),
            "leaf_completed": completed, "leaf_total": count,
            "leaf_percent": round(100 * completed / count, 6) if count else None,
            "leaf_display_percent": math.floor(100 * completed / count + 0.5) if count else None,
            "leaf_items": [
                {"key": "ITEM-A-" + str(index + 1).zfill(2), "summary": "<checklist item>",
                 "status": item["fields"]["status"]["name"],
                 "category": item["fields"]["status"]["statusCategory"]["key"],
                 "has_resolution": bool(item["fields"].get("resolution")), "done": done(item),
                 "source_updated_at": item["fields"].get("updated")}
                for index, item in enumerate(leaves)
            ],
        },
        "field_metadata": interesting,
        "request_counts": dict(calls),
        "max_request_seconds": round(max(durations, default=0), 3),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({
        "evidence": str(args.output), "stable": stable, "requests": sum(calls.values()),
        "duration_seconds": evidence["duration_seconds"],
        "epics_in_project": len(selected_project), "leaf_completed": completed, "leaf_total": count,
        "jira_percent": normalized["jiraProgress"],
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        raise SystemExit("Read-only collection failed (" + type(error).__name__ + "). Review access and scope privately; no raw Jira records were exported.") from None
