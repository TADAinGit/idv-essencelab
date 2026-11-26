const esc=value=>String(value??'').normalize('NFC').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function rewardAppearance(item,skin){
 const widget=skin.widgets[String(item.type)],quality=Number(item.quality)||1;
 if(!widget)return {quality,frame:null,color:skin.palette[String(quality)]||'#e5dcce'};
 return {...widget,quality,frame:skin.perItem?.[item.key]?.frame??widget.frames[String(quality)]??null,color:skin.palette[String(quality)]||'#e5dcce',nameColor:Number(item.type)===1&&quality===5?'#ffcf71':widget.nameColor};
}
export function rewardVisual(item,skin,{owned=false}={}){
 const a=rewardAppearance(item,skin),width=a.width||140,height=a.height||140;
 const size=width*(a.displayScale||1)/160*100;
 const label=item.name?.startsWith('TID_')?item.typeName:item.name;
 return `<span class="native-reward q${a.quality} type-${item.type}" data-quality="${a.quality}" style="--native-width:${size}%;--native-ratio:${width}/${height};--icon-width:${a.iconWidth||100}%;--icon-height:${a.iconHeight||100}%;--native-color:${a.color};--native-name-color:${a.nameColor||'#ffffff'}">${a.frame?`<img class="native-frame" src="${esc(a.frame)}" alt="" loading="lazy">`:''}${item.image?`<img class="native-icon" src="${esc(item.image)}" alt="" loading="lazy">`:'<span class="native-missing">Chưa có ảnh</span>'}${owned?'<span class="native-owned" role="img" aria-label="Owned">Owned</span>':''}${a.showName?`<span class="native-name" style="top:${a.nameY}%">${esc(label)}</span>`:''}</span>`;
}
