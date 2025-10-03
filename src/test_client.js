import net from 'node:net';
import { sleep } from "./util/util.js";

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

const count_per_um = 2184.56064

const dev_info = {VID:VID, PID:PID, SERIAL:SERIAL}
const payload = {cmd:"connect", data:dev_info}

const socket = await connect()
await sendJSON( socket, payload)

await sendJSON( socket, {cmd:"start_comm"})
// await sendJSON( socket, {cmd:"move_home"})

await sleep( 1000)
// await sendJSON( socket, {cmd:"move_relative", data: Math.round(3000*count_per_um)})
// await sleep( 10000)
await sendJSON( socket, {cmd:"move_absolute", data:4369121})
// await sleep( 10000)
// await sendJSON( socket, {cmd:"move_absolute", data:20000})
// await 

// await await new Promise((res) => setTimeout(res, 2000));
// await sendJSON( socket, {cmd:"move_home", data:""})