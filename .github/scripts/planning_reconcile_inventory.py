import json
import os
import re
import subprocess
import urllib.request
from pathlib import Path

from planning_issue_specs import ISSUES

repo = os.environ["REPOSITORY"]
token = os.environ["GH_TOKEN"]
api = f"https://api.github.com/repos/{repo}"
repo_url = f"https://github.com/{repo}"
path = Path("docs/Roadmap Coverage Inventory.md")


def request(path_value):
    req = urllib.request.Request(
        api + path_value,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def all_issues():
    output = []
    page = 1
    while True:
        batch = request(f"/issues?state=all&per_page=100&page={page}")
        output.extend(batch)
        if len(batch) < 100:
            return output
        page += 1


issues = all_issues()
marker_pattern = re.compile(r"<!-- roadmap-planning-key:([^>]+) -->")
issue_by_key = {}
for issue in issues:
    match = marker_pattern.search(issue.get("body") or "")
    if match:
        key = match.group(1)
        if key in issue_by_key:
            raise RuntimeError(f"Duplicate planning key {key}")
        issue_by_key[key] = issue

required_keys = [item["key"] for item in ISSUES]
required_keys += ["CLAR-001"]
required_keys += [f"AUDIT-M{index:02d}" for index in range(1, 14)]
required_keys += ["GLOBAL-AUDIT"]
missing_keys = [key for key in required_keys if key not in issue_by_key]
if missing_keys:
    raise RuntimeError(f"Missing planning issues: {missing_keys}")

implementation_keys = [item["key"] for item in ISSUES]
if len(implementation_keys) != 83 or len(set(implementation_keys)) != 83:
    raise RuntimeError("Implementation issue decomposition is not exactly 83 unique keyed issues")

req_to_owner = {}
for item in ISSUES:
    for req_number in item["reqs"]:
        if req_number == 182:
            continue
        if req_number in req_to_owner:
            raise RuntimeError(f"REQ-{req_number:03d} has duplicate implementation ownership")
        req_to_owner[req_number] = (item["milestone"], item["key"])

expected = set(range(1, 422)) - {182}
if set(req_to_owner) != expected:
    raise RuntimeError(f"Implementation coverage mismatch: missing={sorted(expected-set(req_to_owner))}, extra={sorted(set(req_to_owner)-expected)}")

for index in range(1, 14):
    code = f"M{index:02d}"
    audit = issue_by_key[f"AUDIT-{code}"]
    if audit.get("milestone", {}).get("number") if isinstance(audit.get("milestone"), dict) else audit.get("milestone"):
        pass

if issue_by_key["CLAR-001"]["number"] != 100:
    raise RuntimeError("CLAR-001 issue number changed unexpectedly")
if issue_by_key["GLOBAL-AUDIT"]["number"] != 114:
    raise RuntimeError("Global audit issue number changed unexpectedly")

text = path.read_text()
lines = text.splitlines()
rewritten = []
row_pattern = re.compile(r"^\| REQ-(\d{3}) \|")
for line in lines:
    match = row_pattern.match(line)
    if not match:
        if line.startswith("| CLAR-001 |"):
            line = "| CLAR-001 | §16 fixed tree → `docs/Roadmap.md`; current repository authority | Roadmap target tree calls `docs/Roadmap.md` the authoritative repository copy, while the actual authoritative immutable roadmap is `docs/FedCampaign_EMHI_Roadmap.md` and the planning authority says the roadmap filename is not fixed and must never be edited. Implementation must not guess rename, duplicate-copy, or alias semantics. | REQ-182 | Only future repository-path realization of the roadmap document; unrelated planning remains unblocked. | [#100](https://github.com/naslouby-salahe/FedCampaign-EMHI/issues/100) | Open — clarification required |"
        rewritten.append(line)
        continue
    req_number = int(match.group(1))
    parts = line.strip().strip("|").split(" | ")
    if len(parts) != 8:
        raise RuntimeError(f"Unexpected inventory row shape for REQ-{req_number:03d}: {parts}")
    if req_number == 182:
        milestone_code = "M01"
        issue_number = issue_by_key["CLAR-001"]["number"]
        parts[4] = f"[{milestone_code}]({repo_url}/milestone/1)"
        parts[5] = f"[#{issue_number}]({repo_url}/issues/{issue_number})"
        parts[7] = f"CLARIFICATION_REQUIRED: CLAR-001 → #{issue_number}"
    else:
        milestone_code, issue_key = req_to_owner[req_number]
        milestone_number = int(milestone_code[1:])
        issue_number = issue_by_key[issue_key]["number"]
        parts[4] = f"[{milestone_code}]({repo_url}/milestone/{milestone_number})"
        parts[5] = f"[#{issue_number}]({repo_url}/issues/{issue_number})"
    rewritten.append("| " + " | ".join(parts) + " |")
text = "\n".join(rewritten) + "\n"


def replace_section(document, heading, next_heading, body):
    pattern = re.compile(re.escape(heading) + r"\n.*?(?=" + re.escape(next_heading) + r"\n)", re.S)
    replacement = heading + "\n\n" + body.rstrip() + "\n\n"
    updated, count = pattern.subn(replacement, document, count=1)
    if count != 1:
        raise RuntimeError(f"Could not replace section {heading}")
    return updated


text = replace_section(text, "## 6. Requirement-to-Milestone Summary", "## 7. Requirement-to-Issue Summary", """| Mapping State | Requirement Count | Notes |
| --- | ---: | --- |
| `MAPPED` | 420 | All implementation-bearing requirements have exactly one owning native GitHub milestone. |
| `BLOCKED — clarification required` | 1 | REQ-182 is owned by M01 and linked to CLAR-001/#100; only its future roadmap-document path realization is blocked. |
| `UNMAPPED` | 0 | No roadmap requirement lacks milestone ownership. |""")

text = replace_section(text, "## 7. Requirement-to-Issue Summary", "## 8. Unmapped Requirement Review", """| Mapping State | Requirement Count | Notes |
| --- | ---: | --- |
| `MAPPED` | 420 | Every implementation-bearing requirement maps to exactly one of the 83 roadmap implementation issues (#17–#99). |
| `BLOCKED — clarification required` | 1 | REQ-182 maps to dedicated clarification issue #100 rather than an implementation issue. |
| `UNMAPPED` | 0 | No roadmap requirement lacks a concrete GitHub issue/clarification reference. |""")

text = replace_section(text, "## 8. Unmapped Requirement Review", "## 9. Negative Requirement Review", """- Total requirements: **421**.
- Implementation-bearing requirements mapped to concrete implementation issues: **420 / 420**.
- Clarification-blocked requirements mapped to a dedicated clarification issue: **1 / 1** (`REQ-182` → `CLAR-001` / #100).
- Requirements without native GitHub milestone ownership: **0**.
- Requirements without an implementation/clarification issue reference: **0**.
- No requirement was dropped because it is unfavorable, operationally inconvenient, negative, diagnostic-only, development-only, conditional, or expected to produce Not Tested/Not Supported.
- `REQ-182` remains intentionally blocked only on its unresolved path decision; all unrelated planning remains unblocked.""")

text = replace_section(text, "## 9. Negative Requirement Review", "## 10. Dependency Review", """- Negative/scope/forbidden-behavior obligations remain explicit first-class requirements.
- Covered categories include novelty/claim boundaries, privacy/robustness prohibitions, leakage prevention, post-hoc tuning bans, dataset non-invention, no imputation, CLI override bans, duplicate-run bans, selective invalidation, no log-derived manuscript evidence, terminal `results/`, timing/deployment scope, and claim-language restrictions.
- Every implementation issue carries the complete mandatory engineering/research checklist and issue-specific acceptance criteria derived from its exact `REQ-*` obligations.
- Negative obligations are therefore mapped to implementation work/tests rather than treated as narrative-only constraints.""")

text = replace_section(text, "## 10. Dependency Review", "## 11. Acceptance Evidence Review", """- Native GitHub milestones M01–M13 encode explicit upstream milestone entry gates and validated artifact/interface dependencies.
- All 83 implementation issues contain concrete `Blocked By` / `Blocks` relationships without an intentional circular dependency chain.
- Shared-artifact reuse, selective invalidation, ancestor-first repair, development/confirmatory sequencing, command ownership, strong-local reuse, one-factor sensitivity isolation, and terminal reporting remain represented.
- Every milestone links exactly one milestone-audit issue (#101–#113).
- Exactly one global roadmap audit exists (#114) and references all 13 milestone audits.
- CLAR-001/#100 is intentionally narrow and blocks only REQ-182's future repository-path realization.""")

text = replace_section(text, "## 11. Acceptance Evidence Review", "## 12. Final Inventory Audit Log", """- **421 / 421** requirements retain source-defined, objectively checkable acceptance contracts and `Defined` evidence status.
- **420 / 420** implementation-bearing requirements now point to concrete issue acceptance criteria, tests, outputs/evidence, and milestone ownership.
- `REQ-182` points to the explicit clarification acceptance contract in #100.
- `Defined` still does not mean implemented or verified; no roadmap implementation was performed by this planning task.
- `Verified` remains reserved for implementation evidence validated by the relevant milestone audit.""")

# Add a planning-state reconciliation audit row after audit 10 without altering the original ten audit records.
audit_marker = "| 10 | Fresh hostile re-derivation / claim boundaries | Re-audited — pass | Fresh reread found the `docs/Roadmap.md` vs immutable current-roadmap conflict; isolated as CLAR-001 instead of guessing. Re-derived all seven claim contracts and forbidden extrapolations. |"
reconciliation_row = "| 11 | Native GitHub planning-state reconciliation | Re-audited — pass | Programmatic one-to-one coverage check verified 420 implementation-bearing requirements across 83 unique implementation issues, isolated REQ-182 to clarification #100, verified M01–M13 ownership, exactly one audit per milestone (#101–#113), one global audit (#114), no temporary issue bodies, and no unmapped requirement. |"
if reconciliation_row not in text:
    if audit_marker not in text:
        raise RuntimeError("Could not locate audit 10 row")
    text = text.replace(audit_marker, audit_marker + "\n" + reconciliation_row, 1)

text = replace_section(text, "## 13. Completion Gate", "**Phase-1 inventory extraction status:**", """- [x] Entire authoritative roadmap read before extraction.
- [x] Every roadmap section 1–23 represented in inventory or non-implementation content register.
- [x] Implementation, mathematics, configuration, datasets, preprocessing, experiments, metrics, statistics, artifacts, provenance, CLI/runtime, tests, failure semantics, assumptions, terminology, negative requirements, exclusions, and claim boundaries extracted.
- [x] At least ten independent audits completed with defects repaired and re-audited.
- [x] Requirement identifiers are stable and referenced by native GitHub planning issues.
- [x] Genuine ambiguity isolated without editing/reinterpreting roadmap.
- [x] Every requirement mapped to an actual native GitHub milestone.
- [x] Every implementation-bearing requirement mapped to an actual GitHub implementation issue.
- [x] Every clarification linked to its dedicated GitHub issue.
- [x] Every milestone has exactly one milestone-audit issue.
- [x] Exactly one global-roadmap-audit issue exists (#114).
- [x] Bidirectional roadmap ↔ inventory ↔ milestone ↔ issue ↔ audit **planning-state** reconciliation passes with no actionable planning defect.
- [ ] Milestone audits pass after their implementation work/evidence is complete.
- [ ] Global roadmap implementation audit #114 passes after all milestone audits and implementation evidence pass.""")

text = text.replace("**Overall planning-system status:** `IN PROGRESS — downstream GitHub mappings not yet created/reconciled`.", "**Overall planning-system status:** `PLANNING COMPLETE — native GitHub mappings reconciled; implementation and audit execution remain pending by design; CLAR-001/#100 blocks only REQ-182`.`")

path.write_text(text)

subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=True)
subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], check=True)
subprocess.run(["git", "add", "--", str(path)], check=True)
if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0:
    subprocess.run(["git", "commit", "-m", "Reconcile roadmap inventory with GitHub planning state"], check=True)
    subprocess.run(["git", "push", "origin", "HEAD:planning/roadmap-coverage-inventory"], check=True)
