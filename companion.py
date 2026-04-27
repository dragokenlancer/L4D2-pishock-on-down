#!/usr/bin/env python3
"""
PiShock / OpenShock companion for Left 4 Dead 2 (VPK fallback version).

Watches L4D2's console.log for trigger lines emitted by the VScript mod
and calls the configured shocker API whenever the player gets downed.

Requirements:
    pip install requests

Usage:
    1. Fill in config.json with your credentials.
    2. Add -condebug to L4D2's Steam launch options.
    3. Run: python companion.py
    4. Launch L4D2. You should see "VScript loaded!" in this window.
"""

import json
import os
import sys
import time
import math
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("Missing dependency -- run:  pip install requests")

# When frozen by PyInstaller, __file__ points to the temp extraction dir.
# sys.executable always points to the actual .exe / script location.
_BASE_DIR   = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).parent
CONFIG_FILE = _BASE_DIR / "config.json"

# Common L4D2 install paths for auto-detection
_L4D2_REL = r"steamapps\common\Left 4 Dead 2\left4dead2\console.log"

def build_candidates(drive: str) -> list[str]:
    d = drive.rstrip(":\\/")
    return [
        fr"{d}:\Steam\{_L4D2_REL}",
        fr"{d}:\SteamLibrary\{_L4D2_REL}",
        fr"C:\Program Files (x86)\Steam\{_L4D2_REL}",
        fr"C:\Program Files\Steam\{_L4D2_REL}",
        str(Path.home() / f"Steam/{_L4D2_REL.replace(chr(92), '/')}"),
    ]

# ---- Config ------------------------------------------------------------------

def load_config():
    if not CONFIG_FILE.exists():
        sys.exit(f"config.json not found at {CONFIG_FILE}")
    with open(CONFIG_FILE, encoding="utf-8") as f:
        raw = f.read()
    return json.loads(raw)

# ---- API calls ---------------------------------------------------------------

def send_pishock(cfg, intensity: int, duration_sec: float):
    ps = cfg["pishock"]
    duration_clamped = max(1, min(15, round(duration_sec)))

    # Support both "share_codes" (list) and legacy "share_code" (string)
    codes = ps.get("share_codes") or [ps["share_code"]]

    for code in codes:
        payload = {
            "Username":  ps["username"],
            "Apikey":    ps["api_key"],
            "Code":      code,
            "Name":      ps.get("device_name", "L4D2"),
            "Op":        1,
            "Duration":  duration_clamped,
            "Intensity": intensity,
        }
        r = requests.post(
            "https://do.pishock.com/api/apioperate",
            json=payload,
            timeout=5,
        )
        print(f"  <- PiShock ({code[:8]}...) HTTP {r.status_code}: {r.text[:80]}")


def send_openshock(cfg, intensity: int, duration_sec: float):
    os_cfg = cfg["openshock"]
    duration_ms = max(300, min(30000, round(duration_sec * 1000)))

    # Support both "shocker_ids" (list) and legacy "shocker_id" (string)
    ids = os_cfg.get("shocker_ids") or [os_cfg["shocker_id"]]

    payload = {
        "shocks": [
            {
                "id":        sid,
                "type":      "Shock",
                "intensity": intensity,
                "duration":  duration_ms,
                "exclusive": True,
            }
            for sid in ids
        ],
        "customName": os_cfg.get("device_name", "L4D2"),
    }
    base = os_cfg.get("api_base", "https://api.openshock.app")
    r = requests.post(
        f"{base}/2/shockers/control",
        json=payload,
        headers={
            "Content-Type":   "application/json",
            "OpenShockToken": os_cfg["token"],
        },
        timeout=5,
    )
    print(f"  <- OpenShock HTTP {r.status_code}: {r.text[:120]}")


def send_shock(cfg, intensity: int, duration_sec: float):
    intensity = max(1, min(cfg["max_intensity"], intensity))

    # provider can be a string or a list
    raw = cfg["provider"]
    providers = [p.lower() for p in raw] if isinstance(raw, list) else [raw.lower()]

    if cfg.get("dry_run", False):
        print(f"  [DRY RUN] Would shock via {providers}: intensity={intensity}%  duration={duration_sec:.1f}s")
        return

    print(f"  Shocking: providers={providers}  intensity={intensity}%  duration={duration_sec:.1f}s")
    for provider in providers:
        try:
            if provider == "pishock":
                send_pishock(cfg, intensity, duration_sec)
            elif provider == "openshock":
                send_openshock(cfg, intensity, duration_sec)
            else:
                print(f"  [!] Unknown provider '{provider}' -- use 'pishock' or 'openshock'")
        except requests.exceptions.RequestException as e:
            print(f"  [!] Network error ({provider}): {e}")

