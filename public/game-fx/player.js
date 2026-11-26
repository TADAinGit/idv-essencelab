import {nativeColor} from './native-colors.js';
// Playback of original CSB p_mc sprite nodes and authored property keyframes.
// Original p_mc plus p_avatar, using the current avatar_1 and named gold/blue bindings.
let bundlePromise;
const imageCache=new Map();
export const capabilities={authored2DSpriteTimelines:true,exactNativeParity:false,original3DModel:false,originalAudio:true,gradeColorMutation:true,customRarityFlash:false,currentAvatar:true,horizontalShockLine:true};

export function sampleTrack(property,frames,index,fallback){
  if(!frames?.length||index<frames[0].frameIndex)return fallback;
  let previous=frames[0];
  for(const current of frames.slice(1)){
    if(index<current.frameIndex){
      if(!previous.tween||current.frameIndex<=previous.frameIndex)return previous.value;
      const t=(index-previous.frameIndex)/(current.frameIndex-previous.frameIndex);
      if(['Position','Scale','RotationSkew','AnchorPoint','CColor'].includes(property)&&previous.value&&current.value&&typeof previous.value==='object')return Object.fromEntries(Object.keys(previous.value).map(key=>[key,previous.value[key]+(current.value[key]-previous.value[key])*t]));
      if(property==='Alpha')return previous.value+(current.value-previous.value)*t;
      return previous.value;
    }
    previous=current;
  }
  return previous.value;
}
function loadImage(url){
  if(!url)return Promise.resolve(null);
  if(!imageCache.has(url))imageCache.set(url,new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=()=>{imageCache.delete(url);reject(Error('Không tải được texture gacha gốc.'));};image.src=url;}));
  return imageCache.get(url);
}
function getBundle(){return bundlePromise??=fetch('/game-fx/opening.json').then(response=>{if(!response.ok)throw Error('Chưa tải được timeline gacha gốc.');return response.json();}).catch(error=>{bundlePromise=null;throw error;});}
function defaults(node,property){return ({Position:node.position,Scale:node.scale,RotationSkew:node.rotationSkew,AnchorPoint:node.anchorPoint,Alpha:node.alpha,VisibleForFrame:node.visible,CColor:node.color,FileData:{texture:node.texture}})[property];}
function stateAt(node,tracks,index){
  const current={...node};
  for(const track of tracks.get(node.actionTag)||[]){const value=sampleTrack(track.property,track.frames,index,defaults(node,track.property));const key=({Position:'position',Scale:'scale',RotationSkew:'rotationSkew',AnchorPoint:'anchorPoint',Alpha:'alpha',VisibleForFrame:'visible',CColor:'color'})[track.property];if(key)current[key]=value;else if(track.property==='FileData')current.texture=value?.texture||node.texture;}
  return current;
}

