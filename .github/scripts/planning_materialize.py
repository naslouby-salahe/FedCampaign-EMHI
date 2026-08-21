import json
import os
import re
import time
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

from planning_issue_specs import ISSUES

repo = os.environ["REPOSITORY"]
token = os.environ["GH_TOKEN"]
api = f"https://api.github.com/repos/{repo}"
pr_number = 16
write_delay_seconds = 0.85

milestone_meta = {
    "M01": {"name": "Governance, Configuration & Architecture Foundation", "upstream": [], "outcome": "Establish the immutable scientific/configuration authority, repository/package structure, deterministic identity primitives, and enforceable architecture/quality boundaries needed by every later milestone.", "scope": "§1–§5, §16 architecture, §22–§23", "ownership": "REQ-001–REQ-019; REQ-061–REQ-086; REQ-098–REQ-102; REQ-182; REQ-275–REQ-282; REQ-376–REQ-387; REQ-395–REQ-413"},
    "M02": {"name": "Artifact Lifecycle, Execution Engine & Public CLI", "upstream": ["M01"], "outcome": "Implement semantic execution identity, artifact ownership/provenance/reuse, selective invalidation and recovery, confirmatory execution governance, and the complete public CLI orchestration contract.", "scope": "§16–§19", "ownership": "REQ-283–REQ-347"},
    "M03": {"name": "Dataset Inventory, Deterministic Preprocessing & Campaign Registry", "upstream": ["M01", "M02"], "outcome": "Implement raw-release authority, deterministic OpTC/TC5 adaptation and preprocessing, chronological benign partitions/horizons, and the immutable campaign registry.", "scope": "§6–§7, §12", "ownership": "REQ-117–REQ-137; REQ-213–REQ-216"},
    "M04": {"name": "Local Detectors, Scoring & Local Policies", "upstream": ["M01", "M02", "M03"], "outcome": "Implement deterministic local detector assignment/training/scoring and independent primary/strong local stopping policies without global-information leakage.", "scope": "§5 local detector/policy rules, §9", "ownership": "REQ-087–REQ-097; REQ-147–REQ-148"},
    "M05": {"name": "EMHI Estimator, Contexts, Evidence & Metric Core", "upstream": ["M01", "M02", "M03", "M04"], "outcome": "Implement the EMII/EMHI scientific core: ranks, exact-exclusion contexts, hierarchical innovations, calibration, sequential evidence/stopping, context variants, and canonical metrics.", "scope": "§4, §8, §11", "ownership": "REQ-020–REQ-060; REQ-138–REQ-146; REQ-174–REQ-181; REQ-183–REQ-212"},
    "M06": {"name": "Comparator Suite & Strong Comparator Selection", "upstream": ["M01", "M02", "M03", "M04", "M05"], "outcome": "Implement all roadmap comparators and baselines under matched calibration contracts, including the pre-real strongest-comparator composition selection.", "scope": "§5 comparator rules, §10", "ownership": "REQ-149–REQ-173; REQ-388–REQ-394; REQ-414–REQ-421"},
    "M07": {"name": "Synthetic Generators & Scientific Smoke Validation", "upstream": ["M01", "M02", "M05", "M06"], "outcome": "Implement deterministic controlled generators and the exact scientific smoke/invariant fixture suite used to validate core mechanisms before claim-bearing experiments.", "scope": "§5 synthetic rules, §13.1", "ownership": "REQ-103–REQ-116; REQ-217–REQ-221"},
    "M08": {"name": "Controlled Mechanism, Estimator & Sequential Validation", "upstream": ["M05", "M06", "M07"], "outcome": "Execute the claim-bearing controlled experiments for self-explanation, pure-order separation, HOFD equivalence, estimator feasibility, comparator challenge timing, and sequential validation.", "scope": "§13.2–§13.7", "ownership": "REQ-222–REQ-236"},
    "M09": {"name": "Primary Corrected OpTC ODI Evaluation & Ablations", "upstream": ["M03", "M04", "M05", "M06", "M08"], "outcome": "Execute the primary Corrected OpTC strict-ODI evaluation plus exclusion, purification/order, and context/estimator ablation/sensitivity experiments.", "scope": "§13.8–§13.11", "ownership": "REQ-237–REQ-241"},
    "M10": {"name": "Robustness, Strong-Local & Secondary Trace", "upstream": ["M03", "M04", "M05", "M06", "M08", "M09"], "outcome": "Execute benign common-mode robustness, strong-local challenge, eligible TC Engagement 5 generalization, outside-contamination, and dropout/context-sparsity boundaries.", "scope": "§13.12–§13.16", "ownership": "REQ-242–REQ-248"},
    "M11": {"name": "Coalition Scalability & Reference-Harness Timing", "upstream": ["M04", "M05", "M07", "M08", "M09"], "outcome": "Implement and execute the common-environment in-process scalability harness across the predeclared client-count grid with exact timing/resource semantics.", "scope": "§13.17, §19.3", "ownership": "REQ-249–REQ-254"},
    "M12": {"name": "Confirmatory Statistics, Downscope & Claim-State Synthesis", "upstream": ["M08", "M09", "M10", "M11"], "outcome": "Implement the predeclared inferential procedures, multiplicity, missing/downscope semantics, and mechanical claim-state rules over complete confirmatory evidence.", "scope": "§14–§15, §21", "ownership": "REQ-255–REQ-274; REQ-363–REQ-375"},
    "M13": {"name": "Manuscript Evidence, Reporting & Reproducibility", "upstream": ["M02", "M12"], "outcome": "Materialize verified source-data exports, exact manuscript tables/figures, project summaries, claim registry, and reproducibility evidence without scientific recomputation.", "scope": "§18 reporting lineage, §20", "ownership": "REQ-348–REQ-362"},
}


