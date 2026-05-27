import http from 'http';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = process.env.PORT || 3000;
const distDir = path.join(__dirname, 'dist');

const server = http.createServer((req, res) => {
  let filePath = path.join(distDir, req.url === '/' ? 'index.html' : req.url);

  // If file doesn't exist and it's not a file request (no extension), serve index.html
  if (!fs.existsSync(filePath) && !path.extname(req.url)) {
    filePath = path.join(distDir, 'index.html');
  }

  // Prevent directory traversal
  if (!filePath.startsWith(distDir)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }

  fs.readFile(filePath, (err, content) => {
    if (err) {
      res.writeHead(404);
      res.end('Not Found');
      return;
    }

    // Set content type
    const ext = path.extname(filePath);
    const contentTypes = {
      '.html': 'text/html',
      '.js': 'application/javascript',
      '.css': 'text/css',
      '.json': 'application/json',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.svg': 'image/svg+xml',
    };

    res.writeHead(200, {
      'Content-Type': contentTypes[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=3600',
    });
    res.end(content);
  });
});

server.listen(PORT, () => {
  console.log(`[SPA Server] Running on http://localhost:${PORT}`);
  console.log(`[SPA Server] Serving from ${distDir}`);
});

