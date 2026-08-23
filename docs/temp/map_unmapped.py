"""Map unmapped REQs to their owning issues via the inventory."""
import json
import re
from collections import Counter

inv = open("docs/inventory/Roadmap Coverage Inventory.md").read()
rows = re.findall(
    r"\|\s*(REQ-\d{4})\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*(I\d{2})\s*\|", inv
)
issue_of = {r: i for r, i in rows}
matrix = json.loads(open("docs/temp/audit_matrix.json").read())
unmapped = [r for r in matrix if not matrix[r]["issues"]]

c = Counter(issue_of.get(r, "?") for r in unmapped)
print("unmapped REQs by owning issue:")
for i, n in c.most_common(25):
    print(f"  {i}: {n}")
print("total:", sum(c.values()))
