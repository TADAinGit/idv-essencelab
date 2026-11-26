import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {editableRates,matchesDefaultRates,posterFit} from '../public/rate-settings.js';
import {sourceProfile} from '../public/source-rates.js';
import {rankProfile} from '../public/rank-rates.js';
const json=async p=>JSON.parse(await readFile(new URL('../'+p,import.meta.url),'utf8'));

test('confirming an unchanged rate form preserves progressive seasonal and Rank default profiles',async()=>{
 for(const id of ['442','429']){
  const {box}=await json(`public/data/v2/boxes/${id}.json`),profile=sourceProfile(box)||rankProfile(box),draft=editableRates(box,profile);
  assert.ok(profile);
  const form={...draft,weights:Object.fromEntries(Object.entries(draft.weights).map(([g,n])=>[g,Number(n.toFixed(8))]))};
  assert.ok(matchesDefaultRates(form,draft));
  form.weights['1']-=1;form.weights['4']+=1;
  assert.equal(matchesDefaultRates(form,draft),false);
  assert.ok(matchesDefaultRates(editableRates(box,profile),draft));
  assert.equal(matchesDefaultRates(form,null),false);
 }
});

test('large landscape artwork fills the frame; portrait, small image and announcement strip retain proportions',()=>{
 const reference=(width,height,extra={})=>({bannerKind:'reference-poster',bannerSource:{width,height},...extra});
 assert.equal(posterFit(reference(5732,4589,{bannerViewport:[0,.11,1,1]})),'cover');
 assert.equal(posterFit(reference(1920,1080)),'cover');
 assert.equal(posterFit(reference(800,450)),'contain');
 assert.equal(posterFit(reference(1600,2500)),'contain');
 assert.equal(posterFit({...reference(5000,800),bannerKind:'reference-strip'}),'contain');
});
