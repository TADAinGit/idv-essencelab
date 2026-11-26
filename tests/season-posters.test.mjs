import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const root=new URL('../',import.meta.url),json=async p=>JSON.parse(await readFile(new URL(p,root),'utf8'));
test('seasonal artwork keeps verified hashes, exact Essence sections and immutable source pools',async()=>{
 const report=await json('research/season-posters/reference-art.json'),source=await json('public/data/catalog.json');
 assert.equal(Object.keys(report.records).length,94);assert.deepEqual(report.downloadErrors,{});
 for(const [id,r] of Object.entries(report.records)){
  const {box}=await json(`public/data/v2/boxes/${id}.json`),original=source.boxes.find(b=>b.id===id);
  assert.deepEqual(box.configuration,original.configuration);assert.deepEqual(box.pools,original.pools);
  assert.equal(box.banner,r.url);assert.equal(box.bannerSource.nativeAliasProven,false);
  assert.equal(createHash('sha256').update(await readFile(new URL('public'+r.url,root))).digest('hex'),r.sha256);
  assert.match(r.section,new RegExp('Essence\\s*'+r.wikiEssence+'\\b','i'));
  assert.equal(box.bannerKind,r.presentation==='strip'?'reference-strip':'reference-poster');
  assert.deepEqual(box.bannerViewport,r.viewport);
  const [l,t,right,bottom]=r.viewport;
  assert.ok(l>=0&&t>=0&&right<=1&&bottom<=1&&right>l&&bottom>t,`bounded artwork viewport ${id}`);
 }
 // Historic Global titles override later reissue seasons; Bloodbath's E2/E3 alias is explicit.
 assert.equal(report.records['1000'].season,1);assert.equal(report.records['75'].wikiEssence,3);
 assert.deepEqual(report.missing.map(r=>r.id),['1','1001']);
 assert.equal((await json('public/data/v2/boxes/1.json')).box.banner,null);
 for(const id of ['440','441','442'])assert.doesNotMatch(report.records[id].key,/InGamePoster/);
 for(const id of ['115','183','235','247','441']){
  assert.equal(report.records[id].origin,'wiki-reference-edited');
  assert.equal(report.records[id].edit.outputSha256,report.records[id].sha256);
  assert.deepEqual(report.records[id].viewport,[0,0,1,1]);
 }
 assert.equal(report.records['63'].origin,'user-provided');
 const supplied=await json('research/ui-polish/user-s6e2.json');
 assert.equal(report.records['63'].sha256,supplied.sha256);
 assert.deepEqual(report.records['63'].viewport,[0,0,1,1]);
 const userSeasons=(await json('research/ui-polish/user-season-art.json')).records;
 for(const [id,receipt] of Object.entries(userSeasons)){
  assert.equal(report.records[id].origin,'user-provided');
  assert.equal(report.records[id].sha256,receipt.sha256);
  assert.equal(report.records[id].season,receipt.season);
  assert.equal(report.records[id].wikiEssence,receipt.wikiEssence??receipt.essence);
  assert.deepEqual(report.records[id].viewport,[0,0,1,1]);
 }
 const app=await readFile(new URL('public/app.js',root),'utf8');assert.doesNotMatch(app,/art-credit|Ảnh tham khảo/);
});
