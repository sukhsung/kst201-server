import { APTManager } from "./APTManager.js";

const MOT_MOVE_HOME = 0X0443
const MOT_MOVE_HOMED = 0X0444
const MOT_MOVE_ABSOLUTE = 0x0453
const MOT_MOVE_COMPLETED = 0x0464
const MOT_MOVE_STOP = 0x0465
const MOT_MOVE_STOPPED = 0x0466

export class KST201Manager extends APTManager {
  constructor( verbose = 2) {
    super( verbose);
  }

  async move_stop(  ) {
    try {
      this.log("Stopping")
      await this.dev.write(this.hdrOnly(MOT_MOVE_STOP, 1, 1));
      // await this.waitFor([MOT_MOVE_STOPPED], 60000);
      return true
    } catch (e) {
      console.log(e.message);
      return false
    }
  }

  async move_absolute( count ) {
    try {
      this.log("Moving")
      const absData = Buffer.concat([this.wordLE(1), this.longLE(count)]); // [Chan WORD][AbsPos LONG]
      await this.dev.write(this.hdrWithData(MOT_MOVE_ABSOLUTE, absData));
      // await this.waitFor([MOT_MOVE_COMPLETED], 60000);
      return true
    } catch (e) {
      console.log(e.message);
      return false
    }
  }

  async move_home() {
    try {
      this.log("Homing")
      await this.dev.write(this.hdrOnly(MOT_MOVE_HOME));
      // await this.waitFor([MOT_MOVE_HOMED], 60000);
      return true
    } catch (e) {
      console.log(e.message);
      return false
    }
  }
  
  async _init_dev() {
    return
  }

  async _dev_check() {
    try {
      // REQ HW INFO -> expect GET (0x0006) with ~84B payload
      console.log("[apt] HW_REQ_INFO (0x0005)");
      await this.dev.write(this.hdrOnly(0x0005));
      const info = await this.recvOne(1000);
      const serial = info.data.readInt32LE(0);
      if (serial === this.dev_info.SERIAL) {
        this.log("dev_check passed");
        return true;
      } else {
        this.log("dev_check failed");
        return false;
      }
    } catch (e) {
      console.log(e.message);
      return false;
    }
  }

  log(msg) {
    if (this.verbose >= 1) {
      console.log(`[KST201Manager]: ${msg}`);
    }
  }
}
