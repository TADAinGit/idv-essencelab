const normalize=value=>String(value??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/đ/g,'d');

export function collectionItems(collection,rewards,{query='',grade='all',sort='collected'}={}){
 const keys=Object.keys(collection).filter(key=>{
  const item=rewards[key];
  return item&&(grade==='all'||Number(item.quality)===Number(grade))&&normalize(item.name+' '+item.typeName).includes(normalize(query));
 });
 const idOrder=(a,b)=>Number(rewards[a].id)-Number(rewards[b].id)||Number(rewards[a].type)-Number(rewards[b].type)||a.localeCompare(b);
 if(sort==='grade-desc'||sort==='grade-asc')keys.sort((a,b)=>(Number(rewards[a].quality||0)-Number(rewards[b].quality||0))*(sort==='grade-desc'?-1:1)||idOrder(a,b));
 if(sort==='id-asc'||sort==='id-desc')keys.sort((a,b)=>idOrder(a,b)*(sort==='id-desc'?-1:1));
 return keys;
}
