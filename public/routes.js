export function readRoute(location){
  const path=location.pathname.replace(/\/$/,'')||'/';
  if(['/collection','/collections'].includes(path))return {view:'collection'};
  if(path==='/history')return {view:'history'};
  return {view:'library',essence:new URLSearchParams(location.search).get('essence')};
}
export function routePath(view,essence){
  if(view==='collection')return '/collection';
  if(view==='history')return '/history';
  return essence&&/^\d+$/.test(String(essence))?`/?essence=${essence}`:'/';
}
