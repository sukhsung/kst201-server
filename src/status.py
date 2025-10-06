# util/status.py

# ---- Status bit masks (32-bit) ----
ST_FWD_HW_LIMIT   = 0x00000001
ST_REV_HW_LIMIT   = 0x00000002
ST_FWD_SW_LIMIT   = 0x00000004
ST_REV_SW_LIMIT   = 0x00000008
ST_MOV_FWD        = 0x00000010
ST_MOV_REV        = 0x00000020
ST_JOG_FWD        = 0x00000040
ST_JOG_REV        = 0x00000080
ST_MOTOR_CONN     = 0x00000100
ST_HOMING         = 0x00000200
ST_HOMED          = 0x00000400
ST_INTERLOCK_EN   = 0x00001000

# useful composites
ST_ANY_MOVE  = ST_MOV_FWD | ST_MOV_REV | ST_JOG_FWD | ST_JOG_REV | ST_HOMING
ST_ANY_LIMIT = ST_FWD_HW_LIMIT | ST_REV_HW_LIMIT | ST_FWD_SW_LIMIT | ST_REV_SW_LIMIT

# ---- Helpers ----
def parseStatus(status32: int) -> dict[str, bool]:
    """Return high-level flags from a 32-bit status word."""
    return {
        "homing": bool(status32 & ST_HOMING),
        "homed":  bool(status32 & ST_HOMED),
        "moving": bool(status32 & ST_ANY_MOVE),
        "limit":  bool(status32 & ST_ANY_LIMIT),
    }
