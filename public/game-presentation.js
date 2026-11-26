import {boxFamily,seasonEdition} from './box-groups.js';

// Source UIDeduceInfoShow.get_norlmal_show_good_lst: pools 5 then4, quality>=A.
export function rankShowcase(box,rewards){
 return ['5','4'].flatMap(grade=>(box.pools?.[grade]||[]).map(e=>rewards[e.key]).filter(item=>item&&Number(item.quality)>=4)).slice(0,3);
}
export function resultTheme(results,rewards){
 return results.some(r=>Number(rewards[r.key]?.quality)>=4)?'gold':'blue';
}
// Render source prose as text. NeoX locale formatting codes are display markup,
// never HTML or research metadata. Raw tables remain in private research files.
export function gameText(value){
 const text=String(value||'').normalize('NFC');
 if(/^TID_[A-Z0-9_()]+$/.test(text))return '';
 return text.replace(/#r/g,'\n').replace(/#[cC][0-9a-fA-F]{6}/g,'').replace(/#n/g,'').replace(/#\d+/g,'').trim();
}

// User presentation choice for the five early Season 1 Essences, including aliases.
export const usesSeasonSkinShowcase=box=>boxFamily(box)==='season'&&/^1:[1-5]$/.test(seasonEdition(box));
export function seasonSkinShowcase(box,rewards){
 const keys=[...new Set(Object.values(box.pools||{}).flat().map(entry=>entry.key))];
 return keys.map(key=>rewards[key]).filter(item=>Number(item?.type)===1)
  .sort((a,b)=>(Number(b.quality)||0)-(Number(a.quality)||0)).slice(0,3);
}
