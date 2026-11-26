import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {sampleTrack,playOpening,capabilities} from '../public/game-fx/player.js';
const root=new URL('../public/',import.meta.url);
const hash=data=>createHash('sha256').update(data).digest('hex');
test('all original UI and timeline sprite exports match their recorded hashes',async()=>{
 const skin=JSON.parse(await readFile(new URL('game-ui/skin.json',root)));
 for(const asset of Object.values(skin.assets)){
  assert.ok(asset.csbNode);assert.ok(asset.csbSha256);assert.ok(asset.source);
  assert.equal(hash(await readFile(new URL('.'+asset.url,root))),asset.imageSha256);
 }
 for(const font of skin.fonts)assert.equal(hash(await readFile(new URL('.'+font.url,root))),font.sha256);
 const bundle=JSON.parse(await readFile(new URL('game-fx/opening.json',root)));
 for(const asset of Object.values(bundle.assets))assert.equal(hash(await readFile(new URL('.'+asset.url,root))),asset.sha256);
 assert.equal(bundle.documents.one.animation.speed,.5);assert.equal(bundle.documents.ten.animation.speed,.5);
 for(const kind of ['one','ten'])for(const name of bundle.playback.sequence[kind])assert.ok(bundle.documents[kind].animation.clips.some(c=>c.name===name));
 assert.equal(capabilities.exactNativeParity,false);assert.equal(capabilities.originalAudio,true);
});
test('authored track sampler preserves discrete frames and interpolated coordinates',()=>{
 const frames=[{frameIndex:10,tween:true,value:{x:0,y:20}},{frameIndex:20,tween:true,value:{x:100,y:40}}];
 assert.deepEqual(sampleTrack('Position',frames,5,{x:1,y:2}),{x:1,y:2});
 assert.deepEqual(sampleTrack('Position',frames,15,{}),{x:50,y:30});
 assert.equal(sampleTrack('Alpha',[{frameIndex:0,tween:false,value:10},{frameIndex:10,value:200}],5,255),10);
 assert.equal(sampleTrack('Alpha',[{frameIndex:0,tween:true,value:0},{frameIndex:10,value:200}],5,255),100);
});
test('reduced motion skips without touching browser or loading the timeline',async()=>{
 const result=await playOpening({reducedMotion:true});assert.equal(result.skipped,true);assert.equal(result.reason,'reduced-motion');
});

import {nativeColor} from '../public/game-fx/native-colors.js';
test('native result-color bindings use published source node palettes, with grade4 or5 gold',()=>{
 assert.deepEqual(nativeColor('/opening/p_avatar/light/s2_1',3),{r:58,g:225,b:255});
 for(const g of [4,5])assert.deepEqual(nativeColor('/opening/p_avatar/light/s2_1',g),{r:255,g:251,b:153});
 assert.deepEqual(nativeColor('/opening/p_mc/p_glow/light_2',4),{r:228,g:111,b:18});
 assert.equal(nativeColor('/opening/p_avatar/avatar_1/face_1',4),null);
});
