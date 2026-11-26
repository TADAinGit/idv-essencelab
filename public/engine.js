// Local deterministic simulator; source-season is a disclosed reconstruction.
import {validateSourceProfile,sourceProbabilities} from "./source-rates.js";
import {validateRankProfile} from './rank-rates.js';
import {isProgressive,validateDefaultProfile} from './default-rates.js';
export const VERSION=1;
const grades=['1','2','3','4','5'];
const plain=o=>o && typeof o==='object' && !Array.isArray(o);
const integer=n=>Number.isSafeInteger(n)&&n>=0&&n<=1_000_000_000;
export function seedHash(text){let h=2166136261;for(const c of String(text)){h=Math.imul(h^c.codePointAt(0),16777619);}return h>>>0;}
export function createState(seed='essence-lab'){return {version:VERSION,seed:String(seed),rng:seedHash(seed),collection:{},history:[],counters:{},total:0};}
export function uniformProfile(box){const active=grades.filter(g=>box.pools[g]?.length);return {weights:Object.fromEntries(grades.map(g=>[g,active.includes(g)?100/active.length:0])),pity4:0,pity5:0};}
export function validateProfile(box,p){
  if(p?.kind==='user-default-v1')return validateDefaultProfile(box,p);
  if(p?.kind==='wiki-rank-v1')return validateRankProfile(box,p);
  if(p?.kind==='source-season-v1')return validateSourceProfile(box,p);
  if(!plain(p)||!plain(p.weights))throw Error('Tỉ lệ không hợp lệ.');
  let sum=0;
  for(const g of grades){const w=p.weights[g];if(typeof w!=='number'||!Number.isFinite(w)||w<0||w>100)throw Error('Tỷ lệ phải nằm trong khoảng 0–100%.');if(w>0&&!box.pools[g]?.length)throw Error(`Bậc ${g} không có phần thưởng trong Essence này.`);sum+=w;}
  if(Math.abs(sum-100)>0.00001)throw Error('Tổng tỷ lệ phải bằng 100%.');
  for(const [field,g] of [['pity4','4'],['pity5','5']]){if(!Number.isInteger(p[field])||p[field]<0||p[field]>10000)throw Error('Bảo hiểm phải là số nguyên từ 0 đến 10.000; 0 để tắt.');if(p[field]&&!box.pools[g]?.length)throw Error(`Không thể bật bảo hiểm bậc ${g} khi không có phần thưởng tương ứng.`);}
  return p;
}
export function profileKey(box,p){if(p?.kind==='user-default-v1')return `default:${box.shareRateId}:${seedHash(JSON.stringify(p))}`;if(p?.kind==='source-season-v1'||p?.kind==='wiki-rank-v1')return `source:${box.shareRateId}:${seedHash(JSON.stringify(p))}`;return `sandbox:${box.shareRateId}:${seedHash(JSON.stringify([grades.map(g=>p.weights[g]),p.pity4,p.pity5]))}`;}
function random(state){let t=state.rng=(state.rng+0x6D2B79F5)>>>0;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return ((t^(t>>>14))>>>0)/4294967296;}
export function drawBatch(state,box,profile,count=1){
  validateProfile(box,profile);
  if(count!==1&&count!==10)throw Error('Chỉ hỗ trợ mở 1 hoặc 10 lượt.');
  if(!integer(state.total)||state.total>1_000_000_000-count)throw Error('Đã đạt giới hạn lượt mở.');
  const next=structuredClone(state),key=profileKey(box,profile);
  const seasonal=isProgressive(profile),source=seasonal||profile.kind==='wiki-rank-v1';
  const counter=next.counters[key]||(source?{'3':0,'4':0,'5':0}:{'4':0,'5':0});
  const results=[];
  for(let i=0;i<count;i++){
    let grade,forced=false;
    if(seasonal){
      const probabilities=sourceProbabilities(profile,counter);let cursor=random(next);
      for(const g of ['5','4','3','2','1']){if(cursor<probabilities.rates[g]){grade=g;break;}cursor-=probabilities.rates[g];}
      grade??='1';forced=!!probabilities.forced[grade];counter['3']++;
    }
    if(source&&!seasonal)counter['3']++;
    counter['4']++;counter['5']++;
    if(!seasonal&&profile.pity5&&counter['5']>=profile.pity5){grade='5';forced=true;}
    else if(!seasonal&&profile.pity4&&counter['4']>=profile.pity4){grade='4';forced=true;}
    else if(!seasonal){let cursor=random(next)*100;for(const g of grades){if(cursor<profile.weights[g]){grade=g;break;}cursor-=profile.weights[g];}grade??=grades.filter(g=>profile.weights[g]>0).at(-1);}
    const entries=box.pools[grade],entry=entries[Math.floor(random(next)*entries.length)];
    const owned=next.collection[entry.key]||0;
    if(!integer(owned)||owned>=1_000_000_000)throw Error('Bộ sưu tập vượt giới hạn.');
    const result={boxId:box.id,key:entry.key,grade,duplicate:owned>0,forced,sequence:++next.total,tail:entry.tail||[],profile:structuredClone(profile),mode:profile.kind==='user-default-v1'?'default':source?'source-config':'sandbox'};
    next.collection[entry.key]=owned+1;
    if(source&&Number(grade)>=3)counter['3']=0;
    if(Number(grade)>=4)counter['4']=0;
    if(grade==='5')counter['5']=0;
    next.history.unshift(result);results.push(result);
  }
  next.counters[key]=counter;next.history=next.history.slice(0,5000);
  return {state:next,results};
}
export function validateState(value,catalog){
  if(!plain(value)||value.version!==VERSION||typeof value.seed!=='string'||value.seed.length>200||!Number.isInteger(value.rng)||value.rng<0||value.rng>4294967295||!integer(value.total))throw Error('Tệp bộ sưu tập không hợp lệ.');
  if(!plain(value.collection)||!plain(value.counters)||!Array.isArray(value.history)||value.history.length>5000||Object.keys(value.counters).length>10000)throw Error('Bộ sưu tập không hợp lệ.');
  for(const [key,count] of Object.entries(value.collection)){if(!catalog.rewards[key]||!integer(count)||count===0)throw Error('Bộ sưu tập có vật phẩm hoặc số lượng không hợp lệ.');}
  if(Object.values(value.collection).reduce((a,b)=>a+b,0)!==value.total)throw Error('Số vật phẩm không khớp số lượt mở.');
  for(const [key,c] of Object.entries(value.counters)){if(!/^(sandbox|source|default):[\w-]+:\d+$/.test(key)||!plain(c)||(!key.startsWith('sandbox:')&&!integer(c['3']))||!integer(c['4'])||!integer(c['5'])||c['4']>value.total||c['5']>value.total||(c['3']!==undefined&&(!integer(c['3'])||c['3']>value.total)))throw Error('Bộ đếm không hợp lệ.');}
  const boxes=new Map(catalog.boxes.map(b=>[b.id,b]));
  for(const entry of value.history){const box=boxes.get(entry?.boxId);if(!box||!['sandbox','source-config','default'].includes(entry.mode)||!grades.includes(entry.grade)||!box.pools[entry.grade].some(e=>e.key===entry.key)||!integer(entry.sequence)||entry.sequence<1||entry.sequence>value.total||typeof entry.duplicate!=='boolean'||typeof entry.forced!=='boolean')throw Error('Lịch sử có kết quả không hợp lệ.');validateProfile(box,entry.profile);if(entry.mode!==(entry.profile.kind==='user-default-v1'?'default':['source-season-v1','wiki-rank-v1'].includes(entry.profile.kind)?'source-config':'sandbox'))throw Error('Thiết lập lượt mở không hợp lệ.');}
  if(value.history.length!==Math.min(value.total,5000)||value.history.some((e,i)=>e.sequence!==value.total-i))throw Error('Thứ tự lịch sử không hợp lệ.');
  const clean=createState(value.seed);clean.rng=value.rng;clean.total=value.total;clean.collection=Object.fromEntries(Object.entries(value.collection));clean.counters=Object.fromEntries(Object.entries(value.counters).map(([k,c])=>[k,{...(c['3']===undefined?{}:{'3':c['3']}),'4':c['4'],'5':c['5']}]));clean.history=structuredClone(value.history);
  return clean;
}
