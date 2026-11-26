import test from 'node:test';
import assert from 'node:assert/strict';
import {readRoute,routePath} from '../public/routes.js';
import {createServer} from '../server.mjs';
test('real paths preserve collection/history and keep unknown/hidden pages out of navigation',()=>{
  assert.deepEqual(readRoute(new URL('http://localhost/collection')),{view:'collection'});
  assert.deepEqual(readRoute(new URL('http://localhost/collections/')),{view:'collection'});
  assert.deepEqual(readRoute(new URL('http://localhost/history/')),{view:'history'});
  assert.deepEqual(readRoute(new URL('http://localhost/?essence=513')),{view:'library',essence:'513'});
  assert.equal(routePath('collection'),'/collection');assert.equal(routePath('history'),'/history');
  assert.equal(routePath('library','513'),'/?essence=513');assert.equal(routePath('assets'),'/');
});
test('direct collection/history refresh serves the app; assets page is hidden',async()=>{
  const server=createServer();await new Promise(r=>server.listen(0,'127.0.0.1',r));
  try{const base=`http://127.0.0.1:${server.address().port}`;for(const route of ['/','/collection','/history']){const res=await fetch(base+route);assert.equal(res.status,200);assert.match(await res.text(),/EssenceLab/);}assert.equal((await fetch(base+'/assets')).status,404);}finally{server.closeAllConnections();await new Promise(r=>server.close(r));}
});
