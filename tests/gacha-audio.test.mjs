import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {createGachaAudio} from '../public/game-fx/audio.js';
import {gachaSounds} from '../public/game-audio/manifest.js';
import {playOpening} from '../public/game-fx/player.js';

const flush=()=>new Promise(resolve=>setImmediate(resolve));
function fixture(fetchAudio=async url=>url){
 const started=[],stopped=[],fetched=[],gains=[];
 const ctx={state:'running',destination:{},resume(){return Promise.resolve();},decodeAudioData:async bytes=>({name:bytes}),createGain:()=>{const g={gain:{},connect(){},disconnect(){}};gains.push(g);return g;},createBufferSource(){const s={connect(){},disconnect(){},start(){started.push(s.buffer.name);},stop(){stopped.push(s.buffer.name);}};return s;}};
 return {started,stopped,fetched,gains,player:createGachaAudio({createContext:()=>ctx,visibility:null,fetchAudio:async url=>{fetched.push(url);return fetchAudio(url);}})};
}
test('audio is gesture-lazy, intro starts with the timeline, and decoded clips are reused',async()=>{
 const f=fixture();assert.equal(f.fetched.length,0);
 const one=f.player.begin(1);await one.ready;await flush();
 assert.deepEqual(f.started,[gachaSounds.click.url]);
 one.playOpening();assert.deepEqual(f.started,[gachaSounds.click.url,gachaSounds.one.url]);one.finish(false);
 const next=f.player.begin(1);await next.ready;await flush();assert.equal(f.fetched.length,2);
 next.finish(true);
});
test('muted or zero-volume draws create no context or audio requests',async()=>{
 let calls=0;const player=createGachaAudio({createContext(){calls++;throw Error('should stay lazy');}});
 for(const settings of [{muted:true,volume:40},{muted:false,volume:0}]){
  player.setSettings(settings);const session=player.begin(1);await session.ready;session.playOpening();session.finish(false);
 }
 assert.equal(calls,0);
});
test('master gain follows volume and mute immediately for an existing audio context',async()=>{
 const f=fixture();f.player.setSettings({muted:false,volume:35});const session=f.player.begin(1);await session.ready;
 assert.equal(f.gains[0].gain.value,.35);
 f.player.setSettings({muted:true,volume:35});assert.equal(f.gains[0].gain.value,0);
 f.player.setSettings({muted:false,volume:70});assert.equal(f.gains[0].gain.value,.7);session.finish(true);
});
test('skip before decoding prevents late sounds; skip/next draw stop existing sources',async()=>{
 let release;const gate=new Promise(resolve=>release=resolve),f=fixture(async url=>{await gate;return url;});
 const first=f.player.begin(10);first.finish(true);release();await first.ready;await flush();first.playOpening();assert.equal(f.started.length,0);
 const second=f.player.begin(10);await second.ready;await flush();second.playOpening();second.finish(true);
 assert.deepEqual(f.stopped.sort(),[gachaSounds.click.url,gachaSounds.ten.url].sort());
});
test('unavailable audio remains optional and never rejects the opening',async()=>{
 const f=fixture(async()=>{throw Error('decode/network unavailable');});const session=f.player.begin(1);
 await session.ready;await flush();assert.doesNotThrow(()=>session.playOpening());session.finish(true);assert.equal(f.started.length,0);
 const silent=createGachaAudio({createContext(){throw Error('unsupported');}}).begin(1);await silent.ready;silent.playOpening();silent.finish(true);
});
test('reduced motion retains only the click tail without starting the opening soundtrack',async()=>{
 const calls=[];const result=await playOpening({reducedMotion:true,audio:{playOpening(){calls.push('intro');},finish(skipped){calls.push(skipped);}}});
 assert.equal(result.reason,'reduced-motion');assert.deepEqual(calls,[false]);
});
test('published gacha sounds retain verified Wwise identities and Ogg hashes without private paths',async()=>{
 const report=JSON.parse(await readFile(new URL('../research/gacha-audio/export.json',import.meta.url),'utf8'));
 for(const [key,asset] of Object.entries(gachaSounds)){
  const bytes=await readFile(new URL('../public'+asset.url,import.meta.url));assert.equal(bytes.subarray(0,4).toString(),'OggS');
  assert.equal(createHash('sha256').update(bytes).digest('hex'),asset.sha256);assert.equal(report.assets[key].sha256,asset.sha256);
  assert.ok(asset.duration>0&&asset.duration<6);
 }
 assert.equal(report.assets.one.event,'P_dwrg_ui2_ui_box_one');assert.equal(report.assets.ten.event,'P_dwrg_ui2_ui_box_ten');
 assert.doesNotMatch(JSON.stringify(gachaSounds),/source_archive|source_offset|[A-Z]:[\\/]/);
});

test('returning from another app replaces even a running-but-silent context on the next gesture',async()=>{
 const visibility=new EventTarget();visibility.hidden=false;const contexts=[],started=[];
 const player=createGachaAudio({visibility,fetchAudio:async url=>url,createContext(){
  const index=contexts.length;const ctx={state:'suspended',destination:{},resume(){this.state='running';return Promise.resolve();},close(){this.state='closed';return Promise.resolve();},decodeAudioData:async name=>({name}),createGain:()=>({gain:{},connect(){},disconnect(){}}),createBufferSource:()=>({connect(){},disconnect(){},start(){started.push(index);},stop(){}})};contexts.push(ctx);return ctx;
 }});
 const first=player.begin(10);assert.equal(contexts[0].state,'running');await first.ready;first.playOpening();first.finish(false);
 visibility.hidden=true;visibility.dispatchEvent(new Event('visibilitychange'));visibility.hidden=false;visibility.dispatchEvent(new Event('visibilitychange'));
 assert.equal(contexts.length,1);const second=player.begin(10);assert.equal(contexts.length,2);assert.equal(contexts[0].state,'closed');assert.equal(contexts[1].state,'running');await second.ready;second.playOpening();assert.ok(started.includes(1));second.finish(false);
 contexts[1].state='closed';const third=player.begin(1);assert.equal(contexts.length,3);await third.ready;third.playOpening();assert.ok(started.includes(2));third.finish(true);
});
