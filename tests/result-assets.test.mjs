import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url);
test('result-screen exported pixels match source receipts and keep private paths out of public metadata',async()=>{
 const report=JSON.parse(await readFile(new URL('research/game-results/export.json',root),'utf8'));
 const published=JSON.parse(await readFile(new URL('public/game-results/assets.json',root),'utf8'));
 for(const [key,a] of Object.entries(report.assets)){
  assert.equal(createHash('sha256').update(await readFile(new URL('public'+a.url,root))).digest('hex'),a.imageSha256);
  assert.equal(published.assets[key].imageSha256,a.imageSha256);
  assert.equal(published.assets[key].provenance,undefined);
 }
 assert.equal(report.assets['quality-45'].csb,'common_get_item_quality.csb');
 assert.equal(report.assets['tool-label'].node,'/treasure/p_operate/btn_content/img_bg_info');
 assert.equal(report.assets.again.node,'/treasure_open/p_btn/btn_open');
});

test('Memory Sphere uses explicitly selected English labels, without losing its original icon',async()=>{
 const recovered=JSON.parse(await readFile(new URL('research/image-audit/recovered.json',root),'utf8'));
 assert.equal(Object.keys(recovered).length,14);
 for(const [id,a] of Object.entries(recovered)){
  const {box}=JSON.parse(await readFile(new URL(`public/data/v2/boxes/${id}.json`,root),'utf8'));
  assert.match(a.resolved,/\/res_en\//);
  assert.equal(box.bannerKind,'label');assert.equal(box.banner,a.url);assert.ok(box.image);
  assert.equal(box.bannerSource.provenance,undefined);
  assert.equal(createHash('sha256').update(await readFile(new URL('public'+a.url,root))).digest('hex'),a.previewSha256);
 }
});
