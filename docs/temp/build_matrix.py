"""Build the requirement audit matrix from the roadmap coverage inventory and GitHub issues."""
import json
import re
import subprocess
from pathlib import Path

ROOT = Path("/home/naslouby/Projects/FedCampaign-EMHI")
inv = (ROOT / "docs/inventory/Roadmap Coverage Inventory.md").read_text()
rows = re.findall(r"\|\s*(REQ-\d{4})\s*\|\s*([^|]+)\|", inv)
matrix: dict[str, str] = {}
for req, desc in rows:
    if req not in matrix:
        matrix[req] = desc.strip()[:150]

print("unique REQs:", len(matrix))

issues_reqs: dict[str, list[int]] = {}
for n in range(151, 190):
    body = subprocess.run(
        ["gh", "issue", "view", str(n), "--repo", "naslouby-salahe/FedCampaign-EMHI",
         "--json", "body", "-q", ".body"],
        capture_output=True, text=True,
    ).stdout
    for r in sorted(set(re.findall(r"REQ-\d{4}", body))):
        issues_reqs.setdefault(r, []).append(n)

print("REQs mapped to issues:", len(issues_reqs))
orphan = sorted(set(matrix) - set(issues_reqs))
print("REQs NOT covered by any issue:", len(orphan))
for o in orphan[:30]:
    print("  ", o, matrix[o][:80])

out = {r: {"desc": d, "issues": issues_reqs.get(r, [])} for r, d in sorted(matrix.items())}
tmp = ROOT / "docs/temp"
tmp.mkdir(exist_ok=True)
(tmp / "audit_matrix.json").write_text(json.dumps(out, indent=1))
print("written:", tmp / "audit_matrix.json")
