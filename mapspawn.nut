// mapspawn.nut — PiShock/OpenShock companion (polling approach)
//
// Event hooks via __CollectGameEventCallbacks don't fire reliably from mapspawn
// because the script runs before the director initialises. Instead we attach a
// Think function to worldspawn that polls survivor incapacitation state every
// 0.25 seconds — worldspawn persists for the entire map lifetime.

local ws = Entities.FindByClassname(null, "worldspawn")
if (ws == null) {
    printl("PISHOCK_EVENT:ERROR:no_worldspawn")
    return
}

ws.ValidateScriptScope()
local S = ws.GetScriptScope()

// ─── Persistent state (lives in worldspawn scope) ─────────────────────────────

S.psIncapStates <- {}   // userid -> last known incap state (0 or 1)
S.psDownCounts  <- {}   // userid -> number of times downed this chapter
S.psLedgeStates <- {}   // userid -> last known ledge-hang state

S.psGetDiff <- function() {
    local d = Convars.GetStr("z_difficulty")
    if (d == null)          return 1
    if (d == "Easy")        return 0
    if (d == "Normal")      return 1
    if (d == "Hard")        return 2
    if (d == "Impossible")  return 3
    return 1
}

// ─── Think — runs every 0.25 s ────────────────────────────────────────────────

S.PiShockPoll <- function() {
    local ent = null
    while ((ent = Entities.FindByClassname(ent, "player")) != null) {
        // human survivors only (skip bots and infected)
        if (NetProps.GetPropInt(ent, "m_iTeamNum") != 2) continue
        if (NetProps.GetPropInt(ent, "m_fFlags") & 32) continue  // FL_FAKECLIENT

        local uid = NetProps.GetPropInt(ent, "m_iUserID").tostring()

        // ── Incapacitation check ──────────────────────────────────────────────
        local incap = NetProps.GetPropInt(ent, "m_isIncapacitated")
        local prevIncap = (uid in psIncapStates) ? psIncapStates[uid] : 0

        if (incap == 1 && prevIncap == 0) {
            // Transition: upright → downed
            if (!(uid in psDownCounts)) psDownCounts[uid] <- 0
            psDownCounts[uid]++
            printl("PISHOCK_EVENT:DOWN:" + psDownCounts[uid] + ":" + psGetDiff())
        }
        psIncapStates[uid] <- incap

        // ── Ledge-hang check ─────────────────────────────────────────────────
        local ledge = NetProps.GetPropInt(ent, "m_isHangingFromLedge")
        local prevLedge = (uid in psLedgeStates) ? psLedgeStates[uid] : 0

        if (ledge == 1 && prevLedge == 0) {
            printl("PISHOCK_EVENT:LEDGE:" + psGetDiff())
        }
        psLedgeStates[uid] <- ledge
    }

    return 0.25   // reschedule in 0.25 s
}

AddThinkToEnt(ws, "PiShockPoll")
printl("PISHOCK_EVENT:LOADED")
