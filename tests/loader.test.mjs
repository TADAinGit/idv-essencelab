import test from 'node:test';
import assert from 'node:assert/strict';

test('loader has no eager requests, shares in-flight requests and retries failures',async()=>{
  const previous=globalThis.fetch,calls=[];
  let fail=true;
  globalThis.fetch=async url=>{calls.push(url);return {ok:!url.includes('retry')||!fail,status:503,json:async()=>({url})};};
  try{
    const {getJSON,loadBox,loadReward}=await import('../public/loader.js?test-demand');
    assert.equal(calls.length,0);
    await Promise.all([loadBox('513'),loadBox('513')]);
    assert.deepEqual(calls,['/data/v2/boxes/513.json']);
    await loadReward('1:3457');assert.equal(calls.at(-1),'/data/v2/rewards/1-3457.json');
    assert.throws(()=>loadBox('../config'));assert.throws(()=>loadReward('bad'));
    await assert.rejects(getJSON('/retry'));fail=false;await getJSON('/retry');
    assert.equal(calls.filter(u=>u==='/retry').length,2);
    assert.equal(calls.some(u=>u==='/data/catalog.json'||u==='/data/asset-index.json'),false);
  }finally{globalThis.fetch=previous;}
});

test('collection validation fetches only boxes referenced by its history',async()=>{
  const previous=globalThis.fetch,calls=[];
  globalThis.fetch=async url=>{calls.push(url);return {ok:true,json:async()=>url.includes('reward-index')?{rewards:{'1:1':{}}}:{box:{id:'513',pools:{}}}};};
  try{
    const {loadValidationCatalog}=await import('../public/loader.js?test-validation');
    assert.deepEqual(await loadValidationCatalog({total:0,history:[]}),{rewards:{},boxes:[]});
    assert.equal(calls.length,0);
    await loadValidationCatalog({total:2,history:[{boxId:'513'},{boxId:'513'}]});
    assert.deepEqual(calls.sort(),['/data/v2/boxes/513.json','/data/v2/reward-index.json']);
    assert.equal(calls.some(url=>url.includes('pool-index')),false);
  }finally{globalThis.fetch=previous;}
});
