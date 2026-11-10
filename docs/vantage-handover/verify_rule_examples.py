"""Execute simulated Vantage discovery examples, independently of Jira and GMR."""

import copy
import json
from pathlib import Path


def discover(projects, rules, roots):
    outcomes = []
    for project in projects:
        if not project.get("approved"):
            continue
        for rule in rules:
            if (rule["department"] not in project["departments"]
                    or project["phase"] not in rule["phases"]
                    or project["project_class"] not in rule["project_classes"]):
                continue
            matches = [root for root in roots
                       if root.get("tgw_ref") == project["tgw_id"]
                       and root.get("jira_project_id") == project["jira_project_id"]
                       and root.get("marker") == rule["marker"]]
            state = "mapped" if len(matches) == 1 else "missing" if not matches else "ambiguous"
            if state == "mapped" and matches[0].get("version") != rule["version"]:
                state = "version_review"
            result = {"project": project["tgw_id"], "department": rule["department"],
                      "template": rule["id"], "state": state}
            if state == "mapped":
                numerator = denominator = optional = excluded = blocked = 0
                for item in matches[0]["items"]:
                    if not isinstance(item.get("required"), bool):
                        result["state"] = "item_review"
                        break
                    if not item["required"]:
                        optional += 1
                        continue
                    disposition = item["state"] in ("skipped", "not_applicable")
                    if disposition and item.get("disposition_approved") is True:
                        excluded += 1
                        continue
                    if disposition or item["state"] not in ("complete", "todo", "blocked", "in_progress"):
                        result["state"] = "item_review"
                        break
                    denominator += 1
                    numerator += item["state"] == "complete"
                    blocked += item["state"] == "blocked"
                if result["state"] == "mapped":
                    result.update(numerator=numerator, denominator=denominator, optional=optional,
                                  excluded=excluded, blocked=blocked,
                                  percent=round(numerator / denominator * 100, 6) if denominator else None)
            outcomes.append(result)
    for root in roots:
        owners = [project for project in projects if project.get("approved")
                  and project["tgw_id"] == root.get("tgw_ref")
                  and project["jira_project_id"] == root.get("jira_project_id")]
        if len(owners) != 1:
            outcomes.append({"root": root["id"], "state": "identity_review"})
            continue
        project = owners[0]
        mappings = [rule for rule in rules if rule["marker"] == root.get("marker")
                    and rule["department"] in project["departments"]
                    and project["phase"] in rule["phases"]
                    and project["project_class"] in rule["project_classes"]]
        if len(mappings) != 1:
            outcomes.append({"root": root["id"], "state": "template_review"})
    return outcomes


def main():
    fixture = json.loads(Path(__file__).with_name("rule-examples.json").read_text())
    rules = fixture["rules"]
    original_rules = copy.deepcopy(rules)
    existing = discover(fixture["projects"][:1], rules, fixture["checklists"])
    expanded = discover(fixture["projects"], rules, fixture["checklists"])
    assert existing[0]["numerator"] == 1 and existing[0]["denominator"] == 3
    assert existing[0]["optional"] == 1 and existing[0]["excluded"] == 2
    assert len(expanded) == 3
    assert all(row["denominator"] == 3 for row in expanded)
    assert all(row["numerator"] == 2 for row in expanded if row["project"] == "TGW-FUTURE-B")
    assert rules == original_rules
    assert not any(row["project"] == "TGW-OUTSIDE" for row in expanded)
    missing = discover(fixture["projects"][:1], rules, [])
    assert missing[0]["state"] == "missing"
    ambiguous = discover(fixture["projects"][:1], rules, fixture["checklists"] + [fixture["checklists"][0]])
    assert ambiguous[0]["state"] == "ambiguous"
    wrong_version = copy.deepcopy(fixture["checklists"])
    wrong_version[0]["version"] = "unknown"
    assert discover(fixture["projects"][:1], rules, wrong_version)[0]["state"] == "version_review"
    no_applicable_items = copy.deepcopy(fixture["checklists"])
    no_applicable_items[0]["items"] = []
    assert discover(fixture["projects"][:1], rules, no_applicable_items)[0]["percent"] is None
    unknown_disposition = copy.deepcopy(fixture["checklists"])
    unknown_disposition[0]["items"][4]["disposition_approved"] = False
    assert discover(fixture["projects"][:1], rules, unknown_disposition)[0]["state"] == "item_review"
    unknown_root = copy.deepcopy(fixture["checklists"][:1])
    unknown_root[0]["marker"] = "UNKNOWN"
    assert any(row["state"] == "template_review" for row in discover(fixture["projects"][:1], rules, unknown_root))
    unknown_root[0].pop("tgw_ref")
    assert any(row["state"] == "identity_review" for row in discover(fixture["projects"][:1], rules, unknown_root))
    print(json.dumps({"classification": "SIMULATION ONLY", "results": expanded, "checks": {
        "future_project_reused_unchanged_rules": True, "second_department_different_template": True,
        "shared_jira_project_kept_tgw_projects_separate": True, "unapproved_project_excluded": True,
        "missing_ambiguous_unknown_version_and_disposition_review": True,
        "unknown_root_and_project_identity_review": True,
        "zero_denominator_is_not_zero_percent": True
    }}, indent=2))


if __name__ == "__main__":
    main()
