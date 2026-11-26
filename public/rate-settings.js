import {sourceProbabilities} from './source-rates.js';
import {uniformProfile} from './engine.js';
import {isProgressive} from './default-rates.js';

// Form values are fixed percentages. An unchanged default stays the original
// progressive/source profile rather than silently becoming a fixed sandbox.
export function editableRates(box,profile){
 if(isProgressive(profile))return {weights:Object.fromEntries(Object.entries(sourceProbabilities(profile).rates).map(([g,r])=>[g,r*100])),pity4:profile.pity['4'],pity5:profile.pity['5']};
 return profile?{weights:{...profile.weights},pity4:profile.pity4,pity5:profile.pity5}:uniformProfile(box);
}
export function matchesDefaultRates(draft,original){
 return !!original&&['1','2','3','4','5'].every(g=>Math.abs(draft.weights[g]-original.weights[g])<1e-7)&&draft.pity4===original.pity4&&draft.pity5===original.pity5;
}
export function posterFit(box){
 if(box.bannerKind==='reference-poster'&&box.bannerFit==='contain')return 'contain';
 if(['reference-strip','label'].includes(box.bannerKind))return 'contain';
 if(box.bannerKind!=='reference-poster')return 'cover';
 const s=box.bannerSource||{},w=s.width||0,h=s.height||1;
 const [l,t,r,b]=box.bannerViewport||[0,0,1,1];
 return w>=1000&&w*(r-l)>=h*(b-t)?'cover':'contain';
}
