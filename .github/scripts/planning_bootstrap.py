import json
import os
import urllib.request

repo = os.environ["REPOSITORY"]
token = os.environ["GH_TOKEN"]
api = f"https://api.github.com/repos/{repo}"


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


def normalize(value):
    return "".join(ch for ch in value.lower() if ch.isalnum())


required_labels = [
    ("implementation", "5319e7", "Roadmap implementation work"),
    ("experiment", "1d76db", "Roadmap experiment execution"),
    ("infrastructure", "6f42c1", "Repository and execution infrastructure"),
    ("validation", "0e8a16", "Validation, testing, and scientific verification"),
    ("reporting", "fbca04", "Reporting and manuscript evidence"),
    ("roadmap-clarification", "d93f0b", "Roadmap ambiguity requiring explicit resolution"),
    ("milestone-audit", "b60205", "Per-milestone completion audit"),
    ("global-roadmap-audit", "000000", "Final roadmap-wide planning audit"),
]

milestones = [
    ("M01", "Governance, Configuration & Architecture Foundation", [], "Establish the immutable scientific/configuration authority, repository/package structure, deterministic identity primitives, and enforceable architecture/quality boundaries needed by every later milestone.", "§1–§5, §16 architecture, §22–§23", "REQ-001–REQ-019; REQ-061–REQ-086; REQ-098–REQ-102; REQ-182; REQ-275–REQ-282; REQ-376–REQ-387; REQ-395–REQ-413"),
    ("M02", "Artifact Lifecycle, Execution Engine & Public CLI", ["M01"], "Implement semantic execution identity, artifact ownership/provenance/reuse, selective invalidation and recovery, confirmatory execution governance, and the complete public CLI orchestration contract.", "§16–§19", "REQ-283–REQ-347"),
    ("M03", "Dataset Inventory, Deterministic Preprocessing & Campaign Registry", ["M01", "M02"], "Implement raw-release authority, deterministic OpTC/TC5 adaptation and preprocessing, chronological benign partitions/horizons, and the immutable campaign registry.", "§6–§7, §12", "REQ-117–REQ-137; REQ-213–REQ-216"),
    ("M04", "Local Detectors, Scoring & Local Policies", ["M01", "M02", "M03"], "Implement deterministic local detector assignment/training/scoring and independent primary/strong local stopping policies without global-information leakage.", "§5 local detector/policy rules, §9", "REQ-087–REQ-097; REQ-147–REQ-148"),
    ("M05", "EMHI Estimator, Contexts, Evidence & Metric Core", ["M01", "M02", "M03", "M04"], "Implement the EMII/EMHI scientific core: ranks, exact-exclusion contexts, hierarchical innovations, calibration, sequential evidence/stopping, context variants, and canonical metrics.", "§4, §8, §11", "REQ-020–REQ-060; REQ-138–REQ-146; REQ-174–REQ-181; REQ-183–REQ-212"),
    ("M06", "Comparator Suite & Strong Comparator Selection", ["M01", "M02", "M03", "M04", "M05"], "Implement all roadmap comparators and baselines under matched calibration contracts, including the pre-real strongest-comparator composition selection.", "§5 comparator rules, §10", "REQ-149–REQ-173; REQ-388–REQ-394; REQ-414–REQ-421"),
    ("M07", "Synthetic Generators & Scientific Smoke Validation", ["M01", "M02", "M05", "M06"], "Implement deterministic controlled generators and the exact scientific smoke/invariant fixture suite used to validate core mechanisms before claim-bearing experiments.", "§5 synthetic rules, §13.1", "REQ-103–REQ-116; REQ-217–REQ-221"),
    ("M08", "Controlled Mechanism, Estimator & Sequential Validation", ["M05", "M06", "M07"], "Execute the claim-bearing controlled experiments for self-explanation, pure-order separation, HOFD equivalence, estimator feasibility, comparator challenge timing, and sequential validation.", "§13.2–§13.7", "REQ-222–REQ-236"),
    ("M09", "Primary Corrected OpTC ODI Evaluation & Ablations", ["M03", "M04", "M05", "M06", "M08"], "Execute the primary Corrected OpTC strict-ODI evaluation plus exclusion, purification/order, and context/estimator ablation/sensitivity experiments.", "§13.8–§13.11", "REQ-237–REQ-241"),
    ("M10", "Robustness, Strong-Local & Secondary Trace", ["M03", "M04", "M05", "M06", "M08", "M09"], "Execute benign common-mode robustness, strong-local challenge, eligible TC Engagement 5 generalization, outside-contamination, and dropout/context-sparsity boundaries.", "§13.12–§13.16", "REQ-242–REQ-248"),
    ("M11", "Coalition Scalability & Reference-Harness Timing", ["M04", "M05", "M07", "M08", "M09"], "Implement and execute the common-environment in-process scalability harness across the predeclared client-count grid with exact timing/resource semantics.", "§13.17, §19.3", "REQ-249–REQ-254"),
    ("M12", "Confirmatory Statistics, Downscope & Claim-State Synthesis", ["M08", "M09", "M10", "M11"], "Implement the predeclared inferential procedures, multiplicity, missing/downscope semantics, and mechanical claim-state rules over complete confirmatory evidence.", "§14–§15, §21", "REQ-255–REQ-274; REQ-363–REQ-375"),
    ("M13", "Manuscript Evidence, Reporting & Reproducibility", ["M02", "M12"], "Materialize verified source-data exports, exact manuscript tables/figures, project summaries, claim registry, and reproducibility evidence without scientific recomputation.", "§18 reporting lineage, §20", "REQ-348–REQ-362"),
]

