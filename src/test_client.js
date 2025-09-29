import net from 'node:net';

const HOST = '127.0.0.1'
const PORT = 5555

function connect() {
  return new Promise((resolve, reject) => {
    const sock = net.connect(PORT, HOST, () => resolve(sock));
    sock.setNoDelay(true);
    sock.on('error', reject);
  });
}

function sendJSON(sock, obj) {
  return new Promise((resolve, reject) => {
    const line = JSON.stringify(obj) + '\n';
    sock.write(line, err => (err ? reject(err) : resolve()));
  });
}




const VID = 0x0403;
const PID = 0xfaf0;
const SERIAL = 26006611;

const dev_info = {VID:VID, PID:PID, SERIAL:SERIAL}
const payload = {cmd:"connect", data:dev_info}

const socket = await connect()
await sendJSON( socket, payload)

await await new Promise((res) => setTimeout(res, 2000));
await sendJSON( socket, {cmd:"home", data:""})