def request(method, path, data=None):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        api + path,
        data=body,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as response:
        payload = response.read()
        return None if not payload else json.loads(payload)


def write(method, path, data=None):
    result = request(method, path, data)
    time.sleep(write_delay_seconds)
    return result


def all_issues():
    result = []
    page = 1
    while True:
        batch = request("GET", f"/issues?state=all&per_page=100&page={page}")
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def parse_inventory():
    inventory = Path("docs/Roadmap Coverage Inventory.md").read_text()
    records = {}
    for line in inventory.splitlines():
        if not line.startswith("| REQ-"):
            continue
        parts = line.strip().strip("|").split(" | ")
        if len(parts) < 8:
            raise RuntimeError(f"Cannot parse inventory row: {line}")
        req_id = parts[0]
        records[int(req_id.split("-")[1])] = {"id": req_id, "source": parts[1], "type": parts[2], "text": parts[3]}
    if set(records) != set(range(1, 422)):
        raise RuntimeError("Inventory requirement set is not exactly REQ-001 through REQ-421")
    return records


def compact_requirements(values):
    values = sorted(values)
    groups = []
    start = previous = values[0]
    for value in values[1:]:
        if value == previous + 1:
            previous = value
            continue
        groups.append((start, previous))
        start = previous = value
    groups.append((start, previous))
    rendered = []
    for start, end in groups:
        if start == end:
            rendered.append(f"REQ-{start:03d}")
        else:
            rendered.append(f"REQ-{start:03d}–REQ-{end:03d}")
    return "; ".join(rendered)


def issue_type(labels):
    if "experiment" in labels:
        return "Experiment"
    if "reporting" in labels:
        return "Reporting"
    if "infrastructure" in labels:
        return "Infrastructure"
    if labels == ["validation"]:
        return "Validation"
    return "Implementation"


records = parse_inventory()
if len(ISSUES) != 83:
    raise RuntimeError(f"Expected 83 implementation issues, found {len(ISSUES)}")
coverage = Counter(req for item in ISSUES for req in item["reqs"])
expected_implementation_requirements = set(range(1, 422)) - {182}
if set(coverage) != expected_implementation_requirements:
    missing = sorted(expected_implementation_requirements - set(coverage))
    extra = sorted(set(coverage) - expected_implementation_requirements)
    raise RuntimeError(f"Implementation requirement coverage mismatch. Missing={missing}, extra={extra}")
