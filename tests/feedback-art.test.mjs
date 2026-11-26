import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
test('S12E1 icon and user S26E1 poster preserve exact bytes and source box membership',async()=>{
 const read=async path=>JSON.parse(await readFile(new URL('../'+path,import.meta.url),'utf8'));
 const {records}=await read('tools/web-art-overrides.json'),source=await read('public/data/catalog.json'),index=await read('public/data/v2/index.json');
 for(const [id,record] of Object.entries(records)){
  const {box}=await read('public/data/v2/boxes/'+id+'.json'),original=source.boxes.find(b=>b.id===id);
  assert.deepEqual(box.pools,original.pools);assert.deepEqual(box.configuration,original.configuration);
  for(const [kind,art] of Object.entries(record)){
   const bytes=await readFile(new URL('../public'+art.url,import.meta.url));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),art.sha256);
   assert.equal(box[kind==='icon'?'image':'banner'],art.url);
   if(kind==='icon')assert.equal(index.boxes.find(b=>b.id===id).image,art.url);
  }
 }
});
