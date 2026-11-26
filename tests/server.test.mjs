import test from 'node:test';
import assert from 'node:assert/strict';
import {createServer} from '../server.mjs';
test('local server serves app but does not expose source config or filesystem',async()=>{const server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));try{const base=`http://127.0.0.1:${server.address().port}`;for(const p of ['/config.local.json','/source-data/pkgmapping.json','/%2e%2e%2fconfig.local.json'])assert.equal((await fetch(base+p)).status,404);const res=await fetch(base+'/engine.js');assert.equal(res.status,200);assert.match(res.headers.get('content-type'),/javascript/);assert.equal((await fetch(base+'/engine.js',{method:'POST'})).status,405);}finally{server.closeAllConnections();await new Promise(r=>server.close(r));}});