duplicated = sorted(req for req, count in coverage.items() if count != 1)
if duplicated:
    raise RuntimeError(f"Implementation requirement ownership is not one-to-one: {duplicated}")

issue_template = Path("docs/Implementation Templates/3 - Issues.md").read_text()
nonneg_start = issue_template.index("## Non-Negotiable Implementation Contracts")
implementation_surface_start = issue_template.index("## Implementation Surface")
quality_start = issue_template.index("## Quality Gates")
nonneg_contract = issue_template[nonneg_start:implementation_surface_start].rstrip()
quality_and_completion_tail = issue_template[quality_start:].rstrip()

existing = all_issues()
key_pattern = re.compile(r"<!-- roadmap-planning-key:([^>]+) -->")
issue_by_key = {}
for item in existing:
    body = item.get("body") or ""
    match = key_pattern.search(body)
    if match:
        issue_by_key[match.group(1)] = item

reuse = {"M01-I02": 1, "M01-I04": 2}
issue_number_by_key = {}
for item in ISSUES:
    key = item["key"]
    marker = f"<!-- roadmap-planning-key:{key} -->"
    current = issue_by_key.get(key)
    if current is None and key in reuse:
        current = next((candidate for candidate in existing if candidate.get("number") == reuse[key]), None)
    title = f"[{item['milestone']}] {item['title']}"
    payload = {
        "title": title,
        "body": marker + "\nPlanning body is being reconciled in this materialization run.",
        "state": "open",
        "labels": item["labels"],
        "milestone": int(item["milestone"][1:]),
    }
    if current is None:
        current = write("POST", "/issues", payload)
    else:
        current = write("PATCH", f"/issues/{current['number']}", payload)
    issue_number_by_key[key] = current["number"]

clarification_key = "CLAR-001"
clarification_marker = f"<!-- roadmap-planning-key:{clarification_key} -->"
clarification_current = issue_by_key.get(clarification_key)
clarification_payload = {"title": "CLAR-001 — Resolve authoritative roadmap repository path", "body": clarification_marker + "\nPlanning body is being reconciled in this materialization run.", "state": "open", "labels": ["roadmap-clarification", "validation"], "milestone": 1}
if clarification_current is None:
    clarification_current = write("POST", "/issues", clarification_payload)
else:
    clarification_current = write("PATCH", f"/issues/{clarification_current['number']}", clarification_payload)
clarification_number = clarification_current["number"]

milestone_issue_keys = defaultdict(list)
for item in ISSUES:
    milestone_issue_keys[item["milestone"]].append(item["key"])

milestone_audit_template = Path("docs/Implementation Templates/4 - Milestone Audit.md").read_text()
audit_number_by_milestone = {}
existing = all_issues()
issue_by_key = {}
for item in existing:
    body = item.get("body") or ""
    match = key_pattern.search(body)
    if match:
        issue_by_key[match.group(1)] = item

for code, meta in milestone_meta.items():
    key = f"AUDIT-{code}"
    marker = f"<!-- roadmap-planning-key:{key} -->"
    current = issue_by_key.get(key)
    payload = {"title": f"Milestone Audit — {code}: {meta['name']}", "body": marker + "\nAudit body is being reconciled in this materialization run.", "state": "open", "labels": ["milestone-audit", "validation"], "milestone": int(code[1:])}
    if current is None:
        current = write("POST", "/issues", payload)
    else:
        current = write("PATCH", f"/issues/{current['number']}", payload)
    audit_number_by_milestone[code] = current["number"]

global_key = "GLOBAL-AUDIT"
global_marker = f"<!-- roadmap-planning-key:{global_key} -->"
existing = all_issues()
issue_by_key = {}
for item in existing:
    body = item.get("body") or ""
    match = key_pattern.search(body)
    if match:
        issue_by_key[match.group(1)] = item
global_current = issue_by_key.get(global_key)
global_payload = {"title": "Global Roadmap Implementation Audit", "body": global_marker + "\nGlobal audit body is being reconciled in this materialization run.", "state": "open", "labels": ["global-roadmap-audit", "validation"]}
if global_current is None:
    global_current = write("POST", "/issues", global_payload)