export async function playOpening({count=1,essenceImage=null,grade=1,reducedMotion=false,audio=null}={}){
  if(reducedMotion){audio?.finish(false);return {skipped:true,reason:'reduced-motion',capabilities};}
  const bundle=await getBundle(),documentData=count===10?bundle.documents.ten:bundle.documents.one;
  const loaded=new Map();
  await Promise.all(Object.values(bundle.assets).map(async asset=>loaded.set(asset.url,await loadImage(asset.url))));
  const essence=await loadImage(essenceImage);
  const tracks=new Map();for(const track of documentData.animation.timelines){if(!tracks.has(track.actionTag))tracks.set(track.actionTag,[]);tracks.get(track.actionTag).push(track);}
  const clips=bundle.playback.sequence[count===10?'ten':'one'].map(name=>documentData.animation.clips.find(clip=>clip.name===name));
  if(clips.some(clip=>!clip))throw Error('Timeline gacha thiếu named clip.');
  const fps=bundle.playback.fps*(documentData.animation.speed||1);
  const delay=bundle.playback.interClipDelaySeconds||0;
  const duration=clips.reduce((total,clip)=>total+(clip.endIndex-clip.startIndex)/fps,0)+delay*(clips.length-1);
  const dialog=document.createElement('dialog');dialog.className='native-gacha-opening';dialog.setAttribute('aria-labelledby','native-gacha-title');
  dialog.style.cssText='position:fixed;inset:0;width:100vw;height:100dvh;max-width:none;max-height:none;margin:0;padding:0;border:0;border-radius:0;background:rgba(7,5,10,.97);color:#f1e3bd;overflow:hidden;';
  const bounds=document.querySelector('.workspace')?.getBoundingClientRect();if(bounds){Object.assign(dialog.style,{left:bounds.x+'px',top:bounds.y+'px',right:'auto',bottom:'auto',width:bounds.width+'px',height:bounds.height+'px',background:'rgba(7,5,10,.62)'});}
  const title=document.createElement('h2');title.id='native-gacha-title';title.textContent='Đang mở Essence';title.style.cssText='position:absolute;top:20px;left:24px;font:24px Georgia,serif;z-index:2;';
  const label=document.createElement('p');label.id='native-gacha-hint';label.textContent='Bấm vào màn hình để bỏ qua hiệu ứng và xem kết quả. Có thể dùng Enter, phím cách hoặc Escape.';dialog.setAttribute('aria-describedby',label.id);label.style.cssText='position:absolute;bottom:18px;left:24px;right:130px;font:14px/1.5 Segoe UI,sans-serif;color:#c8c1b4;z-index:2;';

  const canvas=document.createElement('canvas');canvas.width=1722;canvas.height=750;canvas.setAttribute('aria-hidden','true');canvas.style.cssText='position:absolute;inset:0;width:100%;height:100%;object-fit:contain;';
  dialog.append(canvas,title,label);document.body.append(dialog);
  const ctx=canvas.getContext('2d');
  if(!ctx){dialog.remove();throw Error('Browser không hỗ trợ Canvas2D.');}
  const tint=document.createElement('canvas'),tintContext=tint.getContext('2d');
  function drawImage(image,width,height,color){
    if(!image||!width||!height)return;
    let draw=image;
    if(tintContext&&color&&(color.r<254||color.g<254||color.b<254)){
      tint.width=image.width;tint.height=image.height;
      tintContext.clearRect(0,0,tint.width,tint.height);tintContext.globalCompositeOperation='source-over';tintContext.drawImage(image,0,0);tintContext.globalCompositeOperation='multiply';tintContext.fillStyle=`rgb(${color.r},${color.g},${color.b})`;tintContext.fillRect(0,0,tint.width,tint.height);tintContext.globalCompositeOperation='destination-in';tintContext.drawImage(image,0,0);tintContext.globalCompositeOperation='source-over';draw=tint;
    }
    ctx.save();ctx.translate(0,height);ctx.scale(1,-1);ctx.drawImage(draw,0,0,width,height);ctx.restore();
  }
  function renderNode(original,index,parentAlpha=1,path=''){
    path+='/'+original.name;
    if(['/p_avatar/avatar','/p_avatar/doubt'].some(p=>path.endsWith(p)))return;
    const node=stateAt(original,tracks,index);if(node.name==='avatar_1'){node.visible=true;node.position={...node.position,y:node.position.y+40};}if(path.endsWith('/p_avatar/doubt_1'))node.visible=true;if(node.visible===false)return;node.color=nativeColor(path,grade)||node.color;
    const alpha=parentAlpha*Math.max(0,Math.min(1,(node.alpha??255)/255));if(alpha<=0)return;
    const p=node.position||{x:0,y:0},s=node.scale||{x:1,y:1},r=node.rotationSkew||{x:0,y:0},a=node.anchorPoint||{x:0,y:0},size=node.size||{width:0,height:0};
    ctx.save();ctx.globalAlpha=alpha;ctx.translate(p.x,p.y);
    const rx=r.x*Math.PI/180,ry=r.y*Math.PI/180;
    ctx.transform(Math.cos(ry),Math.sin(ry),-Math.sin(rx),Math.cos(rx),0,0);ctx.scale(s.x*(node.flipX?-1:1),s.y*(node.flipY?-1:1));ctx.translate(-a.x*size.width,-a.y*size.height);
    if(node.name==='n_treasure'&&essence){ctx.save();ctx.translate(-210,-210);drawImage(essence,420,420,node.color);ctx.restore();}
    else if(node.texture)drawImage(loaded.get(node.texture),size.width,size.height,node.color);
    for(const child of [...(original.children||[])].sort((left,right)=>(left.zOrder||0)-(right.zOrder||0)))renderNode(child,index,alpha,path);
    ctx.restore();
  }
  if(audio)await audio.ready;
  return new Promise(resolve=>{
    let request=0,finished=false;
    const start=performance.now();
    function finish(skipped){if(finished)return;finished=true;cancelAnimationFrame(request);audio?.finish(skipped);dialog.close();dialog.remove();document.body.classList.remove('gacha-playing');resolve({skipped,capabilities,gradeApplied:true,source:documentData.source});}
    dialog.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();finish(true);});dialog.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();event.stopPropagation();finish(true);}});dialog.addEventListener('cancel',event=>{event.preventDefault();finish(true);});
    document.body.classList.add('gacha-playing');dialog.dataset.tone=Number(grade)>=4?'gold':'blue';dialog.showModal();dialog.focus();
    audio?.playOpening();
    function frame(now){
      if(finished)return;
      let elapsed=(now-start)/1000,clip=clips.at(-1),index=clip.endIndex;
      for(let i=0;i<clips.length;i++){const candidate=clips[i],seconds=(candidate.endIndex-candidate.startIndex)/fps;if(elapsed<=seconds){clip=candidate;index=clip.startIndex+elapsed*fps;break;}elapsed-=seconds;if(i<clips.length-1){if(elapsed<delay){clip=candidate;index=clip.endIndex;break;}elapsed-=delay;}}
      ctx.setTransform(1,0,0,1,0,0);ctx.clearRect(0,0,canvas.width,canvas.height);ctx.translate(194,canvas.height);ctx.scale(1,-1);renderNode(documentData.root,index);canvas.dataset.phase=clip===clips[0]&&index>=22&&index<=40?'shock':'opening';
      if((now-start)/1000>=duration){finish(false);return;}request=requestAnimationFrame(frame);
    }
    request=requestAnimationFrame(frame);
  });
}
