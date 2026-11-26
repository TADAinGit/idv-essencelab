// Explicit, demand-driven requests with bounded in-memory caching. No prefetch.
const cache=new Map();
const MAX_CACHE=36;
export async function getJSON(url){
  if(cache.has(url)){const value=cache.get(url);cache.delete(url);cache.set(url,value);return value;}
  const request=fetch(url).then(response=>{if(!response.ok)throw Error(`Không tải được dữ liệu (${response.status}).`);return response.json();});
  cache.set(url,request);
  while(cache.size>MAX_CACHE)cache.delete(cache.keys().next().value);
  try{return await request;}catch(error){cache.delete(url);throw error;}
}
export function loadBox(id){if(!/^\d+$/.test(String(id)))throw Error('ID Essence không hợp lệ.');return getJSON(`/data/v2/boxes/${id}.json`);}
export function loadReward(key){if(!/^\d+:\d+$/.test(key))throw Error('ID phần thưởng không hợp lệ.');return getJSON(`/data/v2/rewards/${key.replace(':','-')}.json`);}
export async function loadValidationCatalog(state){
  if(state?.total===0)return {rewards:{},boxes:[]};
  if(!state||!Array.isArray(state.history)||state.history.length>5000)throw Error('Collection không hợp lệ.');
  const ids=[...new Set(state.history.map(entry=>entry?.boxId))];
  if(ids.length>524||ids.some(id=>!/^\d+$/.test(String(id))))throw Error('Lịch sử Essence không hợp lệ.');
  const [r,details]=await Promise.all([getJSON('/data/v2/reward-index.json'),Promise.all(ids.map(loadBox))]);
  return {rewards:r.rewards,boxes:details.map(detail=>detail.box)};
}
