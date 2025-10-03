export class SocketHandler {
  constructor(socket, manager, SERVER_SETTINGS, onReleased) {
    this.socket = socket;
    this.manager = manager;
    this.onReleased = onReleased;
    this.settings = SERVER_SETTINGS;

    this.buf = "";
    this.q = [];
    this.running = false;
    this.closed = false;

    this.attach();
  }

  attach() {
    const { socket, settings, manager } = this;
    socket.setNoDelay(true);
    if (settings.KEEPALIVE_ENABLED) {
      socket.setKeepAlive(true, settings.KEEPALIVE_DELAY_MS);
    }
    socket.setTimeout(settings.IDLE_TIMEOUT_MS);

    console.log(
      "[server] client connected:",
      socket.remoteAddress,
      socket.remotePort,
    );

    socket.on("data", (data) => this.onData(data));
    socket.on("timeout", () => {
      console.warn("[server] idle timeout; closing");
      socket.end('{"error":"idle_timeout"}\n');
    });
    socket.on("close", async () => {
      await this.onClose();
    });
    socket.on("error", (err) => {
      console.error("[server] socket error:", err);
      // 'close' will still follow
    });

    manager.on("send", (data) => this.sendJSON(data));
  }

  onData(data) {
    if (this.closed) return;

    this.buf += data.toString("utf8");
    if (this.buf.length > this.settings.MAX_LINE_BYTES) {
      console.warn("[server] line too long; destroying socket");
      this.socket.destroy();
      return;
    }

    for (;;) {
      const i = this.buf.indexOf("\n");
      if (i < 0) break;
      const raw = this.buf.slice(0, i);
      this.buf = this.buf.slice(i + 1);

      const line = raw.trim();
      if (!line) continue;
      this.enqueue(line);
    }
  }

  enqueue(line) {
    this.q.push(line);
    queueMicrotask(() => this.runQueue());
  }

  async runQueue() {
    if (this.running || this.closed) return;
    this.running = true;
    try {
      while (this.q.length && !this.closed) {
        const line = this.q.shift();
        await this.handleLine(line);
      }
    } finally {
      this.running = false;
    }
  }

  async handleLine(line) {
    let req;
    try {
      req = JSON.parse(line);
    } catch (e) {
      return this.sendJSON({ error: "bad_json", message: e.message });
    }

    console.log(req);
    try {
      const { cmd, data } = req;
      if (cmd === "connect") {
        await this.manager.connect(data);
        const connected = await this.manager.is_connected();
        this.sendJSON( {connected:connected})
      } else if (cmd === "get_serial") {
        const serial = await this.manager.get_serial();
        this.sendJSON( {serial:serial})
      } else if (cmd === "start_comm") {
        await this.manager.start_comm(); // or drop await if fire-and-forget
      } else if (cmd === "is_connected") {
        const connected = await this.manager.is_connected();
        this.sendJSON( {connected:connected})
      } else {
        await this.manager.add_to_requests(req);
      }
    } catch (e) {
      console.error("[server] handle error:", e);
      return this.sendJSON({
        error: "command_failed",
        message: String(e?.message || e),
      });
    }
  }

  sendJSON(obj) {
    console.log("SENDING" + obj);
    return new Promise((resolve, reject) => {
      const line = JSON.stringify(obj) + "\n";
      this.socket.write(line, (err) => (err ? reject(err) : resolve()));
    });
  }

  async onClose() {
    if (this.closed) return;
    this.closed = true;
    this.q.length = 0;

    try {
      await this.manager.close();
    } catch (e) {
      console.error("[server] manager close error:", e);
    }
    if (this.manager.socket === this.socket) this.manager.socket = null;

    console.log("[server] client disconnected");
    this.onReleased?.(); // tell the server the slot is free
  }
}
