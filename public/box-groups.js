// Source records remain intact; only the library chooses representatives.
export const boxSeason=box=>Number(box.displaySeason||box.season)||null;
export function seasonEdition(box){
 const named=box.name?.match(/^(?:S|Season\s+)(\d+)\b.*?Essence\s*(\d+)\b/);
 if(named)return `${Number(named[1])}:${Number(named[2])}`;
 const pair=box.configuration?.show_img_num;
 return box.displayEssence?`${boxSeason(box)}:${box.displayEssence}`:pair?.length===2?pair.join(':'):box.id;
}
export const rankTier=box=>Number(box.configuration?.show_img_num?.[1]||box.nameTid?.match(/COLLECTION_(\d)/)?.[1])||null;
export const coaEdition=box=>Number(box.nameTid?.match(/SHENGDIAN_TREASURE_(\d+)/)?.[1])||0;
export const crossoverEdition=box=>(box.nameTid||box.id).replace(/_OVERSEA$/,'');
export function sameLibraryBox(a,b){
 if(!a||!b)return false;
 const family=boxFamily(a);if(family!==boxFamily(b))return false;
 if(family==='crossover')return crossoverEdition(a)===crossoverEdition(b);
 if(family==='coa')return coaEdition(a)===coaEdition(b);
 if(family==='rank')return boxSeason(a)===boxSeason(b);
 if(family==='season')return seasonEdition(a)===seasonEdition(b);
 return a.id===b.id;
}
export function libraryBoxes(boxes){
 const coa=new Map(),cross=new Map(),season=new Map();
 for(const b of boxes){
  const family=boxFamily(b);if(!['coa','crossover','season'].includes(family))continue;
  const map=family==='coa'?coa:family==='crossover'?cross:season,key=family==='coa'?coaEdition(b):family==='crossover'?crossoverEdition(b):seasonEdition(b),old=map.get(key);
  if(!old||(family==='season'?Number(b.id)<Number(old.id):Number(b.id)>Number(old.id)))map.set(key,b);
 }
 // Hide the ambiguous historical Persona 5/Memory Sphere row from the library.
 // Keep its source ID accessible for existing links, collection and history.
 return boxes.filter(b=>b.id!=='72').filter(b=>boxFamily(b)==='coa'?coa.get(coaEdition(b))===b:boxFamily(b)==='crossover'?cross.get(crossoverEdition(b))===b:boxFamily(b)==='season'?season.get(seasonEdition(b))===b:b.category==='rank'?rankTier(b)===8:true);
}
export function boxTitle(box){
 if(boxFamily(box)==='coa')return `Kho báu Vực Thẳm ${['','I','II','III','IV','V','VI','VII','VIII','IX'][coaEdition(box)]||coaEdition(box)}`;
 if(/KENAN_1/.test(box.nameTid))return 'Case Closed Crossover Essence 1';
 if(/KENAN_3/.test(box.nameTid))return 'Case Closed Crossover Essence 2';
 if(boxFamily(box)==='season'&&box.displayEssence)return `Season ${boxSeason(box)} Essence ${box.displayEssence}`;
 if(!box.name?.startsWith('TID_'))return box.name;
 if(/DEATHNOTE/.test(box.nameTid))return 'Death Note Crossover Essence';
 if(/KENAN/.test(box.nameTid))return 'Case Closed';
 if(/FURNITURE/.test(box.nameTid))return 'Essence nội thất';
 return `Essence${boxSeason(box)?' mùa '+boxSeason(box):''}`;
}
export function boxFamily(box){
  const text=`${box.name||''} ${box.nameTid||''}`;
  if(/SHENGDIAN_TREASURE|Abyss Treasure/i.test(text))return 'coa';
  if(/Crossover|GACHINAME|KENAN|WENHAO|XXXHOLIC/i.test(text))return 'crossover';
  return box.category;
}
export function groupBoxes(boxes){
  const groups=new Map();
  for(const box of boxes){
    const family=boxFamily(box),season=boxSeason(box),start=season?Math.floor((season-1)/5)*5+1:0;
    const key=['coa','crossover','classic','other'].includes(family)||!start?family:`${family}-${start}`;
    const label=family==='coa'?'Call of the Abyss · COA':family==='crossover'?'Crossover':family==='classic'?'Memory Sphere':family==='other'?'Đặc biệt':!start?'Rank Treasure':`${family==='rank'?'Rank · ':''}Mùa ${start}–${start+4}`;
    if(!groups.has(key))groups.set(key,{key,label,family,start,boxes:[]});
    groups.get(key).boxes.push(box);
  }
  const order={season:0,crossover:1,coa:2,classic:3,rank:4,other:5};
  for(const g of groups.values())g.boxes.sort((a,b)=>g.family==='coa'?coaEdition(b)-coaEdition(a):g.family==='rank'?boxSeason(b)-boxSeason(a):0);
  return [...groups.values()].sort((a,b)=>(order[a.family]??5)-(order[b.family]??5)||b.start-a.start);
}
