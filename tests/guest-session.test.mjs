import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {GuestSession,SESSION_KEY,LEGACY_KEY,REFILL_MS,IDLE_MS,refillCountdown} from '../public/guest-session.js';
import {createState,drawBatch} from '../public/engine.js';
import {defaultRateProfile} from '../public/default-rates.js';
function fixture(){
 const data=new Map();let now=1000000,id=0,queue=Promise.resolve();
 const storage={getItem:k=>data.get(k)??null,setItem:(k,v)=>data.set(k,v),removeItem:k=>data.delete(k)};
 const options={now:()=>now,id:()=>String(++id),lock:fn=>{const next=queue.then(fn);queue=next.catch(()=>{});return next;}};
 return {data,storage,options,session:new GuestSession(storage,options),time:value=>now=value,advance:n=>now+=n};
}
test('anonymous wallet survives reload, refills to 1000 on six-hour boundaries without stacking',async()=>{
 const f=fixture(),first=await f.session.snapshot(true);
 await f.session.draw(10,()=>({state:{total:10}}));
 const reload=new GuestSession(f.storage,f.options);
 assert.equal((await reload.snapshot()).balance,990);
 f.advance(REFILL_MS-1);assert.equal((await reload.snapshot()).balance,990);
 f.advance(1);let next=await reload.snapshot();assert.equal(next.balance,1000);assert.equal(next.refillAt,first.refillAt+REFILL_MS);
 await reload.draw(1,()=>({state:{total:11}}));f.advance(REFILL_MS*2);next=await reload.snapshot();assert.equal(next.balance,1000);assert.equal(JSON.parse(next.save).total,11);
 assert.equal(refillCountdown(next.refillAt,next.refillAt-1001),'00:00:02');
});
test('24-hour idle expiry drops save and backup, while returning activity slides expiry',async()=>{
 const f=fixture();await f.session.save('collection');await f.session.save('backup',true);
 const first=await f.session.snapshot();f.advance(IDLE_MS-1);assert.equal((await f.session.snapshot(true)).id,first.id);
 f.advance(IDLE_MS-1);assert.equal((await f.session.snapshot()).save,'collection');
 f.advance(1);const expired=await f.session.snapshot();assert.notEqual(expired.id,first.id);assert.equal(expired.balance,1000);assert.equal(expired.save,null);assert.equal(expired.backup,null);
});
test('legacy migration retains collection exactly and cannot resurrect it after expiry',async()=>{
 const f=fixture();f.data.set(LEGACY_KEY,'original collection');f.data.set(LEGACY_KEY+'.backup','original backup');
 const migrated=await f.session.snapshot(true);assert.equal(migrated.save,'original collection');assert.equal(migrated.backup,'original backup');assert.equal(f.data.has(LEGACY_KEY),false);
 f.advance(IDLE_MS);assert.equal((await f.session.snapshot()).save,null);
});
test('existing 300-capacity sessions keep their save, backup and balance until the next 1000 refill',async()=>{
 const f=fixture(),first=await f.session.snapshot(true);
 const previous={...first,balance:280,save:'existing collection',backup:'existing backup'};
 f.data.set(SESSION_KEY,JSON.stringify(previous));
 assert.deepEqual(await f.session.snapshot(),previous);
 f.advance(REFILL_MS);
 const refilled=await f.session.snapshot();
 assert.equal(refilled.balance,1000);assert.equal(refilled.id,previous.id);
 assert.equal(refilled.save,previous.save);assert.equal(refilled.backup,previous.backup);
});
test('draw and wallet commit together; parallel tabs cannot overspend or overwrite newer draws',async()=>{
 const f=fixture(),other=new GuestSession(f.storage,f.options);
 const {box}=JSON.parse(await readFile(new URL('../public/data/v2/boxes/513.json',import.meta.url)));
 const make=saved=>drawBatch(saved?JSON.parse(saved):createState('guest-test'),box,defaultRateProfile(box),10);
 const draws=await Promise.allSettled(Array.from({length:101},(_,i)=>(i%2?f.session:other).draw(10,make)));
 assert.equal(draws.filter(d=>d.status==='fulfilled').length,100);assert.equal(draws.filter(d=>d.status==='rejected').length,1);
 const result=await f.session.snapshot();assert.equal(result.balance,0);assert.equal(JSON.parse(result.save).total,1000);
 const before=f.data.get(SESSION_KEY);await assert.rejects(f.session.draw(1,()=>{throw Error('should not be called');}),/Không đủ cầu/);assert.equal(f.data.get(SESSION_KEY),before);
 // Import and collection reset must not replenish currency.
 await f.session.save(JSON.stringify(createState()));assert.equal((await f.session.snapshot()).balance,0);
});
test('failed draw or storage write grants neither rewards nor a wallet deduction',async()=>{
 const f=fixture();await f.session.snapshot(true);const before=f.data.get(SESSION_KEY);
 await assert.rejects(f.session.draw(10,()=>{throw Error('load failed');}),/load failed/);assert.equal(f.data.get(SESSION_KEY),before);
 f.storage.setItem=()=>{throw Error('storage full');};await assert.rejects(f.session.draw(10,()=>({state:{total:10}})),/storage full/);assert.equal(f.data.get(SESSION_KEY),before);
 await assert.rejects(f.session.draw(2,()=>({state:{}})),/Chỉ hỗ trợ/);
});

test('a stale tab cannot write a previous session save after its 24-hour expiry',async()=>{
 const f=fixture(),old=await f.session.snapshot(true);await f.session.save('old',false,old.id);
 f.advance(IDLE_MS);await assert.rejects(f.session.save('stale collection',false,old.id),/Phiên đã hết hạn/);
 const fresh=await f.session.snapshot(true);assert.equal(fresh.save,null);assert.notEqual(fresh.id,old.id);
});