else:
    global_current = write("PATCH", f"/issues/{global_current['number']}", global_payload)
global_audit_number = global_current["number"]

spec_by_key = {item["key"]: item for item in ISSUES}
index_by_key = {item["key"]: index for index, item in enumerate(ISSUES)}
blocked_by = defaultdict(list)
blocks = defaultdict(list)
for item in ISSUES:
    current_key = item["key"]
    current_index = index_by_key[current_key]
    for dependency_key in item["deps"]:
        if dependency_key not in spec_by_key:
            raise RuntimeError(f"Unknown issue dependency {dependency_key} from {current_key}")
        dependency_index = index_by_key[dependency_key]
        if dependency_index < current_index:
            blocked_by[current_key].append(dependency_key)
            blocks[dependency_key].append(current_key)
        else:
            blocks[current_key].append(dependency_key)


def render_dependencies(item):
    key = item["key"]
    blocked_lines = []
    for dependency_key in sorted(set(blocked_by[key]), key=index_by_key.get):
        dependency = spec_by_key[dependency_key]
        blocked_lines.append(f"- #{issue_number_by_key[dependency_key]} — `{dependency_key}` {dependency['title']}: required upstream contract/evidence must be complete and valid before this issue consumes it.")
    if not blocked_lines:
        milestone_upstream = milestone_meta[item["milestone"]]["upstream"]
        if milestone_upstream:
            blocked_lines.append("- Upstream milestone entry gates apply: " + ", ".join(f"{code} complete with audit PASS" for code in milestone_upstream) + ".")
        else:
            blocked_lines.append("- None beyond repository/roadmap authority and the milestone entry gate.")
    block_lines = []
    for downstream_key in sorted(set(blocks[key]), key=index_by_key.get):
        downstream = spec_by_key[downstream_key]
        block_lines.append(f"- #{issue_number_by_key[downstream_key]} — `{downstream_key}` {downstream['title']}: consumes this issue's validated contract/evidence or must remain compatible with it.")
    if not block_lines:
        block_lines.append("- No direct implementation-issue dependency beyond the milestone's declared downstream consumers.")
    return "\n".join(blocked_lines), "\n".join(block_lines)


