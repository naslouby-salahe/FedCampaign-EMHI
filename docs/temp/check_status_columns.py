"""Check the MAPPED/READY status columns in the coverage inventory."""
import re
from collections import Counter
from pathlib import Path

inv = Path("/home/naslouby/Projects/FedCampaign-EMHI/docs/inventory/Roadmap Coverage Inventory.md").read_text()
rows = re.findall(
    r"\|\s*(REQ-\d{4})\s*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*([A-Za-z ]+?)\s*\|\s*([A-Za-z ]+?)\s*\|",
    inv,
)
print("parsed rows:", len(rows))
status = Counter((mapped.strip(), ready.strip()) for _, mapped, ready in rows)
for k, n in status.most_common():
    print(f"{n:5d}  {k}")