# ---- Event handling ----------------------------------------------------------

def handle_event(event_str: str, cfg: dict, last_shock_time: list) -> list:
    """Process a PISHOCK_EVENT:... line. Returns updated last_shock_time."""
    parts = event_str.split(":")

    if len(parts) < 2:
        return last_shock_time

    etype = parts[1]

    if etype == "LOADED":
        print("[Companion] VScript loaded in game!")

    elif etype == "RESET":
        print("[Companion] Chapter transition -- down counts reset in VScript.")

    elif etype == "DOWN" and len(parts) >= 4:
        now      = time.monotonic()
        cooldown = cfg.get("cooldown_seconds", 0.5)
        if now - last_shock_time[0] < cooldown:
            print("[Companion] Cooldown active, skipping shock.")
            return last_shock_time

        down_num = int(parts[2])
        diff_idx = max(0, min(3, int(parts[3])))

        base_dur  = cfg["difficulty_base_duration"][diff_idx]
        scale_dur = cfg["difficulty_scale_duration"][diff_idx]
        duration  = min(base_dur + scale_dur * (down_num - 1), cfg.get("max_duration_seconds", 15))
        intensity = cfg["base_intensity"] + cfg["intensity_per_down"] * (down_num - 1)

        print(f"\n[Companion] Player downed! #{down_num}  diff={diff_idx}  intensity={intensity}%  duration={duration:.1f}s")
        send_shock(cfg, intensity, duration)
        last_shock_time[0] = time.monotonic()

    elif etype == "LEDGE" and len(parts) >= 3:
        if not cfg.get("ledge_shock", True):
            return last_shock_time

        now      = time.monotonic()
        cooldown = cfg.get("cooldown_seconds", 0.5)
        if now - last_shock_time[0] < cooldown:
            return last_shock_time

        diff_idx  = max(0, min(3, int(parts[2])))
        base_dur  = cfg["difficulty_base_duration"][diff_idx]
        intensity = cfg["base_intensity"]
        duration  = min(base_dur * cfg.get("ledge_duration_scale", 0.5), cfg.get("max_duration_seconds", 15))
        intensity = math.ceil(intensity * cfg.get("ledge_intensity_scale", 0.55))

        print(f"\n[Companion] Ledge grab!  diff={diff_idx}  intensity={intensity}%  duration={duration:.1f}s")
        send_shock(cfg, intensity, duration)
        last_shock_time[0] = time.monotonic()

    return last_shock_time

# ---- Log watcher -------------------------------------------------------------

def find_console_log(cfg: dict) -> str | None:
    manual = cfg.get("console_log_path", "").strip()
    if manual:
        return manual if os.path.exists(manual) else None
    drive = cfg.get("steam_drive", "C")
    for path in build_candidates(drive):
        if os.path.exists(path):
            return path
    return None


def tail_log(log_path: str, cfg: dict):
    last_shock_time = [0.0]

    print(f"[Companion] Watching: {log_path}")
    print(f"[Companion] Provider: {cfg['provider']}")
    if cfg.get("dry_run", False):
        print("[Companion] *** DRY RUN MODE -- no shocks will be sent ***")
    print("[Companion] Waiting for L4D2... (you should see 'VScript loaded!' once you start a map)\n")

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.05)
                continue

            line = line.strip()
            idx  = line.find("PISHOCK_EVENT:")
            if idx == -1:
                continue

            event_str = line[idx:]
            last_shock_time = handle_event(event_str, cfg, last_shock_time)

# ---- Entry point -------------------------------------------------------------

def main():
    print("=" * 60)
    print("  PiShock / OpenShock -- L4D2 VPK Companion")
    print("=" * 60)

    cfg = load_config()

    log_path = find_console_log(cfg)
    if not log_path:
        print("\n[!] Could not find console.log.")
        print("    1. Add  -condebug  to L4D2's Steam launch options.")
        print("    2. Launch L4D2 once so the file is created.")
        print("    3. Or set 'console_log_path' in config.json manually.")
        sys.exit(1)

    try:
        tail_log(log_path, cfg)
    except KeyboardInterrupt:
        print("\n[Companion] Stopped.")


if __name__ == "__main__":
    main()
