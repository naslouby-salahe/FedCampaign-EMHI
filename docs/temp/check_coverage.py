"""Check REQ coverage across all closed issues."""
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path("/home/naslouby/Projects/FedCampaign-EMHI")
m = json.loads((ROOT / "docs/temp/audit_matrix.json").read_text())
all_reqs = set(m)

covered: set[str] = set()
for n in range(151, 190):
    body = subprocess.run(
        ["gh", "issue", "view", str(n), "--repo", "naslouby-salahe/FedCampaign-EMHI",
         "--json", "body", "-q", ".body"],
        capture_output=True, text=True,
    ).stdout
    covered |= set(re.findall(r"REQ-\d{4}", body))

print("inventory:", len(all_reqs), "| covered by issues:", len(covered & all_reqs))
missing = sorted(all_reqs - covered)
print("unmapped:", len(missing))

c = Counter(m[r]["desc"].split("(")[0].strip()[:50] for r in missing)
for sec, n in c.most_common(12):
    print(f"  {n:4d} {sec}")
