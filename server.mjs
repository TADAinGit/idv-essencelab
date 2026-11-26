import http from 'node:http';
import {createReadStream} from 'node:fs';
import {stat} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root = path.dirname(fileURLToPath(import.meta.url));
const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.webp':'image/webp','.svg':'image/svg+xml','.ico':'image/x-icon','.ttf':'font/ttf','.ogg':'audio/ogg','.wav':'audio/wav'};
export function createServer() {
  return http.createServer(async (req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');
    res.setHeader('X-EssenceLab','0.1.0');
    res.setHeader('Referrer-Policy','no-referrer');
    res.setHeader('Content-Security-Policy',"default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'");
    if(!['GET','HEAD'].includes(req.method)){res.writeHead(405);return res.end();}
    try {
      let url = decodeURIComponent(new URL(req.url,'http://localhost').pathname);
      if(url.includes('\0')||url.includes('\\'))throw Error('Invalid path');
      const raw = /^\/assets\/raw\/[a-f0-9]{32}\.[a-z0-9]+$/i.test(url);
      const base = raw ? root : path.join(root,'public');
      const pageRoute=['/','/collection','/collection/','/collections','/collections/','/history','/history/'].includes(url);
      if(url==='/assets'||url==='/assets/')throw Error('Asset browser is temporarily hidden');
      const file = path.resolve(base,'.'+(pageRoute?'/index.html':url));
      if(!file.startsWith(base+path.sep))throw Error('Outside public root');
      const info = await stat(file);
      if(!info.isFile())throw Error('Not a file');
      res.setHeader('Content-Type',raw?'application/octet-stream':types[path.extname(file)]||'application/octet-stream');
      res.setHeader('Content-Length',info.size);
      res.setHeader('Cache-Control',url.startsWith('/media/')?'public, max-age=31536000, immutable':'no-cache');
      if(raw)res.setHeader('Content-Disposition',`attachment; filename="${path.basename(file)}"`);
      res.writeHead(200);
      if(req.method==='HEAD')return res.end();
      createReadStream(file).on('error',()=>res.destroy()).pipe(res);
    }catch{res.writeHead(404,{'Content-Type':'text/plain; charset=utf-8'});res.end('Không tìm thấy tài nguyên.');}
  });
}
if(process.argv[1] && path.resolve(process.argv[1])===fileURLToPath(import.meta.url)) {
  const port=Number(process.env.PORT||4173);
  createServer().listen(port,'127.0.0.1',()=>console.log(`EssenceLab local: http://127.0.0.1:${port}`));
}
