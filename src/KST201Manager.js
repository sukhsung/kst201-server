import { APTManager } from "./APTManager.js";
import {HW, MOT} from "./util/APT_MGMSG.js"
import { parseStatus } from "./util/APT_STATUS.js";
import { sleep, hdr_short, hdr_long, hdr_w_data, wordLE, longLE } from "./util/util.js";


const USB = 0x50;
const HOST = 0x01;

export class KST201Manager extends APTManager {
  constructor(verbose = 2) {
    super(verbose);


    this.MOVE_HOMED = hdr_short( MOT.MOVE_HOMED, 1, 0, HOST, USB);
    this.MOVE_COMPLETED = hdr_long( MOT.MOVE_COMPLETED, 14, HOST, USB);
    this.GET_STATUSUPDATE = hdr_long( MOT.GET_STATUSUPDATE, 28, HOST, USB);
    // this.MOVE_STOPPED = hdrWithData( MOT.MOVE_STOPPED, 14, HOST, USB);

  }

  async _process_regular(){
    return
  }

  async _process_request(req) {
    const { cmd, data } = req;
    this.log(
      `Process: ${cmd} ${data !== undefined ? JSON.stringify(data) : ""}`,
    );
    await this.purge()
    try {
      if (cmd == "get_status") {
        await this.get_status();
      } else if (cmd === "move_home") {
        await this.move_home();
      } else if (cmd === "move_absolute") {
        await this.move_absolute(data);
      } else if (cmd === "move_relative") {
        await this.move_relative(data);
      } else if (cmd === "move_stop") {
        await this.move_stop();
      } else {
        this.log("Unknown Command: " + cmd);
      }
    } catch (e) {
      console.error("process_request error:", e);
    }
  }

  async get_status() {
    try {
      await this.write_short(MOT.REQ_STATUSUPDATE);
      const resp = await this.waitUntil(this.GET_STATUSUPDATE, 60_000);

      if (resp) {
        const data = await this.readExact(28, 200);
        const pos = data.readInt32LE(2);
        const status = parseStatus(data.readUInt32LE(10));
        status.position = pos;
        console.log(status)
        this.emit("send", status);
      }
      else {
        console.log( hdr)
      }
    } catch (e) {
      console.log("Error: " + e.message);
      return -1;
    }
  }

  async move_stop() {
    try {
      this.log("Stopping");
      await this.write_short(MOT.MOVE_STOP, 1, 1);
    } catch (e) {
      console.log("Error: " + e.message);
      return -1;
    }
  }

  async move_relative(count) {
    try {
      this.log("Move Relative: " + count);
      const data = Buffer.concat([wordLE(1), longLE(count)]); // [Chan WORD][AbsPos LONG]
      await this.write_long(MOT.MOVE_RELATIVE, data);
      const resp = await this.waitUntil(this.MOVE_COMPLETED, 30_000);
      if ( resp ){
        await this.readExact(14,10_000)
        this.get_status()
      }
    } catch (e) {
      console.log("Error: " + e.message);
      return -1;
    }
  }

  async move_absolute(count) {
    try {
      this.log("Move Absolute: " + count);
      const data = Buffer.concat([wordLE(1), longLE(count)]); // [Chan WORD][AbsPos LONG]
      await this.write_long(MOT.MOVE_ABSOLUTE, data);
      const resp = await this.waitUntil(this.MOVE_COMPLETED, 30_000);
      if ( resp ){
        await this.readExact(14)
        this.get_status()
      }
    } catch (e) {
      console.log("Error: " + e.message);
      return -1;
    }
  }

  async move_home() {
    try {
      await this.write_short(MOT.MOVE_HOME);
      const resp = await this.waitUntil(this.MOVE_HOMED, 60_000)
      if ( resp ){
        this.get_status()
      }
    } catch (e) {
      console.log("Error: " + e.message);
      return false;
    }
  }

  async _dev_check() {
    try {
      const serial = await this.get_serial();
      console.log("SERIAL: "+serial)
      if (serial === this.dev_info.SERIAL) {
        this.log("dev_check passed");
        return true;
      } else {
        this.log("dev_check failed");
        return false;
      }
    } catch (e) {
      console.log("Error: " + e.message);
      return false;
    }
  }

  async get_serial() {
    await this.purge();
    await this.write_short(HW.REQ_INFO);

    const hdr = await this.readExact(6);
    if (hdr.readInt16LE(0) === HW.GET_INFO) {
      const data = await this.readExact(84);
      return data.readInt32LE(0);
    } else {
      return -1;
    }
  }

  log(msg) {
    if (this.verbose >= 1) {
      console.log(`[KST201Manager]: ${msg}`);
    }
  }
}