labels = request("GET", "/labels?per_page=100")
actual_labels = {}
by_norm = {normalize(item["name"]): item for item in labels}
for name, color, description in required_labels:
    existing = by_norm.get(normalize(name))
    if existing is None:
        existing = request("POST", "/labels", {"name": name, "color": color, "description": description})
        by_norm[normalize(name)] = existing
    actual_labels[name] = existing["name"]

existing_milestones = request("GET", "/milestones?state=all&per_page=100")
milestone_by_code = {}
for item in existing_milestones:
    title = item["title"]
    for code, *_ in milestones:
        if title.startswith(code + " ") or title == code:
            milestone_by_code[code] = item

milestone_map = {}
for code, name, upstream, outcome, scope, reqs in milestones:
    title = f"{code} — {name}"
    upstream_text = ", ".join(upstream) if upstream else "None"
    description = f"""# {code} — {name}

> **Outcome:** {outcome}

## At a Glance

| Field | Value |
|---|---|
| Roadmap scope | `{scope}` |
| Requirement ownership | `{reqs}` |
| Upstream milestones | `{upstream_text}` |
| Implementation issues | `PENDING — issue reconciliation in progress` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `PENDING` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every owned roadmap requirement must map explicitly to implementation issue(s) and objective verification evidence. Requirement ranges here are summaries only and never substitute for row-level inventory mapping.

### Coverage Rules

- Every mandatory owned requirement must exist in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one implementation issue.
- Conditional requirements remain traceable and execute exactly when their roadmap condition applies.
- Every mapped requirement has objective verification/evidence.
- Every implementation issue references exact requirement IDs and roadmap sections.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the roadmap.

## Dependencies

### Milestone Dependencies

`{upstream_text}`. Every upstream milestone must be complete with audit `PASS`, and every consumed artifact/interface must be valid, current, provenance-compatible where applicable, and compatible with the active roadmap contract.

### Artifact / Interface Dependencies

Concrete artifact/interface dependencies are owned by implementation issues and will be listed with actual issue references after issue reconciliation. Dependency completion alone is insufficient without schema, provenance, compatibility, and integrity validation.

## Implementation Issues

Implementation issues are the executable work units. Detailed task checklists belong in issues, not in the milestone. This list is finalized after actual GitHub issue numbers exist; bootstrap never fabricates issue references.

### Issue Contract

Every issue must reference exact roadmap sections and requirement IDs, define detailed executable work, objective acceptance criteria, required tests, required outputs/evidence, provenance/manifest updates where applicable, and concrete dependencies; preserve roadmap terminology/semantics; and close only when every mapped requirement and criterion is satisfied.

## Deliverables

All roadmap-required implementation components, artifacts, interfaces, schemas, manifests, tests, and validation evidence owned by `{code}` must be produced by its issues and explicitly traceable through the inventory. Downstream consumers may use only validated, current, provenance-compatible deliverables.

## Entry Criteria

Implementation may begin only when required upstream milestones and audits pass; required dependencies exist and validate; every owned roadmap requirement is present in the inventory; every mandatory implementation requirement is mapped to an issue and evidence target; no blocking owned requirement is `UNMAPPED`/`AMBIGUOUS`; and no unresolved roadmap ambiguity would force an invented material decision.

## Exit Criteria

Completion requires every mandatory/applicable conditional owned requirement satisfied; every mapped implementation issue closed; no unresolved owned coverage ambiguity; required unit/integration/validation procedures pass; all deliverables and provenance validate; no stale/incompatible evidence remains; the milestone audit is `PASS`; and no blocking finding remains.

## Acceptance Evidence

Required evidence includes the reconciled Roadmap Coverage Inventory, closed implementation issues linked to exact requirements, passing unit/integration/scientific/functional validation, complete valid deliverables and provenance, and the milestone audit result `PASS`.

## Milestone Audit

**Audit issue:** `PENDING`

**Status:** `PENDING`

The audit independently verifies complete owned-roadmap coverage, exact requirement-to-issue traceability, genuine issue completion, tests/validations, deliverables, provenance/manifests, absence of stale evidence/blocking findings, and readiness for all declared downstream consumers. The audit result is `PASS` or `FAIL`; the milestone is not complete until `PASS`.

## Scope Boundary

This milestone implements only its explicitly assigned roadmap requirements. The roadmap remains authoritative. Planning may organize work but may not redefine, weaken, extend, or silently reinterpret science, mathematics, methodology, architecture, numerical/configuration values, artifact rules, or execution semantics. Detailed implementation belongs in issues; verification belongs in the audit issue; work outside mapped scope requires upstream authority first.
"""
    current = milestone_by_code.get(code)
    payload = {"title": title, "description": description, "state": "open"}
    if current is None:
        current = request("POST", "/milestones", payload)
    else:
        current = request("PATCH", f"/milestones/{current['number']}", payload)
    milestone_map[code] = {"number": current["number"], "title": current["title"]}

marker = "<!-- roadmap-planning-bootstrap-state -->"
mapping = {"labels": actual_labels, "milestones": milestone_map}
body = marker + "\n## Roadmap planning bootstrap state\n\n```json\n" + json.dumps(mapping, indent=2, sort_keys=True) + "\n```"
comments = request("GET", "/issues/16/comments?per_page=100")
prior = next((item for item in comments if marker in item.get("body", "")), None)
if prior is None:
    request("POST", "/issues/16/comments", {"body": body})
else:
    request("PATCH", f"/issues/comments/{prior['id']}", {"body": body})
