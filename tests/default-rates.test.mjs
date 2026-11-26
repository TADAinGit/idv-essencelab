import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {defaultRateProfile,isProgressive} from '../public/default-rates.js';
import {boxFamily} from '../public/box-groups.js';
import {sourceProfile,sourceProbabilities} from '../public/source-rates.js';
import {rankProfile} from '../public/rank-rates.js';
import {editableRates,matchesDefaultRates} from '../public/rate-settings.js';
import {createState,drawBatch,profileKey,validateProfile,validateState,uniformProfile} from '../public/engine.js';
const catalog=JSON.parse(await readFile(new URL('../public/data/catalog.json',import.meta.url),'utf8'));
test('all 524 source boxes have valid usable defaults and no probability enters empty pools',()=>{
 for(const box of catalog.boxes){
  const p=defaultRateProfile(box);assert.ok(p,box.id);validateProfile(box,p);
  if(isProgressive(p))for(const n of [0,9,59,199,249]){
   const {rates}=sourceProbabilities(p,{'3':n,'4':n,'5':n});
   assert.ok(Math.abs(Object.values(rates).reduce((a,b)=>a+b,0)-1)<1e-12);
   for(const [g,r] of Object.entries(rates))if(!box.pools[g]?.length)assert.equal(r,0,`${box.id}/${g}`);
  }
  drawBatch(createState('all-defaults'),box,p,10);
  assert.ok(matchesDefaultRates(editableRates(box,p),editableRates(box,p)));
  const old=rankProfile(box)||sourceProfile(box);
  if(old&&!['coa','crossover'].includes(boxFamily(box)))assert.deepEqual(p,old);
 }
});
test('COA S200 and crossover S250 override family aliases, force the due draw and reject tampering',()=>{
 for(const box of catalog.boxes.filter(b=>['coa','crossover'].includes(boxFamily(b)))){
  const p=defaultRateProfile(box),limit=boxFamily(box)==='coa'?200:250;
  assert.equal(p.pity['5'],limit);assert.equal(p.base['5'],0.00004975);assert.equal(p.add['5'],0.00004975);
  assert.equal(sourceProbabilities(p,{'5':limit-1}).rates['5'],1);
  assert.ok(sourceProbabilities(p,{'5':limit-2}).rates['5']<1);
  const state=createState();state.counters[profileKey(box,p)]={'3':9,'4':59,'5':limit-1};
  const {results,state:after}=drawBatch(state,box,p);
  assert.equal(results[0].grade,'5');assert.equal(results[0].forced,true);assert.equal(after.counters[profileKey(box,p)]['5'],0);
  const changed=structuredClone(p);changed.pity['5']=1;assert.throws(()=>validateProfile(box,changed));
 }
});
test('new defaults roundtrip beside old sandbox/source histories and isolate counters',()=>{
 const box=catalog.boxes.find(b=>b.id==='438'),p=defaultRateProfile(box),sandbox=uniformProfile(box);
 const before=drawBatch(createState('preserve'),box,sandbox,10).state;
 const after=drawBatch(before,box,p,10).state;
 assert.deepEqual(validateState(JSON.parse(JSON.stringify(after)),catalog),after);
 assert.deepEqual(after.history.slice(10),before.history);assert.deepEqual(after.counters[profileKey(box,sandbox)],before.counters[profileKey(box,sandbox)]);
 assert.notEqual(profileKey(box,p),profileKey(box,sandbox));assert.equal(after.history[0].mode,'default');
 const altered=structuredClone(after);altered.history[0].mode='sandbox';assert.throws(()=>validateState(altered,catalog));
 assert.deepEqual(validateState(before,catalog),before);
});