def render_issue(item):
    key = item["key"]
    meta = milestone_meta[item["milestone"]]
    req_rows = [records[req] for req in item["reqs"]]
    sources = []
    for row in req_rows:
        if row["source"] not in sources:
            sources.append(row["source"])
    blocked_text, blocks_text = render_dependencies(item)
    scope_lines = "\n".join(f"- {work}" for work in item["work"])
    source_lines = "\n".join(f"- {source}" for source in sources)
    req_lines = "\n".join(f"- {row['id']}" for row in req_rows)
    acceptance_lines = "\n".join(f"- [ ] {row['id']} — {row['text']}" for row in req_rows)
    test_lines = "\n".join(f"- [ ] {test}" for test in item["tests"])
    output_lines = "\n".join(f"- {output}" for output in item["outputs"])
    return f"""<!-- roadmap-planning-key:{key} -->
# {item['title']}

> Every issue is an executable unit of roadmap work. The authoritative roadmap remains the scientific and implementation authority; this issue may organize execution and verification but may not expand, reinterpret, redesign, or weaken it.

## Issue Summary

- **Planning key:** `{key}`
- **Milestone:** `{item['milestone']} — {meta['name']}`
- **Milestone audit:** #{audit_number_by_milestone[item['milestone']]}
- **Primary deliverable:** {item['objective']}
- **Issue type:** {issue_type(item['labels'])}

## Roadmap Authority

### Roadmap Sections

{source_lines}

### Requirements

{req_lines}

Every scope item, acceptance criterion, required output, and claim-bearing behavior in this issue must trace to this authority or to prerequisite implementation strictly necessary to satisfy it.

## Objective

{item['objective']}

## Scope

Implement only the work required to satisfy the referenced roadmap requirements:

{scope_lines}

No requirement may exist only implicitly in acceptance criteria, tests, or implementation notes.

## Out of Scope

- Editing, renaming, weakening, or otherwise changing the authoritative roadmap.
- Any roadmap requirement not listed above except prerequisite plumbing strictly necessary to satisfy the listed requirements.
- Speculative features, alternative scientific behavior, unrelated refactors, new experiments, extra abstractions, post-hoc choices, or convenience functionality not required by the roadmap.
- Any scientific value, default, fallback, dataset fact, method, metric, claim, or assumption invented by the implementer.

## Dependencies

### Blocked By

{blocked_text}

### Blocks

{blocks_text}

Dependencies describe actual consumed or downstream contracts/evidence, not merely administrative ordering.

{nonneg_contract}

## Implementation Surface

Expected areas affected by this issue:

### Production Code / Domain Contracts

- Roadmap-owned modules and typed domain/configuration contracts required by the scope above; exact placement follows the fixed repository architecture.

### Tests

- Tests listed in **Required Tests** plus every applicable repository quality/architecture/scientific gate.

### Artifacts / Reporting

{output_lines}

## Acceptance Criteria

{acceptance_lines}
- [ ] All issue scope items are implemented completely and no listed requirement remains implicit.
- [ ] Roadmap semantics, formulas, equality rules, thresholds, tolerances, configuration ownership, and failure semantics are preserved exactly where applicable.
- [ ] Invalid, unavailable, infeasible, unsupported, Not Tested, and abstention states follow the roadmap instead of hidden fallback behavior.
- [ ] Determinism, provenance, reuse, stale-evidence, and reproducibility obligations are satisfied where applicable.
- [ ] Required upstream/downstream contracts integrate successfully.
- [ ] Required artifacts/evidence have the correct identity, schema, integrity, completion state, and provenance.
- [ ] No unrelated scientific or product behavior is introduced.

## Required Tests

Concrete issue-specific tests:

{test_lines}

In addition, every test category in the mandatory template below is required when applicable; a genuinely inapplicable category must be recorded as `N/A — <reason>` in the completion record rather than silently skipped.

## Required Outputs

{output_lines}

Each output must use its roadmap/repository-defined identity and location where specified.

{quality_and_completion_tail}
"""

for item in ISSUES:
    number = issue_number_by_key[item["key"]]
    payload = {"title": f"[{item['milestone']}] {item['title']}", "body": render_issue(item), "state": "open", "labels": item["labels"], "milestone": int(item["milestone"][1:])}
    write("PATCH", f"/issues/{number}", payload)

clarification_body = f"""<!-- roadmap-planning-key:CLAR-001 -->
# CLAR-001 — Resolve authoritative roadmap repository path

## Issue Summary

- **Milestone:** M01 — {milestone_meta['M01']['name']}
- **Milestone audit:** #{audit_number_by_milestone['M01']}
- **Primary deliverable:** An explicit authoritative resolution of how the fixed Section 16 `docs/Roadmap.md` target path relates to the current immutable authoritative `docs/FedCampaign_EMHI_Roadmap.md`.
- **Issue type:** Roadmap Clarification

## Roadmap Authority

### Roadmap Sections

- §16 fixed repository tree → `docs/Roadmap.md`
- Current repository planning authority: the substantive roadmap directly under `docs/` is immutable and its filename is not fixed by the planning process.

### Requirements

- REQ-182

## Objective

Resolve the repository-path conflict without editing the authoritative roadmap or allowing implementation to guess whether Section 16 intends a rename, duplicate authoritative copy, alias, or another path realization.

## Scope

- Determine the authoritative implementation interpretation of the Section 16 roadmap-document path.
- Record the resolution explicitly in this clarification issue and the Roadmap Coverage Inventory.
- Link the resolution to M01 and REQ-182 before implementing that path.
- Keep all unrelated roadmap implementation work unblocked.

## Out of Scope

- Editing or rewriting the authoritative roadmap.
- Inventing a new scientific, methodological, architectural, or execution requirement.
- Blocking requirements unrelated to REQ-182.

## Dependencies

### Blocked By

- None; this issue exists because the roadmap and immutable current repository authority do not uniquely determine the future path realization.

### Blocks

- Only REQ-182 and the corresponding future repository-path realization in M01.

## Acceptance Criteria

- [ ] A single unambiguous interpretation is explicitly approved for the future repository path.
- [ ] The resolution does not edit, weaken, or reinterpret scientific roadmap content.
- [ ] `docs/Roadmap Coverage Inventory.md` records the resolution and actual issue reference.
- [ ] M01 planning state reflects the resolved path contract.
- [ ] No unrelated milestone or issue is blocked by this clarification.

## Required Tests / Verification

- [ ] Verify the chosen path behavior is compatible with the immutable roadmap authority rule.
- [ ] Verify no duplicate authoritative scientific source is silently created unless that exact behavior is the approved resolution.
- [ ] Verify inventory, milestone, and implementation issue traceability for REQ-182 are consistent.

## Required Outputs

- Clarification decision recorded in this issue.
- Updated REQ-182 / CLAR-001 mapping in the Roadmap Coverage Inventory.
- Updated M01 path contract when resolution is applied.

## Roadmap Deviations / Follow-Ups

No roadmap deviation is authorized by this issue. Any implementation follow-up must be limited to applying the approved path resolution.
"""
write("PATCH", f"/issues/{clarification_number}", {"title": "CLAR-001 — Resolve authoritative roadmap repository path", "body": clarification_body, "state": "open", "labels": ["roadmap-clarification", "validation"], "milestone": 1})

