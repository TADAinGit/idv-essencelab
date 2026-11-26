import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeAudioSettings,loadAudioSettings,saveAudioSettings} from '../public/audio-settings.js';
test('audio preferences persist independently, clamp volume and tolerate unavailable storage',()=>{
 const data=new Map([['identityv.essencelab.sandbox.v1','collection-unchanged']]);
 const storage={getItem:k=>data.get(k),setItem:(k,v)=>data.set(k,v)};
 assert.deepEqual(loadAudioSettings(storage),{muted:false,volume:100});
 saveAudioSettings(storage,{muted:true,volume:35});assert.deepEqual(loadAudioSettings(storage),{muted:true,volume:35});
 assert.equal(data.get('identityv.essencelab.sandbox.v1'),'collection-unchanged');
 assert.deepEqual(normalizeAudioSettings({volume:150}),{muted:false,volume:100});
 assert.deepEqual(loadAudioSettings(null),{muted:false,volume:100});
 assert.deepEqual(saveAudioSettings(null,{volume:0}),{muted:false,volume:0});
});
