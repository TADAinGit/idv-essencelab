// Anonymous browser session. Wallet and game save commit as one storage record.
export const SESSION_KEY='identityv.essencelab.guest.v1';
export const LEGACY_KEY='identityv.essencelab.sandbox.v1';
export const CAPACITY=300, REFILL_MS=6*60*60*1000, IDLE_MS=24*60*60*1000;
const valid=r=>r?.version===1&&typeof r.id==='string'&&Number.isFinite(r.lastSeen)&&Number.isFinite(r.refillAt)&&Number.isInteger(r.balance)&&r.balance>=0&&r.balance<=CAPACITY&&[r.save,r.backup].every(v=>v===null||typeof v==='string');
export class GuestSession{
 constructor(storage,{now=()=>Date.now(),id=()=>crypto.randomUUID(),lock=action=>globalThis.navigator?.locks? navigator.locks.request(SESSION_KEY,action):action()}={}){this.storage=storage;this.now=now;this.id=id;this.lock=lock;}
 async run(action=()=>{}, {touch=false}={}){
  return this.lock(async()=>{
   const now=this.now(),stored=this.storage.getItem(SESSION_KEY);let record;
   try{record=JSON.parse(stored);}catch{}
   const migrate=stored===null;
   if(!valid(record)||now-record.lastSeen>=IDLE_MS){
    record={version:1,id:this.id(),lastSeen:now,refillAt:now+REFILL_MS,balance:CAPACITY,save:migrate?this.storage.getItem(LEGACY_KEY):null,backup:migrate?this.storage.getItem(LEGACY_KEY+'.backup'):null};
   }
   if(now>=record.refillAt){record.balance=CAPACITY;record.refillAt+= (Math.floor((now-record.refillAt)/REFILL_MS)+1)*REFILL_MS;}
   if(touch)record.lastSeen=Math.max(record.lastSeen,now);
   const result=await action(record);
   const serialized=JSON.stringify(record);
   if(serialized!==stored)this.storage.setItem(SESSION_KEY,serialized);
   // Delete old copies only after a successful commit; they cannot revive expired saves.
   this.storage.removeItem(LEGACY_KEY);this.storage.removeItem(LEGACY_KEY+'.backup');
   return result;
  });
 }
 async snapshot(touch=false){return this.run(r=>structuredClone(r),{touch});}
 async save(value,backup=false,expectedId=null){return this.run(r=>{if(expectedId&&r.id!==expectedId)throw Error('Phiên đã hết hạn. Vui lòng thử lại trong phiên mới.');r[backup?'backup':'save']=value;return structuredClone(r);},{touch:true});}
 async draw(count,makeSave){
  if(count!==1&&count!==10)throw Error('Chỉ hỗ trợ mở 1 hoặc 10 lượt.');
  return this.run(async r=>{
   if(r.balance<count)throw Error(`Không đủ cầu. Cần ${count} cầu; số dư được nạp lại thành 300 mỗi 6 giờ.`);
   const batch=await makeSave(r.save);
   r.save=JSON.stringify(batch.state);r.balance-=count;
   return {batch,session:structuredClone(r)};
  },{touch:true});
 }
}
export function refillCountdown(refillAt,now=Date.now()){
 const seconds=Math.max(0,Math.ceil((refillAt-now)/1000));
 return [Math.floor(seconds/3600),Math.floor(seconds/60)%60,seconds%60].map(n=>String(n).padStart(2,'0')).join(':');
}
