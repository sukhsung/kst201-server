import d2xx from "ftdi-d2xx";
import { EventEmitter } from "node:events";
import { HW } from "./util/APT_MGMSG.js";
import { sleep, hdr_short, hdr_long, hdr_w_data, wordLE, longLE } from "./util/util.js";

//CONSTANTS
//d2xx constants
const FT_BITS_8 = d2xx.FT_BITS_8;
const FT_STOP_BITS_1 = d2xx.FT_STOP_BITS_1;
const FT_PARITY_NONE = d2xx.FT_PARITY_NONE;
const FT_PURGE_RX = d2xx.FT_PURGE_RX;
const FT_PURGE_TX = d2xx.FT_PURGE_TX;
const FT_PURGE = FT_PURGE_RX | FT_PURGE_TX;
const FT_FLOW_RTS_CTS = d2xx.FT_FLOW_RTS_CTS;

// For Single Device - Hdev_infoost Communication
const DEST_USB = 0x50;
const SRC_HOST = 0x01;

export class APTManager extends EventEmitter {
  constructor(verbose) {
    super();
    this.verbose = verbose;
    this.dev = null;
    this._connecting = false;

    this.requests = [];
    this._closed = false;
  }

  /*----- Connection -----*/
  is_connected() {
    return !!this.dev?.is_connected;
  }

  async connect(dev_info) {
    if (this._connecting) return;

    this.dev_info = dev_info;
    this.dev = null;

    try {
      d2xx.setVIDPID(this.dev_info.VID, this.dev_info.PID);
      this.dev = await d2xx.openDevice({
        serial_number: this.dev_info.SERIAL.toString(),
      });
      await this.dev.setBaudRate(115200);
      await this.dev.setDataCharacteristics(
        FT_BITS_8,
        FT_STOP_BITS_1,
        FT_PARITY_NONE,
      );

      this.dev.setTimeouts(1000, 1000); // set the max TX and RX duration in ms
      await sleep(50);
      await this.dev.purge(FT_PURGE_RX | FT_PURGE_TX);
      await sleep(50);

      await this.dev.resetDevice();
      await this.dev.setFlowControl(FT_FLOW_RTS_CTS, 0, 0);
      await this.dev.setRts();

      if (await this.dev_check()) {
        await this.init_dev();
        await this.write_short(HW.NO_FLASH_PROGRAMING);
      } else {
        this.dev = null;
      }
    } catch (e) {
      console.log(e.message);
    } finally {
      this._connecting = false;
      return;
    }
  }

  async init_dev() {
    return await this._init_dev();
  }

  async dev_check() {
    return await this._dev_check();
  }
  async close() {
    this.log("Closing");
    this._closed = true; // lets the loop wind down
    this.dev?.close();
  }

  /*----- Read & Write -----*/
  async readExact(n, timeoutMs = 1000) {
    const out = Buffer.alloc(n);
    let off = 0;
    const end = Date.now() + timeoutMs;
    while (off < n && !this._closed) {
      // if (Date.now() > end) throw new Error(`timeout ${off}/${n}`);
      if (Date.now() > end) return out;
      const chunk = Buffer.from(await this.dev.read(n - off));
      if (chunk.length) {
        chunk.copy(out, off);
        off += chunk.length;
      } else {
        await sleep(5);
      }
    }
    return out;
  }
async  waitUntil(header, timeoutMs = 1000) {
  if (!Buffer.isBuffer(header)) throw new TypeError("header must be a Buffer");
  if (header.length === 0) throw new Error("header must not be empty");

  const deadline = Date.now() + timeoutMs;
  const winLen = header.length;

  const window = Buffer.allocUnsafe(winLen);
  let filled = 0;

  while (!this._closed) {
    if (Date.now() > deadline) {
      return false; // timeout
    }

    const chunk = Buffer.from(await this.dev.read(1));
    if (chunk.length === 0) {
      await sleep(50);
      continue;
    }
    const byte = chunk[0];

    if (filled < winLen) {
      window[filled++] = byte;
      if (filled < winLen) continue; // not enough to compare yet
    } else {
      window.copy(window, 0, 1);
      window[winLen - 1] = byte;
    }

    if (window.equals(header)) {
      return true; // match!
    }
  }

  return false; // closed
}


  async write_short(id, p1 = 0, p2 = 0, d = DEST_USB, s = SRC_HOST) {
    const buf = hdr_short(id, p1, p2, d, s);
    const res = await this.dev.write(buf);

    // this.log(`Wrote ${res} Bytes`);
    // console.log(buf);
  }

  async write_long(id, data, d = DEST_USB, s = SRC_HOST) {
    const buf = hdr_w_data(id, data, d, s);
    const res = await this.dev.write(buf);

    // this.log(`Wrote ${res} Bytes`);
    // console.log(buf);
  }

  async purge() {
    await this.dev.purge(FT_PURGE);
  }

  /*----- Communication Loop-----*/
  start_comm() {
    (async () => {
      try {
        let counter = 0;
        while (!this._closed) {
          // this.log(`Counter: ${counter}, NumReq: ${this.requests.length}`);
          if (this.requests.length > 0) {
            await this.process_request();
          } else {
            await this.process_regular();
          }
          counter++;

          await sleep(50);
        }
      } catch (e) {
        console.error("start_comm loop error:", e);
      } finally {
      }
    })();
  }

  add_to_requests(req) {
    this.requests.push(req);
  }

  async process_request() {
    const req = this.requests.shift();
    await this._process_request(req);
  }

  async process_regular() {
    await this._process_regular();
    return;
  }

  /*---- Utility ----*/
  log(msg) {
    if (this.verbose >= 2) {
      console.log(`[APTManager]: ${msg}`);
    }
  }

  /*----- Abstract -----*/
  async _init_dev() {
    return true;
  }
  async _dev_check() {
    return await true;
  }
  async _process_request() {
    return;
  }
  async _process_regular() {
    return;
  }
}
