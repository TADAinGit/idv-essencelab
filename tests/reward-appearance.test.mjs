import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {rewardAppearance,rewardVisual} from '../public/reward-appearance.js';
const root=new URL('../',import.meta.url);
const read=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));

test('article quality selects original frames and colors independently of the pool grade',async()=>{
 const skin=await read('public/game-rewards/skin.json');
 const c=rewardAppearance({type:1,key:'1:311',quality:2,grade:1},skin);
 assert.match(c.frame,/quailty_skin_c-/);assert.equal(c.quality,2);assert.equal(c.color,'#53efcc');
 const a=rewardAppearance({type:1,quality:4},skin),s=rewardAppearance({type:1,quality:5},skin);
 assert.match(a.frame,/quailty_skin_a-/);assert.equal(a.color,'#b573ff');
 assert.match(s.frame,/quailty_skin_s-/);assert.equal(s.color,'#ffc684');
 assert.equal(a.width,160);assert.equal(a.height,240);
 const action=rewardAppearance({type:2,quality:3},skin);assert.match(action.frame,/quailty_motion_b-/);assert.equal(action.width,140);assert.equal(action.height,140);
 assert.match(rewardAppearance({type:3,quality:3},skin).frame,/quailty_pose_b-/);
 assert.equal(rewardAppearance({type:10,quality:3},skin).frame,null);
 const html=rewardVisual({type:1,key:'1:311',quality:2,name:'A < B',image:'/media/test.png'},skin);
 assert.ok(html.includes('data-quality="2"'));assert.ok(html.includes('A &lt; B'));
});

test('source frame and Vietnamese font bytes retain their audited hashes',async()=>{
 const report=await read('research/reward-widgets/skin-export.json'),skin=await read('public/game-rewards/skin.json');
 for(const [literal,a] of Object.entries(report.textures)){
  const bytes=await readFile(new URL('public'+a.url,root));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),a.imageSha256,literal);
  assert.equal(skin.textures[literal].provenance,undefined);
 }
 const font=await readFile(new URL('public/game-ui/font-vi.ttf',root));
 assert.equal(createHash('sha256').update(font).digest('hex'),report.font.sha256);
 const coverage=await read('research/reward-widgets/vietnamese-coverage.json');
 assert.equal(coverage.fontSha256,report.font.sha256);assert.deepEqual(coverage.missing,[]);assert.equal(coverage.family,'Alegreya Medium');
});
