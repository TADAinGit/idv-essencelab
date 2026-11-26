const key='identityv.essencelab.audio.v1';
export function normalizeAudioSettings(value){
 const volume=Number(value?.volume);
 return {muted:value?.muted===true,volume:Number.isFinite(volume)&&value?.volume!=null?Math.max(0,Math.min(100,volume)):100};
}
export function loadAudioSettings(storage){try{return normalizeAudioSettings(JSON.parse(storage.getItem(key)));}catch{return normalizeAudioSettings();}}
export function saveAudioSettings(storage,value){const settings=normalizeAudioSettings(value);try{storage.setItem(key,JSON.stringify(settings));}catch{}return settings;}
