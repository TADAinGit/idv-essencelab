import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),json=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));
test('missing crossover icons use attributed reference images without rewriting snapshot config',async()=>{
 const source=await json('public/data/catalog.json'),index=await json('public/data/v2/index.json');
 const supplied=(await json('research/crossover-audit/user-art/manifest.json')).records;
 const expected=['74','85','93','367','366','116','161','306','134','158','307','182','280','293','305','327','1005','1006'];
 for(const id of expected){
  const original=source.boxes.find(b=>b.id===id),summary=index.boxes.find(b=>b.id===id),{box}=await json(`public/data/v2/boxes/${id}.json`);
  assert.equal(original.image,null);assert.equal(summary.iconStatus,'external-reference');
  assert.equal(summary.iconSource.nativeAliasProven,false);assert.equal(summary.iconSource.origin,'wiki-reference');
  assert.deepEqual(box.configuration,original.configuration);assert.deepEqual(box.pools,original.pools);
  assert.equal(box.bannerKind,'reference-poster');assert.equal(box.bannerSource.origin,supplied[id]?'user-provided':'wiki-reference');
  for(const [url,stamp] of [[box.image,box.iconSource],[box.banner,box.bannerSource]]){
   const bytes=await readFile(new URL('public'+url,root));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),stamp.sha256);
   if(stamp.origin==='wiki-reference')assert.match(stamp.context,/^https:\/\/id5\.fandom\.com\/wiki\//);
   else assert.equal(stamp.context,undefined);
  }
 }
 // Conan I aliases share a pool; Conan II has Kid and a different icon/poster.
 const a=(await json('public/data/v2/boxes/1005.json')).box,b=(await json('public/data/v2/boxes/1006.json')).box;
 assert.notEqual(a.image,b.image);assert.notEqual(a.banner,b.banner);
 assert.equal(index.boxes.find(b=>b.id==='203').iconStatus,'copied');
});
