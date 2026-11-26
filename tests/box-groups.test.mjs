import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {groupBoxes,boxFamily,boxSeason,libraryBoxes,coaEdition,rankTier,crossoverEdition,seasonEdition,sameLibraryBox} from '../public/box-groups.js';

test('display groups retain all IDs and separate crossovers/COA from seasonal ranges',async()=>{
 const {boxes}=JSON.parse(await readFile(new URL('../public/data/v2/index.json',import.meta.url),'utf8'));
 const groups=groupBoxes(boxes),flat=groups.flatMap(g=>g.boxes.map(b=>b.id));
 assert.equal(flat.length,524);assert.equal(new Set(flat).size,524);
 const latest=groups.find(g=>g.key==='season-41');assert.equal(latest.label,'Mùa 41–45');assert.equal(latest.boxes.length,15);
 for(const g of groups.filter(g=>g.family==='season'))for(const b of g.boxes)assert.ok(boxSeason(b)>=g.start&&boxSeason(b)<=g.start+4);
 for(const id of ['21','42','96','463','468'])assert.equal(boxFamily(boxes.find(b=>b.id===id)),'coa');
 for(const id of ['74','367','182','1005','1006','438'])assert.equal(boxFamily(boxes.find(b=>b.id===id)),'crossover');
 assert.equal(boxFamily(boxes.find(b=>b.id==='134001')),'season');
 for(const g of groups.filter(g=>g.family==='rank'))for(const b of g.boxes)assert.ok(boxSeason(b)>=g.start&&boxSeason(b)<=g.start+4);
 assert.ok(groups.find(g=>g.family==='crossover').boxes.some(b=>b.id==='366'));
 assert.ok(groups.find(g=>g.family==='crossover').boxes.some(b=>b.id==='93'));
});

test('season and crossover representatives remove reruns while preserving distinct numbered parts',async()=>{
 const {boxes}=JSON.parse(await readFile(new URL('../public/data/v2/index.json',import.meta.url),'utf8'));
 const shown=libraryBoxes(boxes),cross=shown.filter(b=>boxFamily(b)==='crossover'),seasons=shown.filter(b=>boxFamily(b)==='season');
 assert.equal(cross.length,15);assert.equal(new Set(cross.map(crossoverEdition)).size,15);
 assert.equal(new Set(seasons.map(seasonEdition)).size,seasons.length);
 for(const id of ['1000','1001','1002','1003','1004'])assert.ok(!shown.some(b=>b.id===id));
 for(const id of ['1','2','11','13','1005','1006','305','307','306','366','367'])assert.ok(shown.some(b=>b.id===id));
 const get=id=>boxes.find(b=>b.id===id);
 for(const [a,b] of [['1','1001'],['2','1000'],['11','1002'],['13','1004'],['134','1005'],['74','366']])assert.ok(sameLibraryBox(get(a),get(b)));
 assert.equal(sameLibraryBox(get('1005'),get('1006')),false);
 assert.equal(sameLibraryBox(get('366'),get('367')),false);
 assert.equal(boxes.length,524);
});

test('library shows one COA per edition newest first and only Rank VIII without deleting source aliases',async()=>{
 const {boxes}=JSON.parse(await readFile(new URL('../public/data/v2/index.json',import.meta.url),'utf8'));
 const shown=libraryBoxes(boxes),groups=groupBoxes(shown),coa=groups.find(g=>g.family==='coa').boxes;
 assert.deepEqual(coa.map(coaEdition),[9,8,7,6,5,4,3,2,1]);
 assert.equal(new Set(coa.map(coaEdition)).size,9);
 assert.ok(coa.some(b=>b.id==='463'));
 const rank=shown.filter(b=>b.category==='rank');assert.ok(rank.length>20);
 assert.ok(rank.every(b=>rankTier(b)===8));assert.equal(new Set(rank.map(boxSeason)).size,rank.length);
 assert.equal(boxes.length,524);assert.ok(boxes.some(b=>b.id==='429'));
});