milestone_owned_requirements = defaultdict(list)
for item in ISSUES:
    milestone_owned_requirements[item["milestone"]].extend(item["reqs"])
milestone_owned_requirements["M01"].append(182)

for code, meta in milestone_meta.items():
    audit_body = milestone_audit_template
    audit_body = audit_body.replace("# Milestone Audit — <Milestone ID>: <Milestone Name>", f"# Milestone Audit — {code}: {meta['name']}", 1)
    audit_body = audit_body.replace("- Milestone ID:", f"- Milestone ID: `{code}`", 1)
    audit_body = audit_body.replace("- Milestone name:", f"- Milestone name: {meta['name']}", 1)
    audit_body = audit_body.replace("- Roadmap sections:", f"- Roadmap sections: {meta['scope']}", 1)
    req_list = "\n".join(f"  - REQ-{req:03d}" for req in sorted(milestone_owned_requirements[code]))
    audit_body = audit_body.replace("- Covered requirement IDs:\n  - REQ-...", "- Covered requirement IDs:\n" + req_list, 1)
    issue_list = "\n".join(f"  - #{issue_number_by_key[key]} — `{key}` {spec_by_key[key]['title']}" for key in milestone_issue_keys[code])
    if code == "M01":
        issue_list += f"\n  - #{clarification_number} — `CLAR-001` roadmap-path clarification for REQ-182"
    audit_body = audit_body.replace("- Milestone issues:\n  - #...", "- Milestone issues:\n" + issue_list, 1)
    upstream = meta["upstream"]
    upstream_list = "\n".join(f"  - {up} — {milestone_meta[up]['name']}" for up in upstream) if upstream else "  - None"
    audit_body = audit_body.replace("- Prerequisite milestones:\n  - ...", "- Prerequisite milestones:\n" + upstream_list, 1)
    audit_body = audit_body.replace("- Audit trigger / reason:", "- Audit trigger / reason: Milestone completion gate; rerun after any relevant upstream/downstream or implementation change.", 1)
    audit_body = audit_body.replace("- Implementation revision:", "- Implementation revision: Record the exact audited commit before executing this audit.", 1)
    audit_body = audit_body.replace("- Audit date:", "- Audit date: Record when the audit is executed.", 1)
    audit_body = audit_body.replace("- Agent / auditor:", "- Agent / auditor: Independent auditor responsible for evidence-based PASS/FAIL.", 1)
    audit_body = f"<!-- roadmap-planning-key:AUDIT-{code} -->\n" + audit_body
    write("PATCH", f"/issues/{audit_number_by_milestone[code]}", {"title": f"Milestone Audit — {code}: {meta['name']}", "body": audit_body, "state": "open", "labels": ["milestone-audit", "validation"], "milestone": int(code[1:])})

