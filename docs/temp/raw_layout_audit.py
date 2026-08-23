"""Raw-data layout audit: does data/raw/ton_iot_network exist as required by the config contract?

The roadmap locks `datasets.primary.raw_directory = data/raw/ton_iot_network` and
`data/raw` is a symlink to the shared raw tree. The actual TON-IoT release lives at
`data/raw/TON-IoT/`. This script checks whether the declared directory exists and, if
not, reports what a non-mutating fix (creating a symlink INSIDE the shared tree is
forbidden by the raw-immutability rule) would require.
"""
from pathlib import Path

raw = Path("data/raw")
print("data/raw resolves to:", raw.resolve())
print()

for name in ("ton_iot_network", "edge_iiotset"):
    target = raw / name
    print(f"declared: {target}")
    print("  exists:", target.exists())
print()
print("actual release directories:")
for p in sorted(raw.iterdir()):
    if p.is_dir():
        print("  ", p.name)
