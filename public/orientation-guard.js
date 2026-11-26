// A modal gate must share the top layer with result/configuration dialogs.
export function installOrientationGuard(){
 const media=matchMedia('(max-width:1100px) and (orientation:portrait)'),source=document.querySelector('.portrait-gate');
 const gate=document.createElement('dialog');gate.className='orientation-dialog';gate.setAttribute('aria-label','Vui lòng xoay ngang thiết bị');
 gate.append(...source.cloneNode(true).childNodes);document.body.append(gate);
 function sync(raise=false){
  const blocked=media.matches&&document.body.dataset.page==='library';
  if(blocked){if(raise&&gate.open)gate.close();if(!gate.open)gate.showModal();}
  else if(gate.open)gate.close();
 }
 gate.addEventListener('cancel',event=>{if(media.matches&&document.body.dataset.page==='library')event.preventDefault();});
 const observer=new MutationObserver(records=>{
  const raise=records.some(record=>record.type==='attributes'&&record.target!==gate&&record.attributeName==='open'&&record.target.open);
  sync(raise);
 });
 observer.observe(document.body,{subtree:true,attributes:true,attributeFilter:['open','data-page']});
 media.addEventListener('change',()=>sync());window.addEventListener('pageshow',()=>sync(true));sync();
 return ()=>{observer.disconnect();gate.remove();};
}
