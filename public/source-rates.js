// Reconstruction of the published ordinary-season probability rules.
// This does not reproduce server RNG, first-purchase or per-item guarantee policies.
export const RATE_SOURCE='https://www.identityvgame.com/kr/news/official/20260813/35363_1246185.html';
export function sourceProfile(box){
 const c=box?.configuration;
 if(!c||box.category!=='season'||!/^TID_TREASURE_GAILV_CONTENT_SAIJI(?:_200)?$/.test(c.drop_rate_tid||''))return null;
 if(['1','2','3','4','5'].some(g=>!box.pools?.[g]?.length))return null;
 const base={},add={},pity={};
 for(const g of ['2','3','4','5']){
  if(!Number.isFinite(c['grade_rate_'+g])||c['grade_rate_'+g]<0||c['grade_rate_'+g]>1)return null;
  base[g]=c['grade_rate_'+g];
 }
 for(const g of ['3','4','5']){
  const a=c['grade_add_'+g];
  if(!Array.isArray(a)||a.length!==2||!Number.isFinite(a[0])||a[0]<0||!Number.isInteger(a[1])||a[1]<1||a[1]>10000)return null;
  add[g]=a[0];pity[g]=a[1];
 }
 return {kind:'source-season-v1',base,add,pity};
}
export function validateSourceProfile(box,p){
 const expected=sourceProfile(box);
 if(!expected||JSON.stringify(expected)!==JSON.stringify(p))throw Error('Cấu hình tỷ lệ gốc không khớp Essence.');
 return p;
}
export function sourceProbabilities(p,counter={}){
 const rates={},conditional={},forced={};let remaining=1;
 for(const g of ['5','4','3','2']){
  const misses=counter[g]||0;
  forced[g]=!!p.pity[g]&&misses+1>=p.pity[g];
  const rate=forced[g]?1:Math.min(1,p.base[g]+(p.add[g]||0)*misses);
  conditional[g]=rate;rates[g]=remaining*rate;remaining*=1-rate;
 }
 rates['1']=remaining;
 return {rates,conditional,forced};
}