global_template = Path("docs/Implementation Templates/5 - Global Roadmap Audit.md").read_text()
milestone_audit_links = "\n".join(f"- {code} — milestone #{int(code[1:])}; audit #{audit_number_by_milestone[code]}" for code in milestone_meta)
global_preamble = f"""<!-- roadmap-planning-key:GLOBAL-AUDIT -->
## Instantiated Planning Scope

- Authoritative roadmap: `docs/FedCampaign_EMHI_Roadmap.md`
- Coverage inventory: `docs/Roadmap Coverage Inventory.md` in planning PR #{pr_number}
- Implementation issues: 83 roadmap implementation issues plus clarification #{clarification_number} for REQ-182
- Milestones: M01–M13
- Milestone audits:
{milestone_audit_links}
- This issue must be rerun after any upstream requirement mapping, milestone, issue, audit, roadmap-clarification resolution, or implementation evidence changes.

"""
global_body = global_preamble + global_template
write("PATCH", f"/issues/{global_audit_number}", {"title": "Global Roadmap Implementation Audit", "body": global_body, "state": "open", "labels": ["global-roadmap-audit", "validation"]})


def unique_sources(item):
    result = []
    for req in item["reqs"]:
        source = records[req]["source"]
        if source not in result:
            result.append(source)
    return result


