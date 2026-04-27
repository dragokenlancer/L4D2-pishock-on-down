# L4D2 Shocker Companion — Setup Guide

## What's in this folder

| File | Purpose |
|------|---------|
| `pishock_companion.exe` | The companion — run this while playing |
| `config.json` | Your credentials and shock settings |
| `pishock_companion_dir.vpk` | The L4D2 mod (install once) |
| `build_vpk.py` | Rebuilds the VPK if you edit `mapspawn.nut` |

---

## Step 1 — Install the VPK mod

1. Copy `pishock_companion_dir.vpk` into:
   ```
   <Steam>\steamapps\common\Left 4 Dead 2\left4dead2\addons\
   ```
2. In Steam, right-click **Left 4 Dead 2 → Properties → General** and add to launch options:
   ```
   -condebug
   ```

That's it for the game side. The mod loads automatically on every map.

---

## Step 2 — Fill in config.json

Open `config.json` in Notepad and edit the relevant section(s).

### OpenShock
Get your token and shocker ID from **openshock.app → API Keys / Shockers**.
```json
"openshock": {
    "token":       "your-token-here",
    "shocker_ids": ["your-shocker-id"],
    "device_name": "L4D2",
    "api_base":    "https://api.openshock.app"
}
```
To also shock a friend, add their shocker ID to the list:
```json
"shocker_ids": ["your-id", "friends-id"]
```

### PiShock
Get credentials from **pishock.com → Account → API**.
```json
"pishock": {
    "username":    "YourUsername",
    "api_key":     "your-api-key",
    "share_codes": ["your-share-code"]
}
```
To also shock a friend, add their share code:
```json
"share_codes": ["your-code", "friends-code"]
```

### Provider
- Only you (OpenShock): `"provider": "openshock"`
- Only friend (PiShock): `"provider": "pishock"`
- Both at once: `"provider": ["openshock", "pishock"]`

### Steam drive
If Steam is not on your C: drive, set:
```json
"steam_drive": "E"
```

---

## Step 3 — Run the companion

Double-click **`pishock_companion.exe`**.

You should see:
```
[Companion] Watching: E:\SteamLibrary\...\console.log
[Companion] Waiting for L4D2...
```

Start L4D2 and load a campaign map. You should then see:
```
[Companion] VScript loaded in game!
```

The companion is now active. Get downed → get shocked.

---

## Shock settings (config.json)

| Setting | Default | What it does |
|---------|---------|-------------|
| `base_intensity` | 5 | Intensity (%) on first down |
| `intensity_per_down` | 5 | Added per additional down |
| `max_intensity` | 50 | Hard cap on intensity |
| `max_duration_seconds` | 3 | Hard cap on duration |
| `ledge_shock` | true | Shock on ledge grabs |
| `cooldown_seconds` | 0.5 | Minimum gap between shocks |
| `dry_run` | false | Set to `true` to test without shocking |

Duration scales with difficulty (Easy → Expert) and how many times you've gone down that chapter.

---

## Troubleshooting

**"VScript loaded" never appears**
- Make sure `-condebug` is in launch options and you restarted L4D2 after adding it.
- Make sure the VPK is in the `addons` folder (not a subfolder).

**"Could not find console.log"**
- Set `steam_drive` to the correct drive letter in `config.json`.
- Or set `console_log_path` to the full path of `console.log`.

**Shocks fire but friend doesn't feel them**
- For OpenShock: make sure their shocker ID is in `shocker_ids` and your token has control access to it.
- For PiShock: make sure their share code is in `share_codes`.
