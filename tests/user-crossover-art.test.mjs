import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {posterFit} from '../public/rate-settings.js';
const root=new URL('../',import.meta.url),json=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));
test('supplied crossover posters retain exact bytes, rerun mapping and source pools',async()=>{
 const receipt=await json('research/crossover-audit/user-art/manifest.json'),source=await json('public/data/catalog.json');
 const expected={'frieren':['438'],'p5-1':['74','93','366'],'p5-2':['85','367'],'xxxholic':['327'],'danganronpa-1':['116','161','306'],'danganronpa-2':['158','307'],'danganronpa-3':['305'],'angels-of-death':['293'],'bungo-2':['280'],'death-note':['182'],'neverland-1':['170','427'],'neverland-2':['203','428'],'case-closed-1':['134','1005'],'case-closed-2':['1006'],'conan-doyle-estate':['413','451']};
 for(const [label,ids] of Object.entries(expected))for(const id of ids){
  const r=receipt.records[id],{box}=await json(`public/data/v2/boxes/${id}.json`),old=source.boxes.find(b=>b.id===id);
  assert.equal(r.label,label);assert.equal(box.banner,r.url);assert.equal(box.bannerSource.origin,'user-provided');
  assert.deepEqual(box.bannerViewport,[0,0,1,1]);assert.deepEqual(box.pools,old.pools);assert.deepEqual(box.configuration,old.configuration);
  assert.equal(posterFit(box),'contain');
  for(const path of ['public'+r.url,r.file])assert.equal(createHash('sha256').update(await readFile(new URL(path,root))).digest('hex'),r.sha256);
 }
 assert.equal(receipt.unassigned.length,1);assert.equal(receipt.unassigned[0].label,'bungo-1');assert.deepEqual(receipt.unassigned[0].boxIds,[]);
});