def render_milestone(code):
    meta = milestone_meta[code]
    keys = milestone_issue_keys[code]
    issue_refs = ", ".join(f"#{issue_number_by_key[key]}" for key in keys)
    if code == "M01":
        issue_refs += f", #{clarification_number} (clarification)"
    upstream_text = ", ".join(meta["upstream"]) if meta["upstream"] else "None"
    coverage_rows = []
    implementation_rows = []
    deliverable_rows = []
    for order, key in enumerate(keys, start=1):
        item = spec_by_key[key]
        sources = "; ".join(unique_sources(item))
        reqs = compact_requirements(item["reqs"])
        number = issue_number_by_key[key]
        verification = "; ".join(item["tests"][:2] + item["outputs"][:1])
        coverage_rows.append(f"| {sources} | {item['title']} | {reqs} | #{number} | {verification} |")
        deps = [f"#{issue_number_by_key[d]}" for d in blocked_by[key]]
        dep_text = ", ".join(deps) if deps else (", ".join(meta["upstream"]) if meta["upstream"] else "None")
        implementation_rows.append(f"| {order} | #{number} — {item['title']} | {item['title']} | {sources} | {reqs} | {dep_text} |")
        deliverable_rows.append(f"| {'; '.join(item['outputs'])} | #{number} | {'; '.join(item['tests'][:2])} | Roadmap-declared downstream consumers / milestone audit |")
    if code == "M01":
        coverage_rows.append(f"| §16 fixed repository tree / current immutable roadmap authority | Resolve roadmap-document path conflict | REQ-182 | #{clarification_number} | Explicit approved clarification and reconciled inventory mapping |")
        implementation_rows.append(f"| {len(keys)+1} | #{clarification_number} — Resolve authoritative roadmap repository path | Roadmap clarification | §16 | REQ-182 | None; blocks only path realization |")
        deliverable_rows.append(f"| Approved repository-path resolution for REQ-182 | #{clarification_number} | Explicit unambiguous decision + inventory reconciliation | M01 path realization / milestone audit |")
    upstream_rows = "\n".join(f"| {up} — {milestone_meta[up]['name']} | Validated milestone outputs and interfaces consumed by {code} | Complete + audit PASS |" for up in meta["upstream"])
    if not upstream_rows:
        upstream_rows = "| None | Roadmap and repository authority only | N/A — first milestone |"
    artifact_rows = []
    for key in keys:
        number = issue_number_by_key[key]
        artifact_rows.append(f"| Validated outputs/evidence from #{number} — {spec_by_key[key]['title']} | #{number} | Required tests, schemas, provenance, integrity, compatibility, and completion evidence defined by that issue |")
    return f"""# {code} — {meta['name']}

> **Outcome:** {meta['outcome']}

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `{meta['scope']}` |
| Requirement ownership | `{meta['ownership']}` |
| Upstream milestones | `{upstream_text}` |
| Implementation issues | `{issue_refs}` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `#{audit_number_by_milestone[code]}` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone is explicitly mapped to implementation issue(s) or, for REQ-182 only, the dedicated clarification issue, with objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
{chr(10).join(coverage_rows)}

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one implementation issue.
- Every conditional requirement must remain traceable and must be implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
{upstream_rows}

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
{chr(10).join(artifact_rows)}

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues are the executable work units for this milestone. Detailed task checklists belong in the issues, not in this milestone description.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
{chr(10).join(implementation_rows)}

### Issue Contract

Every milestone issue must reference its exact roadmap sections, list every covered requirement ID, contain a detailed implementation checklist, define objective acceptance criteria, identify required tests and artifacts/interfaces, identify provenance/manifest updates where applicable, identify explicit dependencies, preserve roadmap terminology/semantics, and close only when every mapped requirement and criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
{chr(10).join(deliverable_rows)}

All roadmap-required deliverables for this milestone appear above or are explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when required upstream milestones are complete with audit PASS; every required dependency exists and validates; consumed evidence is provenance-compatible/current; all owned requirements are present in the inventory; every mandatory implementation requirement maps to an issue and evidence target; no blocking owned requirement is UNMAPPED/AMBIGUOUS; and no unresolved roadmap ambiguity would force an invented material decision. For M01, CLAR-001 remains a narrow blocker only for REQ-182 until resolved.

## Exit Criteria

Completion requires every mandatory/applicable conditional owned requirement satisfied; every mapped implementation issue closed; no unresolved owned coverage ambiguity; all required unit/integration/validation procedures pass; all deliverables and provenance validate; no stale/incompatible evidence remains; the milestone audit is PASS; and no blocking finding remains.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory | All mandatory and applicable requirements accounted for with no blocking coverage gaps |
| Implementation | Closed milestone issues linked to exact requirements | Every mapped requirement has completed implementation evidence |
| Unit validation | Required unit-test results | All required tests pass |
| Integration validation | Required integration-test results | All required integration paths pass |
| Scientific / functional validation | Issue-specific scientific/functional validation outputs | All roadmap-defined validation conditions pass |
| Deliverables | Required outputs and artifacts | Complete, readable, valid, and consistent with the roadmap |
| Provenance | Required manifests / dependency identity / compatibility evidence | Complete and sufficient to verify origin, compatibility, and staleness where applicable |
| Audit | Milestone audit #{audit_number_by_milestone[code]} | Final result is PASS with no unresolved blocking findings |

## Milestone Audit

**Audit issue:** `#{audit_number_by_milestone[code]}`

**Status:** `PENDING`

The milestone audit is the final completion gate and independently verifies coverage, traceability, genuine issue closure, tests/validations, deliverables, provenance/manifests, absence of stale evidence/blockers, and downstream readiness. The result is exactly PASS or FAIL; the milestone is not complete until PASS.

## Scope Boundary

- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues.
- Detailed verification checklists belong in the milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.
"""

for code in milestone_meta:
    write("PATCH", f"/milestones/{int(code[1:])}", {"title": f"{code} — {milestone_meta[code]['name']}", "description": render_milestone(code), "state": "open"})

mapping = {"implementation_issues": {key: issue_number_by_key[key] for key in issue_number_by_key}, "clarification": {"CLAR-001": clarification_number}, "milestone_audits": {code: audit_number_by_milestone[code] for code in milestone_meta}, "global_audit": global_audit_number}
marker = "<!-- roadmap-planning-materialized-state -->"
comment_body = marker + "\n## Roadmap planning materialized state\n\n```json\n" + json.dumps(mapping, indent=2, sort_keys=True) + "\n```"
comments = request("GET", f"/issues/{pr_number}/comments?per_page=100")
prior = next((item for item in comments if marker in (item.get("body") or "")), None)
if prior is None:
    write("POST", f"/issues/{pr_number}/comments", {"body": comment_body})
else:
    write("PATCH", f"/issues/comments/{prior['id']}", {"body": comment_body})
