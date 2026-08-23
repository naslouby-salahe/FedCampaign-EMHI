"""Verify closure + checklist state of issues 136-163 (M01-M05)."""
import subprocess

for n in range(136, 164):
    state = subprocess.run(
        ["gh", "issue", "view", str(n), "--repo", "naslouby-salahe/FedCampaign-EMHI",
         "--json", "state", "-q", ".state"],
        capture_output=True, text=True,
    ).stdout.strip()
    body = subprocess.run(
        ["gh", "issue", "view", str(n), "--repo", "naslouby-salahe/FedCampaign-EMHI",
         "--json", "body", "-q", ".body"],
        capture_output=True, text=True,
    ).stdout
    unchecked = body.count("- [ ]")
    print(f"{n}: {state} unchecked={unchecked}")
