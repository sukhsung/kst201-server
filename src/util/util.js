export async function sleep(ms) {
  // this.log(`Sleeping for ${ms} ms`);
  return await new Promise((res) => setTimeout(res, ms));
}

export function wordLE(n) {
  const b = Buffer.alloc(2);
  b.writeUInt16LE(n >>> 0, 0);
  return b;
}
export function longLE(n) {
  const b = Buffer.alloc(4);
  b.writeInt32LE(n | 0, 0);
  return b;
}

// Protocol Helpers
export function hdr_short(id, p1, p2, d, s) {
  const b = Buffer.alloc(6);
  b.writeUInt16LE(id, 0); // bytes 0–1: message ID (LE)
  b[2] = p1 & 0xff; // byte 2: param1
  b[3] = p2 & 0xff; // byte 3: param2
  b[4] = d & 0xff; // byte 4: destination
  b[5] = s & 0xff; // byte 5: source
  return b;
}

export function hdr_long(id, data_length, d, s) {
  const b = Buffer.alloc(6);
  b.writeUInt16LE(id, 0);
  b.writeUInt16LE( data_length, 2);
  b[4] = (d | 0x80) & 0xff; // MSB set => data following
  b[5] = s & 0xff;
  return b;
}

export function hdr_w_data(id, data, d, s) {
  const b = hdr_long(id, data.length, d, s);
  return Buffer.concat([b, data]);
}
