import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,access,rm} from 'node:fs/promises';
import path from 'node:path';
import os from 'node:os';
import {buildPages} from '../tools/build-pages.mjs';
async function fixture(){const root=await mkdtemp(path.join(os.tmpdir(),'essencelab-pages-'));const add=async(p,text)=>{await mkdir(path.dirname(path.join(root,'public',p)),{recursive:true});await writeFile(path.join(root,'public',p),text);};
 for(const p of ['data/v2/index.json','data/v2/reward-index.json','data/v2/boxes/1.json','data/v2/rewards/1-1.json','game-ui/skin.json','game-rewards/skin.json','game-rank/scene.json','game-fx/opening.json'])await add(p,'{}');
 await add('game-ui/skin.json',JSON.stringify({assets:{},parser:{path:'D:/Apps/private/tool.py'},sources:{private:'research'}}));
 await add('index.html','<img alt="" src="/media/second.png"><script type="module" src="/app.js"></script>');await add('app.js',"import './engine.js';const image='/media/needed.png';const hidden='/data/v2/assets/index.json';");await add('engine.js','export const version=1;');await add('media/needed.png','image');await add('media/second.png','image2');await add('media/unneeded.png','unused');await add('data/asset-index.json','private old index');await add('config.local.json','private config');return {root,add};}
test('Pages bundle closes runtime references, excludes private/legacy/unreferenced files and preserves explicit SPA routes',async()=>{
 const {root}=await fixture();try{const result=await buildPages(root);const files=new Set(result.records.map(r=>r.path));
 for(const p of ['index.html','app.js','engine.js','media/needed.png','media/second.png','404.html','collection.html','history.html','_headers','_redirects'])assert.ok(files.has(p));
 for(const p of ['media/unneeded.png','data/asset-index.json','data/v2/assets/index.json','config.local.json'])assert.ok(!files.has(p));
 assert.equal(await readFile(path.join(result.output,'collection.html'),'utf8'),await readFile(path.join(result.output,'index.html'),'utf8'));
 assert.equal(await readFile(path.join(result.output,'history.html'),'utf8'),await readFile(path.join(result.output,'index.html'),'utf8'));
 assert.match(await readFile(path.join(result.output,'_headers'),'utf8'),/Content-Security-Policy/);
 assert.match(await readFile(path.join(result.output,'_redirects'),'utf8'),/\/collection\/ \/collection 301/);
 const ui=JSON.parse(await readFile(path.join(result.output,'game-ui/skin.json'),'utf8'));assert.ok(!Object.hasOwn(ui,'parser'));assert.ok(!Object.hasOwn(ui,'sources'));
 assert.ok(!/\/\* \/index.html/.test(await readFile(path.join(result.output,'_redirects'),'utf8')));
 assert.ok(result.manifestSha256.match(/^[a-f0-9]{64}$/));
 await writeFile(path.join(result.output,'obsolete.txt'),'stale');await buildPages(root);await assert.rejects(access(path.join(result.output,'obsolete.txt')));
 }finally{await rm(root,{recursive:true,force:true});}
});
test('Pages build rejects missing runtime resources and private machine paths',async()=>{
 const {root,add}=await fixture();try{await add('app.js',"const image='/media/missing.png';");await assert.rejects(buildPages(root),/Missing or unsafe/);await add('app.js',"const secret='C:/Users/private/token';");await assert.rejects(buildPages(root),/Private path/);}finally{await rm(root,{recursive:true,force:true});}
});
