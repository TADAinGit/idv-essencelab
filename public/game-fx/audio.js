import {gachaSounds} from '../game-audio/manifest.js';

// Construct/resume from the draw gesture, before any asynchronous state loading.
// Audio bytes are fetched only after that gesture and decoded once per context.
export function createGachaAudio({createContext=()=>new (globalThis.AudioContext||globalThis.webkitAudioContext)(),fetchAudio=url=>fetch(url,{signal:AbortSignal.timeout(4000)}).then(r=>{if(!r.ok)throw Error('Audio unavailable');return r.arrayBuffer();}),visibility=globalThis.document}={}){
 let context,previous,master,resetOnNextGesture=false;
 let settings={muted:false,volume:100};
 let cache=new Map();
 visibility?.addEventListener('visibilitychange',()=>{if(visibility.hidden){resetOnNextGesture=true;previous?.cancel();}});
 function load(key){
  const buffers=cache,decoder=context;
  if(!buffers.has(key))buffers.set(key,Promise.resolve().then(()=>fetchAudio(gachaSounds[key].url)).then(bytes=>decoder.decodeAudioData(bytes)).catch(error=>{buffers.delete(key);throw error;}));
  return buffers.get(key);
 }
 return {setSettings(value){settings={muted:value.muted===true,volume:Math.max(0,Math.min(100,Number(value.volume)||0))};if(master)master.gain.value=settings.muted?0:settings.volume/100;},begin(count){
  previous?.cancel();
  if(settings.muted||settings.volume===0)return {ready:Promise.resolve(),playOpening(){},finish(){}};
  let resumed;
  try{if(resetOnNextGesture||context?.state==='closed'){const old=context;context=undefined;master=undefined;cache=new Map();resetOnNextGesture=false;try{Promise.resolve(old?.close?.()).catch(()=>{});}catch{}}context??=createContext();if(!master){master=context.createGain();master.connect(context.destination);}master.gain.value=settings.volume/100;resumed=Promise.resolve(context.resume());}
  catch{return {ready:Promise.resolve(),playOpening(){},finish(){}};}
  let live=true,openingBuffer;
  const sources=new Set();
  const detach=()=>visibility?.removeEventListener('visibilitychange',hidden);
  function cancel(){live=false;for(const source of sources){try{source.stop();}catch{}}sources.clear();detach();}
  function hidden(){if(visibility.hidden)cancel();}
  function play(buffer,volume){
   if(!live||!buffer||context.state!=='running')return;
   try{
    const source=context.createBufferSource(),gain=context.createGain();
    source.buffer=buffer;gain.gain.value=volume;source.connect(gain);gain.connect(master);
    sources.add(source);source.onended=()=>{sources.delete(source);source.disconnect();gain.disconnect();};source.start();
   }catch{/* Sound must never prevent a valid draw or hide its results. */}
  }
  visibility?.addEventListener('visibilitychange',hidden);
  previous={cancel};
  // A blocked context/failed decode is silent; no delayed autoplay after cancel.
  Promise.all([resumed,load('click')]).then(([,buffer])=>play(buffer,.55)).catch(()=>{});
  const ready=Promise.all([resumed,load(count===10?'ten':'one')]).then(([,buffer])=>{openingBuffer=buffer;}).catch(()=>{});
  return {ready,playOpening(){play(openingBuffer,.7);},finish(skipped){
   if(skipped){cancel();return;}
   // Let the native burst's short tail finish under the results tableau.
   live=false;detach();
  }};
 }};
}
const audio=createGachaAudio();
export const beginGachaAudio=count=>audio.begin(count);
export const setGachaAudioSettings=settings=>audio.setSettings(settings);
