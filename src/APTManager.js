import d2xx from "ftdi-d2xx";
import { EventEmitter } from "node:events";

//CONSTANTS
//d2xx constants
const FT_BITS_8 = d2xx.FT_BITS_8;
const FT_STOP_BITS_1 = d2xx.FT_STOP_BITS_1;
const FT_PARITY_NONE = d2xx.FT_PARITY_NONE;
const FT_PURGE_RX = d2xx.FT_PURGE_RX;
const FT_PURGE_TX = d2xx.FT_PURGE_TX;
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
    this.connected = false;
  }

  async dev_check() {
    return await this._dev_check();
  }

  async init_dev() {
    return await this._init_dev();
  }

  async connect(dev_info) {
    if (this._connecting) return;

    this.dev_info = dev_info;
    this.dev = null;
    this.connected = false;

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

      await this.sleep(50);
      await this.dev.purge(FT_PURGE_RX | FT_PURGE_TX);
      await this.sleep(50);

      await this.dev.resetDevice();
      await this.dev.setFlowControl(FT_FLOW_RTS_CTS, 0, 0);
      await this.dev.setRts();

      if (await this.dev_check()) {
        await this.init_dev();
        this.connected = true;
      } else {
        this.connected = false;
        this.dev = null;
      }
    } finally {
      this._connecting = false;
      return;
    }
  }

  // Protocol Helpers
  hdrOnly(id, p1 = 0, p2 = 0, d = DEST_USB, s = SRC_HOST) {
    const b = Buffer.alloc(6);
    b.writeUInt16LE(id, 0); // bytes 0–1: message ID (LE)
    b[2] = p1 & 0xff; // byte 2: param1
    b[3] = p2 & 0xff; // byte 3: param2
    b[4] = d & 0xff; // byte 4: destination
    b[5] = s & 0xff; // byte 5: source
    return b;
  }

  hdrWithData(id, data, d = DEST_USB, s = SRC_HOST) {
    const b = Buffer.alloc(6);
    b.writeUInt16LE(id, 0);
    b.writeUInt16LE(data.length, 2);
    b[4] = (d | 0x80) & 0xff; // MSB set => data following
    b[5] = s & 0xff;
    return Buffer.concat([b, data]);
  }

  async readExact(n, timeoutMs = 1000) {
    const out = Buffer.alloc(n);
    let off = 0;
    const end = Date.now() + timeoutMs;
    while (off < n) {
      if (Date.now() > end) throw new Error(`read timeout ${off}/${n}`);
      const resp = await this.dev.read(n - off);

      let chunk = Buffer.isBuffer(resp) ? resp : Buffer.from(resp || []);

      if (chunk.length) {
        chunk.copy(out, off);
        off += chunk.length;
      } else await new Promise((r) => setTimeout(r, 5));
    }
    return out;
  }

  async recvOne(timeoutMs = 1000) {
    const hdr = await this.readExact(6, timeoutMs);
    const msgId = hdr.readUInt16LE(0);
    const hasData = (hdr.readUInt8(4) & 0x80) !== 0;
    let data = Buffer.alloc(0);
    if (hasData) {
      const len = hdr.readUInt16LE(2);
      data = await this.readExact(len, timeoutMs);
    }
    return { msgId, hdr, data };
  }

  async waitFor(wantedIds, timeoutMs = 30000) {
    const wanted = new Set(wantedIds);
    const end = Date.now() + timeoutMs;
    for (;;) {
      const left = end - Date.now();
      if (left <= 0) throw new Error("waitFor timeout");
      try {
        const m = await this.recvOne(Math.max(50, left));
        if (wanted.has(m.msgId)) return m;
        // ignore 0x0481 periodic status frames here
      } catch (e) {
        if (/timeout/i.test(String(e))) continue;
        throw e;
      }
    }
  }

  wordLE(n) {
    const b = Buffer.alloc(2);
    b.writeUInt16LE(n >>> 0, 0);
    return b;
  }
  longLE(n) {
    const b = Buffer.alloc(4);
    b.writeInt32LE(n | 0, 0);
    return b;
  }

  async sleep(ms) {
    // this.log(`Sleeping for ${ms} ms`);
    return await new Promise((res) => setTimeout(res, ms));
  }

  log(msg) {
    if (this.verbose >= 2) {
      console.log(`[APTManager]: ${msg}`);
    }
  }
}
