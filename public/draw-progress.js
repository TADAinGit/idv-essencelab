import {profileKey} from './engine.js';
import {isProgressive} from './default-rates.js';

export function drawProgress(state,box,profile,rewards={}){
 const key=profileKey(box,profile),counter=state.counters[key]||{};
 const entries=state.history.filter(entry=>String(entry.boxId)===String(box.id)&&profileKey(box,entry.profile)===key);
 const count=quality=>entries.filter(entry=>Number(rewards[entry.key]?.quality??entry.grade)===quality).length;
 const remaining=grade=>{
  const pity=isProgressive(profile)?profile.pity[grade]:profile['pity'+grade];
  return pity?Math.max(1,pity-(counter[grade]||0)):null;
 };
 return {opened:entries.length,s:count(5),a:count(4),remainingA:remaining('4'),remainingS:remaining('5'),partial:state.total>state.history.length};
}

const number=value=>new Intl.NumberFormat('vi-VN').format(value);
const highlight=(text,grade)=>`<span class="progress-${grade}">${text}</span>`;
export function progressCopy(progress,view='received'){
 if(view==='guarantee'){
  const a=progress.remainingA===null?'Chưa bật bảo hiểm bậc '+highlight('A','a'):`Còn ${highlight(number(progress.remainingA)+' lượt','a')} để chắc chắn nhận ${highlight('A','a')} trở lên`;
  const s=progress.remainingS===null?'Chưa bật bảo hiểm bậc '+highlight('S','s'):`Còn ${highlight(number(progress.remainingS)+' lượt','s')} để chắc chắn nhận ${highlight('S','s')}`;
  return `<span class="progress-line">${a}</span><span class="progress-line">${s}</span>`;
 }
 return `<span class="progress-line">${progress.partial?'Trong nhật ký gần đây:':'Đã mở'} ${number(progress.opened)} lượt. Đã nhận:</span><span class="progress-line">${highlight(number(progress.s)+' vật phẩm bậc S','s')} và ${highlight(number(progress.a)+' vật phẩm bậc A','a')}</span>`;
}
