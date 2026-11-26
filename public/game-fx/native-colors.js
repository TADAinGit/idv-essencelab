// Named-node bindings from TBoxUtils.apply_box_result_color (bounded IR).
const stars=['star_1','star_2','star_3','star_4','star_5','star_1_0','star_2_0','star_3_0','star_4_0','star_5_0'];
const glow=Object.fromEntries(stars.map(n=>[n,['FFF82D','3AE1FF']]));
Object.assign(glow,{light_1:['FF9F2E','C2B1FF'],light_2:['E46F12','014FFF'],light_3:['FFE13C','18ABFF'],light_4:['FCB929','00C0FF'],light_5:['FFA200','9000FF']});
const shock=Object.fromEntries(['s1_1','s1_2','s1_3','s2_1','s2_2','s2_3','s2_4'].map(n=>[n,['FFFB99','3AE1FF']]));
shock.glow_2=['FFC46B','3AE1FF'];
export function nativeColor(path,grade){
 const name=path.split('/').at(-1);let pair;
 if(path.includes('/p_glow/'))pair=glow[name];
 else if(path.includes('/p_avatar/light/'))pair=shock[name];
 if(!pair)return null;
 const h=pair[Number(grade)>=4?0:1];return {r:parseInt(h.slice(0,2),16),g:parseInt(h.slice(2,4),16),b:parseInt(h.slice(4,6),16)};
}
