import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {posterFit} from '../public/rate-settings.js';
const json=async p=>JSON.parse(await readFile(new URL('../'+p,import.meta.url),'utf8'));
test('COA I and II use verified external icons and exact supplied posters without changing pools',async()=>{
 const {records}=await json('research/coa-art/manifest.json'),source=await json('public/data/catalog.json'),index=await json('public/data/v2/index.json');
 for(const [id,art] of Object.entries(records)){
  const {box}=await json(`public/data/v2/boxes/${id}.json`),old=source.boxes.find(b=>b.id===id),summary=index.boxes.find(b=>b.id===id);
  assert.equal(box.image,art.icon.url);assert.equal(summary.image,art.icon.url);assert.equal(box.iconSource.nativeAliasProven,false);
  assert.equal(box.banner,art.banner.url);assert.equal(posterFit(box),'contain');assert.deepEqual(box.configuration,old.configuration);assert.deepEqual(box.pools,old.pools);
  for(const r of Object.values(art))for(const p of [r.file,'public'+r.url])assert.equal(createHash('sha256').update(await readFile(new URL('../'+p,import.meta.url))).digest('hex'),r.sha256);
 }
});
