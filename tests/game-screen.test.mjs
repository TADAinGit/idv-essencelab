import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
const read=p=>readFile(new URL(p,root));
const json=async p=>JSON.parse(await read(p));
const sha=b=>createHash('sha256').update(b).digest('hex');
test('screen atlas and current Alice parts retain source hashes and exact URI bindings',async()=>{
 for(const a of await json('research/game-screen/assets.json')){
  assert.ok(!a.error,a.uri);
  assert.equal(sha(await read('public'+a.url)),a.sha256);
  if(a.image)assert.equal(sha(await read('public'+a.image)),a.imageSha256);
 }
 const alice=await json('research/game-screen/alice.json');
 assert.equal(alice.avatar.name,'avatar_1');assert.equal(alice.assets.length,8);
 assert.equal(sha(await read('public/game-scene/alice-idle.svg')),alice.outputSha256);
 for(const a of alice.assets){assert.ok(a.uri.includes('/treasure_ani_new/avatar/'));assert.equal(sha(await read('public'+a.image)),a.imageSha256);}
 const pose=await json('research/game-screen/posed-frame.json');
 assert.deepEqual(pose.canvas,{width:1722,height:750});
 assert.ok(pose.layers.treasure_list_new_centre.some(s=>s.name==='zhong_hua'));
 for(const layer of ['after','centre']){
  const png=await read('public/game-scene/treasure_list_new_'+layer+'-posed.png');
  assert.equal(png.readUInt32BE(16),1722);assert.equal(png.readUInt32BE(20),750);
 }
});
test('opening exports the actual Alice and horizontal shock subtree, not only the chest effect',async()=>{
 const bundle=await json('public/game-fx/opening.json');
 for(const kind of ['one','ten']){
  const d=bundle.documents[kind],avatar=d.root.children.find(n=>n.name==='p_avatar');assert.ok(avatar);
  const alice=avatar.children.find(n=>n.name==='avatar_1');assert.ok(alice);
  const light=avatar.children.find(n=>n.name==='light');assert.ok(light);
  for(const name of ['glow_2','s1_1','s1_2','s1_3','s2_1','s2_2','s2_3','s2_4']){
   const node=light.children.find(n=>n.name===name);assert.ok(node?.texture,name);
   assert.ok(d.animation.timelines.some(t=>t.actionTag===node.actionTag&&t.property==='Alpha'&&t.frames.some(f=>f.value>0)),name);
  }
 }
});
