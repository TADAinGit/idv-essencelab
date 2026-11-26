import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {rankShowcase,usesSeasonSkinShowcase,seasonSkinShowcase,resultTheme,gameText} from '../public/game-presentation.js';
const root=new URL('../',import.meta.url);
const json=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));

test('Rank showcase follows source pools5 then4, retains source order and actual item quality',async()=>{
 const {box,rewards}=await json('public/data/v2/boxes/429.json');
 const featured=rankShowcase(box,rewards);
 assert.deepEqual(featured.map(r=>r.key),['5:647','5:648','5:649']);
 assert.deepEqual(featured.map(r=>r.quality),[5,4,4]);
 assert.match(box.description,/Tier I Rank Treasure/);
 const mock={pools:{5:[{key:'c'},{key:'s'}],4:[{key:'a'},{key:'b'},{key:'extra'}]}};
 assert.deepEqual(rankShowcase(mock,{c:{key:'c',quality:2},s:{key:'s',quality:5},a:{key:'a',quality:4},b:{key:'b',quality:4},extra:{key:'extra',quality:4}}).map(i=>i.key),['s','a','b']);
});

test('result backdrop has only gold and blue, based on actual quality rather than pool grade',()=>{
 const items={c:{quality:2},b:{quality:3},a:{quality:4},s:{quality:5}};
 assert.equal(resultTheme([{key:'c',grade:5}],items),'blue');
 assert.equal(resultTheme([{key:'b',grade:3}],items),'blue');
 assert.equal(resultTheme([{key:'a',grade:1}],items),'gold');
 assert.equal(resultTheme([{key:'c'},{key:'s'}],items),'gold');
});

test('source prose keeps story text while stripping locale display codes',()=>{
 assert.equal(gameText('#cffffffA story#rSpecial effect:#rChanges ability#n'),'A story\nSpecial effect:\nChanges ability');
 assert.equal(gameText('TID_UNRESOLVED_DESCRIPTION'),'');
 assert.equal(gameText(null),'');
 assert.equal(gameText("A story isn't reality."),"A story isn't reality.");
});

test('Rank curtain and both backdrop exports retain their recorded source/output hashes',async()=>{
 const record=await json('research/rank-screen/scene-export.json');
 for(const a of Object.values(record.assets)){
  const data=await readFile(new URL('public'+a.url,root));
  assert.equal(createHash('sha256').update(data).digest('hex'),a.sha256);
 }
 assert.equal(record.assets.curtain.node,'/Node/p_main/p_move/p_content/p_main/p_mask/p_treasure/img_bg');
 assert.match(record.assets.curtain.requested,/img_bg_poster\.png$/);
 assert.deepEqual(record.assets['rays-gold'].color,[255,248,45]);
 assert.deepEqual(record.assets['rays-blue'].color,[58,225,255]);
 assert.equal(record.slots.length,3);
});

test('Season 1 Essences 1–5 showcase their own three highest-quality skins, including historical aliases',async()=>{
 const expected={'1':['1:1908','1:1907','1:2504'],'2':['1:6007','1:6006','1:2103'],'3':['1:6206','1:207','1:6205'],'11':['1:6809','1:6808','1:6311'],'12':['1:6403','1:6402','1:2509']};
 const {boxes}=await json('public/data/v2/index.json');
 for(const id of [...Object.keys(expected),'1001','1000','1002']){
  const {box,rewards}=await json(`public/data/v2/boxes/${id}.json`);
  assert.equal(usesSeasonSkinShowcase(box),true);assert.equal(usesSeasonSkinShowcase(boxes.find(b=>b.id===id)),true);
  const items=seasonSkinShowcase(box,rewards);assert.equal(items.length,3);assert.deepEqual(items.map(i=>i.quality),[5,4,4]);
  assert.ok(items.every(i=>i.type===1&&i.image));
  if(expected[id])assert.deepEqual(items.map(i=>i.key),expected[id]);
 }
 for(const id of ['13','22','429','74','71'])assert.equal(usesSeasonSkinShowcase((await json(`public/data/v2/boxes/${id}.json`)).box),false);
 const rewards={a:{key:'a',type:1,quality:4},s:{key:'s',type:1,quality:5},accessory:{key:'accessory',type:5,quality:6},b:{key:'b',type:1,quality:3}};
 assert.deepEqual(seasonSkinShowcase({pools:{1:[{key:'s'},{key:'a'}],5:[{key:'accessory'},{key:'a'},{key:'b'}]}},rewards).map(i=>i.key),['s','a','b']);
});
