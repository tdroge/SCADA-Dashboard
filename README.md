# SCADA Dashboard handover for TGW Project Vantage

Technical handover prepared on 10 November 2026 from the working SCADA dashboard and Mission Ctrl Viewer code, configuration, and test evidence.

- [Technical handover](docs/vantage-handover/HANDOVER.md)
- [31-row field and tag mapping](docs/vantage-handover/mapping.csv)
- [Sanitized live reconciliation](docs/vantage-handover/live-evidence.json)
- [Source revisions and test evidence](docs/vantage-handover/source-and-test-evidence.json)
- [Simulated future-project and second-department results](docs/vantage-handover/simulation-evidence.json)

The handover distinguishes implemented behavior, tested behavior, live observations, proposed design, and remaining access or policy decisions. It includes source references pinned to the inspected application revisions.

## Repeatable checks

Run the simulated discovery and checklist examples from the handover folder.

~~~powershell
cd docs/vantage-handover
py -B verify_rule_examples.py
~~~

The simulation uses [rule-examples.json](docs/vantage-handover/rule-examples.json) and requires only Python's standard library.

The [read-only live collector](docs/vantage-handover/verify_scada_readonly.py) reuses the original SCADA source and the Viewer's saved Windows credential. Its setup, source dependencies, permitted reads, and cutoff limitations are documented in the handover. Published evidence uses sanitized project, issue, user, and instance identifiers.
