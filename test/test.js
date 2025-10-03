// test.js
import d2xx from 'ftdi-d2xx';

// ---- Command IDs ----
const MGMSG_HW_REQ_INFO = 0x0005;
const MGMSG_HW_GET_INFO = 0x0006;
const MOT_MOVE_ABSOLUTE = 0x0453;

const DEST_USB = 0x50;
const SRC_HOST = 0x01;

// ---- Helpers ----
function hdrOnly(id, p1 = 0, p2 = 0, d = DEST_USB, s = SRC_HOST) {
  const b = Buffer.alloc(6);
  b.writeUInt16LE(id, 0);
  b[2] = p1 & 0xff;
  b[3] = p2 & 0xff;
  b[4] = d & 0xff;
  b[5] = s & 0xff;
  return b;
}

function hdrWithData(id, data, d = DEST_USB, s = SRC_HOST) {
  const b = Buffer.alloc(6);
  b.writeUInt16LE(id, 0);
  b.writeUInt16LE(data.length, 2);
  b[4] = (d | 0x80) & 0xff;
  b[5] = s & 0xff;
  return Buffer.concat([b, data]);
}

async function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

async function main() {
  // ---- open device ----
d2xx.setVIDPID(0x0403, 0xfaf0);
  const dev = await d2xx.openDevice({ serial_number: '26006611'}); // or serial_number: "12345678"
  await dev.setBaudRate(115200);
  await dev.setDataCharacteristics(d2xx.FT_BITS_8, d2xx.FT_STOP_BITS_1, d2xx.FT_PARITY_NONE);
  await dev.purge(d2xx.FT_PURGE_RX | d2xx.FT_PURGE_TX);
  await sleep(50);
  await dev.resetDevice();
  await dev.setFlowControl(d2xx.FT_FLOW_RTS_CTS, 0, 0);
  await dev.setRts();

  // ---- Send REQ_INFO ----
  let req = hdrOnly(MGMSG_HW_REQ_INFO);
  console.log("Sending REQ_INFO...");
  console.log(req.toString('hex'));
  await dev.purge(d2xx.FT_PURGE_RX | d2xx.FT_PURGE_TX);
  await dev.write(req);

  let hdr = Buffer.from(await dev.read(6));
  let msgId = hdr.readUInt16LE(0);
  if (msgId !== MGMSG_HW_GET_INFO) {
    console.log(`Unexpected header: 0x${msgId.toString(16).padStart(4, '0')}`);
  }
  let data = Buffer.from(await dev.read(4));
  let serial = data.readUInt32LE(0);
  console.log("Device serial:", serial);

  // ---- Send MOVE_ABSOLUTE 1600000 ----
  const target = 0;
  const chan = Buffer.alloc(2); chan.writeUInt16LE(1, 0);
  const pos = Buffer.alloc(4); pos.writeInt32LE(target, 0);
  const payload = Buffer.concat([chan, pos]);
  const frame = hdrWithData(MOT_MOVE_ABSOLUTE, payload);

  console.log("Sending MOVE_ABSOLUTE 1600000...");
  await dev.purge(d2xx.FT_PURGE_RX | d2xx.FT_PURGE_TX);
  await dev.write(frame);

  await sleep(5000);

  // ---- Send REQ_INFO again ----
  req = hdrOnly(MGMSG_HW_REQ_INFO);
  console.log("Sending REQ_INFO again...");
  console.log(req.toString('hex'));
  await dev.purge(d2xx.FT_PURGE_RX | d2xx.FT_PURGE_TX);
  await dev.write(req);

  hdr = Buffer.from(await dev.read(6));
  msgId = hdr.readUInt16LE(0);
  if (msgId !== MGMSG_HW_GET_INFO) {
    console.log(`Unexpected header: 0x${msgId.toString(16).padStart(4, '0')}`);
  }
  data = Buffer.from(await dev.read(4));
  serial = data.readUInt32LE(0);
  console.log("Device serial (again):", serial);

  await dev.close();
}

main().catch(e => {
  console.error("Error:", e);
});
