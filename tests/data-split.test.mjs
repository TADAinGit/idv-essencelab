import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
const read=async p=>JSON.parse(await readFile(new URL('../public/data/'+p,import.meta.url),'utf8'));

test('bootstrap contains summaries only and is substantially smaller than the source',async()=>{
  const index=await read('v2/index.json');
  assert.equal(index.boxes.length,524);
  assert.equal(new Set(index.boxes.map(b=>b.id)).size,524);
  for(const box of index.boxes){assert.equal(box.pools,undefined);assert.equal(box.configuration,undefined);assert.equal(box.banner,undefined);}
  assert.equal(index.rewards,undefined);
  const report=await read('v2/size-report.json');assert.ok(report.bootstrapBytes<report.inputCatalogBytes/10);
});
test('all selected box cards and full reward records preserve source membership',async()=>{
  const source=await read('catalog.json'),index=await read('v2/reward-index.json'),pools=await read('v2/pool-index.json');
  assert.equal(Object.keys(index.rewards).length,3117);
  assert.equal(pools.boxes.length,524);
  for(const original of source.boxes){
    const detail=await read(`v2/boxes/${original.id}.json`);
    assert.deepEqual(detail.box.pools,original.pools);
    assert.deepEqual(detail.box.configuration,original.configuration);
    for(const entries of Object.values(detail.box.pools))for(const entry of entries){assert.ok(detail.rewards[entry.key]);assert.equal(detail.rewards[entry.key].configuration,undefined);}
    assert.deepEqual(pools.boxes.find(b=>b.id===original.id).pools,original.pools);
  }
  for(const [key,reward] of Object.entries(source.rewards)){
    const detail=await read(`v2/rewards/${key.replace(':','-')}.json`);
    assert.deepEqual(detail.configuration,reward.configuration);assert.equal(index.rewards[key].configuration,undefined);
  }
});
test('asset pages have bounded sizes and retain all URI identities',async()=>{
  const index=await read('v2/assets/index.json'),seen=new Set();
  for(const meta of index.pages){const page=await read('v2/assets/page-'+meta.page+'.json');assert.ok(page.entries.length<=1000);assert.equal(page.entries.length,meta.count);for(const entry of page.entries){assert.ok(!seen.has(entry.uri));seen.add(entry.uri);}}
  assert.equal(seen.size,index.total);
});
