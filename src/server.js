// server.js
import net from "node:net";
import { KST201Manager } from "./KST201Manager.js";
import { SocketHandler } from "./SocketHandler.js";

const HOST = "0.0.0.0";
const PORT = 5555;

const SERVER_SETTINGS = {
  KEEPALIVE_ENABLED: true,
  KEEPALIVE_DELAY_MS: 30_000,
  IDLE_TIMEOUT_MS: 5 * 60_000, // close idle sockets after 5 min
  MAX_LINE_BYTES: 2 * 1024 * 1024, // 2MB per line cap
};

// --- Single-connection gate ---

let activeHandler = null; // exactly one at a time

const server = net.createServer((socket) => {
  if (activeHandler && !activeHandler.closed) {
    // Already busy: politely refuse
    socket.end('{"error":"busy"}\n');
    return;
  }

  // Accept this client
  const mgr = new KST201Manager();
  mgr.socket = socket;
  const on_release = () => {
    activeHandler = null;
  };

  activeHandler = new SocketHandler(socket, mgr, SERVER_SETTINGS, on_release);
});

// Optional hint; not enforcement by itself, so we enforce manually above.
server.maxConnections = 1;

server.listen(PORT, HOST, () => {
  console.log(`[server] listening on ${HOST}:${PORT}`);
});

server.on("error", (err) => {
  console.error("[server] error:", err);
});

// Graceful shutdown
for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    console.log(`[server] ${sig} received, shutting down...`);
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(0), 3_000).unref();
  });
}
