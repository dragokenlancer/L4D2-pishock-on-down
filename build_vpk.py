#!/usr/bin/env python3
"""
Packages mapspawn.nut into a L4D2 addon VPK.

Usage:
    pip install vpk
    python build_vpk.py

Output: pishock_companion_dir.vpk  (drop this into left4dead2/addons/)
"""

import sys
import shutil
import tempfile
from pathlib import Path

try:
    import vpk
except ImportError:
    sys.exit("Missing dependency — run:  pip install vpk")

HERE    = Path(__file__).parent
NUT_SRC = HERE / "mapspawn.nut"
OUT     = HERE / "pishock_companion_dir.vpk"

if not NUT_SRC.exists():
    sys.exit(f"mapspawn.nut not found at {NUT_SRC}")

# vpk.new() needs a real directory on disk with the game-relative structure
with tempfile.TemporaryDirectory() as tmp:
    dest = Path(tmp) / "scripts" / "vscripts"
    dest.mkdir(parents=True)
    shutil.copy(NUT_SRC, dest / "mapspawn.nut")

    pak = vpk.new(tmp)
    pak.version = 1  # L4D2 expects VPK v1, not v2 (CS:GO+)
    pak.save(str(OUT))

print(f"Built: {OUT}  ({OUT.stat().st_size} bytes)")
print(f"\nInstall: copy  pishock_companion_dir.vpk  into  left4dead2/addons/")
