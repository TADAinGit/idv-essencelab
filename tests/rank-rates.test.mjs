import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {rankProfile,rankPreset,RANK_RATE_ROWS} from '../public/rank-rates.js';
import {createState,drawBatch,profileKey,validateState} from '../public/engine.js';
const data=JSON.parse(await readFile(new URL('../public/data/v2/boxes/436.json',import.meta.url)));
const box=data.box,p=rankProfile(box);
test('Wiki Rank preset retains frame-card probability separately from B and totals 100 for all tiers',()=>{
 assert.deepEqual(p.weights,{'1':59.75,'2':26,'3':10.5,'4':3,'5':.75});
 assert.equal(p.pity5,250);assert.equal(p.pity4,0);
 for(const t of Object.keys(RANK_RATE_ROWS))assert.ok(Math.abs(Object.values(rankPreset(box,t).weights).reduce((a,b)=>a+b)-100)<1e-9);
 assert.equal(rankPreset(box,1).weights['5'],0);
 assert.equal(rankPreset({...box,pools:{...box.pools,3:[{key:'5:1'}]}}),null);
});
test('Rank preset draws keep independent counters, replay, import and 250th S guarantee',()=>{
 const s=createState('rank-rates');const ten=drawBatch(s,box,p,10);
 let sequential=s;for(let i=0;i<10;i++)sequential=drawBatch(sequential,box,p).state;
 assert.deepEqual(ten.state,sequential);
 assert.deepEqual(validateState(ten.state,{boxes:[box],rewards:data.rewards}),ten.state);
 const due=createState('rank-pity');due.counters[profileKey(box,p)]={'3':0,'4':249,'5':249};
 const result=drawBatch(due,box,p).results[0];assert.equal(result.grade,'5');assert.equal(result.forced,true);
 const tier1=rankPreset(box,1),low=createState('tier1');low.counters[profileKey(box,tier1)]={'4':0,'5':249};
 assert.equal(drawBatch(low,box,tier1).results[0].grade,'5');
 const changed=structuredClone(ten.state);changed.history[0].profile.weights['5']=1;
 assert.throws(()=>validateState(changed,{boxes:[box],rewards:data.rewards}));
});
