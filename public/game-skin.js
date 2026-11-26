import {getJSON} from './loader.js';
let ready;
export function applyGameSkin(){
  return ready??=(async()=>{
    const skin=await getJSON('/game-ui/skin.json');
    for(const [name,asset] of Object.entries(skin.assets)){
      if(!/^\/game-ui\/[a-z0-9-]+\.(png|webp)$/.test(asset.url))throw Error('Asset UI không hợp lệ.');
      document.documentElement.style.setProperty('--native-'+name,`url("${asset.url}")`);
    }
    document.body.classList.add('game-skin');
    return skin;
  })();
}
