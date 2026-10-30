/**
 * server.js — Hardened Next.js HTTP server wrapper
 *
 * Wraps Next.js with an explicit Node.js HTTP server attaching socket and process-level
 * error handlers. This prevents ECONNRESET / EPIPE errors (common on TechZone Power VMs
 * when idle TCP connections or health checks are reset) from crashing the server process.
 */

const { createServer } = require('http');
const { parse } = require('url');
const next = require('next');

const port = parseInt(process.env.PORT || '3000', 10);
const dev = process.env.NODE_ENV === 'development';
const app = next({ dev });
const handle = app.getRequestHandler();

app.prepare().then(() => {
  const server = createServer((req, res) => {
    // Catch ECONNRESET / EPIPE on the response socket (client dropped connection)
    res.on('error', (err) => {
      if (err.code === 'ECONNRESET' || err.code === 'EPIPE') {
        return; // Client disconnected mid-response — not a server crash
      }
      console.error('[server] response socket error:', err);
    });

    const parsedUrl = parse(req.url, true);
    handle(req, res, parsedUrl);
  });

  // Catch socket-level client errors before request completes
  server.on('clientError', (err, socket) => {
    if (err.code === 'ECONNRESET' || err.code === 'EPIPE' || !socket.writable) {
      return;
    }
    socket.end('HTTP/1.1 400 Bad Request\r\n\r\n');
  });

  // Server-level error handling
  server.on('error', (err) => {
    if (err.code === 'ECONNRESET' || err.code === 'EPIPE') {
      return;
    }
    console.error('[server] server error:', err);
    process.exit(1);
  });

  // Process-level uncaught error trapping for network drops
  process.on('uncaughtException', (err) => {
    if (err.code === 'ECONNRESET' || err.code === 'EPIPE' || (err.message && err.message.includes('ECONNRESET'))) {
      console.warn('[server] Swallowed uncaught network reset:', err.code || err.message);
      return;
    }
    console.error('[server] uncaughtException:', err);
  });

  process.on('unhandledRejection', (reason) => {
    console.error('[server] unhandledRejection:', reason);
  });

  server.listen(port, '0.0.0.0', () => {
    console.log(`✓ Hardened Next.js server listening on http://0.0.0.0:${port}`);
    console.log(`  NODE_ENV: ${process.env.NODE_ENV || 'production'}`);
  });
});
