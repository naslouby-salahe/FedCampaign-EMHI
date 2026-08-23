"""Cross-check the milestone audit doc's REQ-to-issue mapping against the inventory."""
import json
import re
from pathlib import Path

ROOT = Path("/home/naslouby/Projects/FedCampaign-EMHI")
audit = (ROOT / "docs/inventory/Milestone Audit.md").read_text()
pairs = re.findall(r"`(REQ-\d{4})` — issue `(I\d{2})`", audit)
print("REQ->issue pairs in audit doc:", len(pairs))

matrix = json.loads((ROOT / "docs/temp/audit_matrix.json").read_text())
all_reqs = set(matrix)
mapped_reqs = {r for r, _ in pairs}
print("inventory REQs:", len(all_reqs), "| audit-doc mapped:", len(mapped_reqs & all_reqs))

missing = sorted(all_reqs - mapped_reqs)
print("REQs not in audit doc:", len(missing))
for r in missing[:10]:
    print("  ", r)

# Distribution by owning issue
from collections import Counter
by_issue = Counter(i for _, i in pairs)
print("\nREQs per issue (top 15):")
for issue, n in by_issue.most_common(15):
    print(f"  {issue}: {n}")
