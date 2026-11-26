// Explicitly requested Wiki preset. Marginal probabilities, not server RNG.
export const RANK_RATE_SOURCE='https://id5.fandom.com/wiki/Essence_Rates';
export const RANK_RATE_ROWS={
 1:[80,8.5,9,2.5,0],2:[77.5,10,10,2.5,0],3:[77.05,10,10,2.5,.45],
 4:[61,10,26,2.5,.5],5:[60.8,10,26,2.6,.6],6:[60.02,10.5,26,2.83,.65],
 7:[59.75,10.5,26,3,.75],8:[59.75,10.5,26,3,.75]
};
export const rankGradeLabels={'1':'C','2':'B','3':'Thẻ đổi khung chân dung','4':'A','5':'S'};
export function rankPreset(box,tier=8){
 // Modern Rank pools: grade1=C, grade2=B, grade3=portrait-frame card.
 // Older pools have another layout and must not silently receive these weights.
 if(box?.category!=='rank'||!RANK_RATE_ROWS[tier]||!box.pools?.['3']?.every(e=>e.key.startsWith('97:'))||!box.pools['3'].length||['1','2','4','5'].some(g=>!box.pools[g]?.length))return null;
 const [c,frame,b,a,s]=RANK_RATE_ROWS[tier];
 return {weights:{'1':c,'2':b,'3':frame,'4':a,'5':s},pity4:0,pity5:250};
}
export function rankProfile(box){const p=rankPreset(box);return p?{kind:'wiki-rank-v1',tier:8,...p}:null;}
export function validateRankProfile(box,p){
 const expected=rankProfile(box);
 if(!expected||JSON.stringify(expected)!==JSON.stringify(p))throw Error('Cấu hình Rank mặc định không khớp.');
 return p;
}
