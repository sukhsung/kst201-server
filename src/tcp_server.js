// tcp_server.js
import net from 'node:net';

const HOST = '0.0.0.0';   // listen on all interfaces
const PORT = 5555;        // pick any free port

// Create server
const server = net.createServer((socket) => {
  console.log('[server] client connected:', socket.remoteAddress, socket.remotePort);

  socket.on('data', (data) => {
    console.log('[server] received:', data.toString());
    // Echo back to client for now
    socket.write(Buffer.from('ACK: ' + data.toString()));
  });

  socket.on('end', () => {
    console.log('[server] client disconnected');
  });

  socket.on('error', (err) => {
    console.error('[server] socket error:', err);
  });
});

// Start listening
server.listen(PORT, HOST, () => {
  console.log(`[server] listening on ${HOST}:${PORT}`);
});

server.on('error', (err) => {
  console.error('[server] error:', err);
});
