import { KST201Manager } from "./KST201Manager.js";
import net from "node:net";

const HOST = "0.0.0.0"; // listen on all interfaces
const PORT = 5555; // pick any free port

// Create server
const kst_manager = new KST201Manager();

const server = net.createServer((socket) => {
  console.log(
    "[server] client connected:",
    socket.remoteAddress,
    socket.remotePort,
  );
  socket.setNoDelay(true);
  let buf = "";

  socket.on("data", (data) => {
    buf += data.toString("utf8");
    while (true) {
      const i = buf.indexOf("\n");
      if (i < 0) break;
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      handle(socket, line);
    }
  });

  socket.on("end", () => {
    console.log("[server] client disconnected");
  });

  socket.on("error", (err) => {
    console.error("[server] socket error:", err);
  });
});

async function handle(socket, line) {
  let req;
  try {
    req = JSON.parse(line);
  } catch {
    return sendJSON(sock, { ok: false, error: "bad JSON" });
  }

  try {
    const { cmd, data } = req;
    console.log( cmd )
    switch (cmd) {
      case "connect": {
        kst_manager.connect(data);
        break;
      }
      case "home": {
        kst_manager.move_home();
        break;
      }
    }
  } catch (e) {
    console.log(e);
  }
}

// Start listening
server.listen(PORT, HOST, () => {
  console.log(`[server] listening on ${HOST}:${PORT}`);
});

server.on("error", (err) => {
  console.error("[server] error:", err);
});

// const dev_info = {
//   VID: VID,
//   PID: PID,
//   SERIAL: SERIAL,
// };

// const kst = new KST201Manager( dev_info )

// await kst.connect()
// // await kst.move_home()

// await kst.move_absolute( 20000000)
// await kst.sleep( 1009 )
// await kst.move_stop()
// // await kst.move_absolute( 20000)

// kst.dev.close()
