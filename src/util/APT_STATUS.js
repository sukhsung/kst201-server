// ---- Status bit masks (32-bit) ----
const ST_FWD_HW_LIMIT = 0x00000001;
const ST_REV_HW_LIMIT = 0x00000002;
const ST_FWD_SW_LIMIT = 0x00000004;
const ST_REV_SW_LIMIT = 0x00000008;
const ST_MOV_FWD = 0x00000010;
const ST_MOV_REV = 0x00000020;
const ST_JOG_FWD = 0x00000040;
const ST_JOG_REV = 0x00000080;
const ST_MOTOR_CONN = 0x00000100;
const ST_HOMING = 0x00000200;
const ST_HOMED = 0x00000400;
const ST_INTERLOCK_EN = 0x00001000;

// useful composites
const ST_ANY_MOVE =
  ST_MOV_FWD | ST_MOV_REV | ST_JOG_FWD | ST_JOG_REV | ST_HOMING;
const ST_ANY_LIMIT =
  ST_FWD_HW_LIMIT | ST_REV_HW_LIMIT | ST_FWD_SW_LIMIT | ST_REV_SW_LIMIT;

// ---- Helpers ----
export function parseStatus(status32) {
  return {
    homing: !!(status32 & ST_HOMING),
    homed: !!(status32 & ST_HOMED),
    moving: !!(status32 & ST_ANY_MOVE),
    limit: !!(status32 & ST_ANY_LIMIT),
  };
}