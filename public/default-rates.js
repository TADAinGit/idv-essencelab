// User-requested defaults. Keep existing verified subset profiles stable;
// extend other pools using their configured conditional rates and increments.
import {boxFamily} from './box-groups.js';
import {sourceProfile} from './source-rates.js';
import {rankProfile} from './rank-rates.js';
export const isProgressive=p=>['source-season-v1','user-default-v1'].includes(p?.kind);
export function configuredDefault(box){
 const c=box?.configuration||{},active=['1','2','3','4','5'].filter(g=>box?.pools?.[g]?.length);
 if(!active.length)return null;
 const base={},add={},pity={},family=boxFamily(box);
 for(const g of ['2','3','4','5']){
  const rate=c['grade_rate_'+g];
  base[g]=active.includes(g)&&Number.isFinite(rate)?Math.min(1,Math.max(0,rate)):0;
 }
 // Assign residual probability to the lowest populated grade, never an empty pool.
 if(active[0]!=='1')base[active[0]]=1;
 for(const g of ['3','4','5']){
  const row=c['grade_add_'+g]||[];
  add[g]=active.includes(g)&&Number.isFinite(row[0])?Math.max(0,row[0]):0;
  pity[g]=active.includes(g)&&Number.isInteger(row[1])&&row[1]>0&&row[1]<=10000?row[1]:0;
 }
 if(active.includes('5')&&['coa','crossover'].includes(family)){
  base['5']=0.00004975;add['5']=0.00004975;
  pity['5']=family==='coa'?200:250;
 }
 return {kind:'user-default-v1',base,add,pity};
}
export function defaultRateProfile(box){
 // Family overrides precede category-based profiles (COA/crossover can be season records).
 if(['coa','crossover'].includes(boxFamily(box)))return configuredDefault(box);
 return rankProfile(box)||sourceProfile(box)||configuredDefault(box);
}
export function validateDefaultProfile(box,p){
 const expected=configuredDefault(box);
 if(!expected||JSON.stringify(expected)!==JSON.stringify(p))throw Error('Tỉ lệ mặc định không khớp cầu.');
 return p;
}
